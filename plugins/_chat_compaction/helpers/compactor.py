"""Core compaction logic for the compaction plugin."""
import os
from datetime import datetime

import models as models_module
from agent import Agent
from helpers import tokens
from helpers.history import History, output_text
from helpers.persist_chat import (
    export_json_chat,
    get_chat_folder_path,
    save_tmp_chat,
    remove_msg_files,
)
from helpers.state_monitor_integration import mark_dirty_all

MIN_COMPACTION_TOKENS = 1000
from plugins._model_config.helpers.model_config import (
    get_chat_model_config,
    get_utility_model_config,
    get_preset_by_name,
    build_model_config,
    build_chat_model,
    build_utility_model,
)


def _save_pre_compaction_backup(context, full_text: str) -> dict[str, str]:
    """Save the original chat as JSON and plain text before compaction.

    Returns dict with 'json' and 'txt' absolute file paths.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = os.path.join(get_chat_folder_path(context.id), "backups")
    os.makedirs(backup_dir, exist_ok=True)

    json_path = os.path.join(backup_dir, f"pre-compact-{timestamp}.json")
    txt_path = os.path.join(backup_dir, f"pre-compact-{timestamp}.txt")

    json_content = export_json_chat(context)
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_content)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    return {"json": json_path, "txt": txt_path}


def _build_model(use_chat_model: bool, preset_name: str | None, agent):
    """Build the LLM model for compaction based on user selection.

    If preset_name is given, builds from that preset's config.
    Otherwise falls back to the agent's currently configured model.
    """
    if preset_name:
        preset = get_preset_by_name(preset_name)
        if preset:
            model_key = "chat" if use_chat_model else "utility"
            cfg = preset.get(model_key, {})
            if cfg.get("provider") or cfg.get("name"):
                mc = build_model_config(cfg, models_module.ModelType.CHAT)
                return cfg, models_module.get_chat_model(
                    mc.provider, mc.name, model_config=mc, **mc.build_kwargs()
                )

    if use_chat_model:
        cfg = get_chat_model_config(agent)
        return cfg, build_chat_model(agent)
    else:
        cfg = get_utility_model_config(agent)
        return cfg, build_utility_model(agent)


async def run_compaction(
    context,
    use_chat_model: bool = True,
    preset_name: str | None = None,
) -> None:
    """
    Compact the chat history into a single summarized message.
    
    This function:
    1. Extracts the full conversation text
    2. Estimates token count and checks against model context window
    3. If needed, splits history and summarizes iteratively
    4. Calls the LLM to generate a comprehensive summary
    5. Replaces the history with a single AI message containing the summary
    6. Resets the log and creates a response log item
    7. Persists the changes
    
    The function streams progress to the frontend via the log system.
    If any error occurs, the original history is preserved.
    """
    agent = context.agent0
    
    try:
        # Step 1: Extract full conversation text
        history_output = agent.history.output()
        full_text = output_text(history_output, ai_label="assistant", human_label="user")
        
        if not full_text.strip():
            raise ValueError("No conversation content to compact")
        
        # Step 2: Estimate tokens, resolve model, and compute context budget
        token_count = tokens.approximate_tokens(full_text)

        resolved_cfg, model = _build_model(use_chat_model, preset_name, agent)
        ctx_length = int(resolved_cfg.get("ctx_length", 128000)) if resolved_cfg else 128000
        # Buffer for BOS/EOS/system tokens (llama.cpp adds 3 special tokens)
        SPECIAL_TOKEN_BUFFER = 10
        max_input_tokens = int(ctx_length * 0.7) - SPECIAL_TOKEN_BUFFER
        
        # Step 3: Create progress log item (count user-visible messages only)
        visible_types = {"user", "response"}
        visible_count = sum(1 for item in context.log.logs if item.type in visible_types)
        log_item = context.log.log(
            type="info",
            heading="Compacting chat history...",
            content=f"Analyzing {visible_count} messages (~{token_count} tokens)...",
        )
        
        # Step 4: Handle large histories by chunking if necessary
        if token_count > max_input_tokens:
            summary = await _compact_large_history(
                agent, full_text, token_count, max_input_tokens, log_item, model
            )
        else:
            summary = await _compact_single_pass(
                agent, full_text, log_item, model
            )
        
        if not summary or not summary.strip():
            raise ValueError("Compaction produced empty summary")
        
        # Step 5: Save pre-compaction backup before destroying history
        backup_paths = _save_pre_compaction_backup(context, full_text)
        
        # Step 6: Replace history with compacted version
        backup_note = (
            f"\n\n---\n"
            f"*Pre-compaction backup of the full original conversation:*\n"
            f"- `{backup_paths['txt']}`"
        )
        compacted_content = f"## Context compacted\n\n{summary}{backup_note}"

        agent.history = History(agent=agent)
        agent.history.add_message(ai=True, content=compacted_content)
        
        # Clear subordinate chain
        agent.data.pop(Agent.DATA_NAME_SUBORDINATE, None)
        context.streaming_agent = None
        
        # Step 7: Reset log and create response
        context.log.reset()
        context.log.log(
            type="response",
            heading="Context compacted",
            content=compacted_content,
            update_progress="none",
        )
        
        # Step 8: Persist and notify
        save_tmp_chat(context)
        remove_msg_files(context.id)
        
        # Step 9: Force progress bar to inactive state LAST
        # This must happen after all log operations and persist
        context.log.set_progress("Waiting for input", 0, False)
        mark_dirty_all(reason="plugins.compaction.compact_chat")
        
    except Exception as e:
        # Log error but don't modify history
        context.log.log(
            type="error",
            heading="Compaction Failed",
            content=str(e),
        )
        mark_dirty_all(reason="plugins.compaction.compact_chat_error")
        raise


async def _compact_single_pass(agent, full_text: str, log_item, model) -> str:
    """Compact history in a single LLM call using the provided model."""
    system_prompt = agent.read_prompt("compact.sys.md")
    user_prompt = agent.read_prompt("compact.msg.md", conversation=full_text)

    async def stream_cb(chunk: str, total: str):
        if chunk:
            log_item.stream(content=chunk)

    summary, _ = await model.unified_call(
        system_message=system_prompt,
        user_message=user_prompt,
        response_callback=stream_cb,
    )
    return summary


async def _compact_large_history(
    agent, full_text: str, token_count: int, max_input_tokens: int, log_item, model
) -> str:
    """Handle large histories by splitting into chunks and summarizing iteratively."""
    log_item.update(
        content=f"History is large (~{token_count} tokens). Splitting into chunks...",
    )

    lines = full_text.split('\n')
    mid = len(lines) // 2
    chunks = ['\n'.join(lines[:mid]), '\n'.join(lines[mid:])]

    summaries = []
    for i, chunk in enumerate(chunks, 1):
        log_item.update(content=f"Summarizing part {i}/{len(chunks)}...")

        system_prompt = agent.read_prompt("compact.sys.md")
        user_prompt = agent.read_prompt("compact.msg.md", conversation=chunk)

        chunk_summary, _ = await model.unified_call(
            system_message=system_prompt,
            user_message=user_prompt,
        )
        summaries.append(chunk_summary)

    combined = "\n\n---\n\n".join(summaries)
    log_item.update(content="Creating final summary from parts...")

    final_prompt = agent.read_prompt("compact.sys.md")
    final_user = agent.read_prompt(
        "compact.msg.md",
        conversation=f"This is a multi-part conversation. Here are summaries of each part:\n\n{combined}",
    )

    async def stream_cb(chunk: str, total: str):
        if chunk:
            log_item.stream(content=chunk)

    final_summary, _ = await model.unified_call(
        system_message=final_prompt,
        user_message=final_user,
        response_callback=stream_cb,
    )
    return final_summary


async def get_compaction_stats(context) -> dict:
    """
    Get statistics about the current chat for the confirmation modal.
    
    Returns:
        dict with message_count, token_count, model_name
    """
    agent = context.agent0
    
    # Count user-visible conversation turns only
    # 'user' = user sent a message, 'response' = agent final response
    # Other types (agent, tool, code_exe, etc.) are intermediate processing steps
    visible_types = {"user", "response"}
    message_count = sum(
        1 for item in context.log.logs
        if item.type in visible_types
    )
    
    # Estimate tokens
    history_output = agent.history.output()
    full_text = output_text(history_output, ai_label="assistant", human_label="user")
    token_count = tokens.approximate_tokens(full_text) if full_text else 0
    
    # Get model names for both chat and utility
    chat_cfg = get_chat_model_config(agent)
    utility_cfg = get_utility_model_config(agent)
    chat_model_name = chat_cfg.get("name", "Default") if chat_cfg else "Default"
    utility_model_name = utility_cfg.get("name", "Default") if utility_cfg else "Default"
    
    return {
        "message_count": message_count,
        "token_count": token_count,
        "model_name": chat_model_name,
        "chat_model_name": chat_model_name,
        "utility_model_name": utility_model_name,
    }
