"""Conservative native projection of already-prepared local Responses history."""

from copy import deepcopy
import hashlib
import json
from typing import Any, Callable

from helpers.llm_result import result_from_metadata


PREFIX_HASH = "history_prefix_hash"


def start_prompt(loop_data: Any) -> None:
    loop_data.params_temporary.pop("responses_prompt_replacements", None)
    loop_data.params_temporary.pop("responses_history", None)


def remember_prompt(loop_data: Any, text: str, system_message: Any, protocol: list[dict]) -> None:
    from helpers import history

    loop_data.params_temporary["responses_history"] = {
        "text": text,
        "prefix": [system_message, *history.output_langchain(protocol + loop_data.history_output)],
    }


def prepare_call(agent: Any, call_data: dict) -> dict:
    from langchain_core.prompts import ChatPromptTemplate
    from helpers import history
    from helpers.secrets import get_secrets_manager

    model, messages = call_data["model"], call_data["messages"]
    params = agent.loop_data.params_temporary
    kwargs = {"responses_prompt_replacements": call_data.get(
        "responses_prompt_replacements", params.get("responses_prompt_replacements", {}),
    )}
    prepared = params.get("responses_history", {})
    if (
        not prepared or not hasattr(model, "_convert_messages")
        or any(message.additional_kwargs or getattr(message, "tool_calls", None) for message in messages)
        or ChatPromptTemplate.from_messages(messages).format() != prepared["text"]
    ):
        return kwargs

    def render(record):
        rendered = agent._responses_prompt_input_items(
            model, history.output_langchain([{**record, "ai": False}]),
        )
        return rendered[0].get("content") if len(rendered) == 1 else None

    kwargs["responses_history_context"] = {
        "prompt": agent._responses_prompt_input_items(model, messages),
        "prefix": agent._responses_prompt_input_items(model, prepared["prefix"]),
        "groups": prepare_groups(
            agent.loop_data.history_output, render,
            get_secrets_manager(agent.context).mask_values,
        ),
    }
    return kwargs


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def prefix_hashes(items: list[dict], scope: dict) -> list[str]:
    digest = hashlib.sha256(_json_bytes(scope))
    hashes = [digest.hexdigest()]
    for item in items:
        digest.update(b"\n" + _json_bytes(item))
        hashes.append(digest.hexdigest())
    return hashes


def _json_object(text: Any) -> dict | None:
    if not isinstance(text, str):
        return None
    try:
        value = json.loads(text)
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _contains_secret(value: Any, mask: Callable[[str], str]) -> bool:
    if isinstance(value, str):
        return mask(value) != value
    if isinstance(value, dict):
        return any(_contains_secret(item, mask) for item in value.values())
    if isinstance(value, list):
        return any(_contains_secret(item, mask) for item in value)
    return False


def prepare_groups(
    records: list[dict], render: Callable[[dict], Any], mask: Callable[[str], str]
) -> list[dict]:
    groups = []
    for index, record in enumerate(records):
        if not record.get("ai"):
            continue
        result = result_from_metadata(record.get("metadata"))
        if not result or result.mode != "responses" or result.state != "local":
            continue
        prefix_hash = result.capability.get(PREFIX_HASH)
        calls = result.function_calls
        if not prefix_hash or not calls:
            continue
        output = [item.to_dict() for item in result.output_items]
        if any(item.get("type") not in {"function_call", "reasoning"} for item in output):
            continue
        if any(
            item.get("type") == "reasoning"
            and (not isinstance(item.get("encrypted_content"), str) or not item["encrypted_content"])
            for item in output
        ):
            continue
        if any(
            _json_object(item.get("arguments")) is None
            for item in output if item.get("type") == "function_call"
        ):
            continue
        try:
            if _contains_secret(output, mask) or _contains_secret([call.arguments for call in calls], mask):
                continue
        except Exception:
            continue  # Keep prepared text when secret masking cannot be checked.
        call_ids = [call.call_id for call in calls]
        if not all(call_ids) or len(set(call_ids)) != len(call_ids):
            continue
        assistant = render(record)
        if _json_object(assistant) != _json_object(result.function_calls_text()):
            continue
        results = []
        for call_id, following in zip(call_ids, records[index + 1:index + 1 + len(calls)]):
            metadata = result_from_metadata(following.get("metadata"))
            items = metadata.input_items if metadata else []
            text = render(following)
            if (
                following.get("ai") or not isinstance(text, str)
                or len(items) != 1 or not isinstance(items[0], dict)
                or items[0].get("type") != "function_call_output"
                or items[0].get("call_id") != call_id
            ):
                break
            results.append({"type": "function_call_output", "call_id": call_id, "output": text})
        if len(results) == len(calls):
            groups.append({
                PREFIX_HASH: prefix_hash, "assistant": assistant,
                "output": deepcopy(output), "results": results,
            })
    return groups


def project_history(items: list[dict], groups: list[dict], scope: dict) -> list[dict]:
    indices = {value: index for index, value in enumerate(prefix_hashes(items, scope))}
    replacements = {}
    used_calls, used_items = set(), set()
    for group in groups:
        index = indices.get(group.get(PREFIX_HASH))
        if index is None or index + 1 >= len(items):
            continue
        assistant, following = items[index:index + 2]
        if assistant.get("role") != "assistant" or assistant.get("content") != group["assistant"]:
            continue
        content = following.get("content")
        expected = "\n".join(result["output"] for result in group["results"])
        if following.get("role") != "user" or not isinstance(content, str):
            continue
        if content != expected and not content.startswith(expected + "\n"):
            continue
        call_ids = {item["call_id"] for item in group["results"]}
        item_ids = [item["id"] for item in group["output"] if item.get("id")]
        if call_ids & used_calls or set(item_ids) & used_items or len(set(item_ids)) != len(item_ids):
            continue
        used_calls.update(call_ids)
        used_items.update(item_ids)
        suffix = content[len(expected):]
        replacement = [*group["output"], *group["results"]]
        if suffix:
            replacement.append({**following, "content": suffix[1:]})
        replacements[index] = replacement
    result = []
    index = 0
    while index < len(items):
        if index in replacements:
            result.extend(deepcopy(replacements[index]))
            index += 2
        else:
            result.append(deepcopy(items[index]))
            index += 1
    return result
