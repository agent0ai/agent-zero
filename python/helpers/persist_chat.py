from collections import OrderedDict
from datetime import datetime
from typing import Any
import uuid
from agent import Agent, AgentConfig, AgentContext, AgentContextType
from python.helpers import files, history
import json
from initialize import initialize_agent

from python.helpers.log import Log, LogItem

CHATS_FOLDER = "usr/chats"
LOG_SIZE = 1000
CHAT_FILE_NAME = "chat.json"


def get_chat_folder_path(ctxid: str):
    """
    Get the folder path for any context (chat or task).

    Args:
        ctxid: The context ID

    Returns:
        The absolute path to the context folder
    """
    return files.get_abs_path(CHATS_FOLDER, ctxid)

def get_chat_msg_files_folder(ctxid: str):
    return files.get_abs_path(get_chat_folder_path(ctxid), "messages")

def save_tmp_chat(context: AgentContext):
    """Save context to the chats folder"""
    # Skip saving BACKGROUND contexts as they should be ephemeral
    if context.type == AgentContextType.BACKGROUND:
        return

    path = _get_chat_file_path(context.id)
    files.make_dirs(path)
    data = _serialize_context(context)
    js = _safe_json_serialize(data, ensure_ascii=False)
    files.write_file(path, js)


def save_tmp_chats():
    """Save all contexts to the chats folder"""
    for context in AgentContext.all():
        # Skip BACKGROUND contexts as they should be ephemeral
        if context.type == AgentContextType.BACKGROUND:
            continue
        save_tmp_chat(context)


def load_tmp_chats():
    """Load all contexts from the chats folder"""
    _convert_v080_chats()
    folders = files.list_files(CHATS_FOLDER, "*")
    json_files = []
    for folder_name in folders:
        json_files.append(_get_chat_file_path(folder_name))

    ctxids = []
    for file in json_files:
        try:
            js = files.read_file(file)
            data = json.loads(js)
            ctx = _deserialize_context(data)
            ctxids.append(ctx.id)
        except Exception as e:
            print(f"Error loading chat {file}: {e}")
    return ctxids


def _get_chat_file_path(ctxid: str):
    return files.get_abs_path(CHATS_FOLDER, ctxid, CHAT_FILE_NAME)


def _convert_v080_chats():
    json_files = files.list_files(CHATS_FOLDER, "*.json")
    for file in json_files:
        path = files.get_abs_path(CHATS_FOLDER, file)
        name = file.rstrip(".json")
        new = _get_chat_file_path(name)
        files.move_file(path, new)


def load_json_chats(jsons: list[str]):
    """Load contexts from JSON strings"""
    ctxids = []
    for js in jsons:
        data = json.loads(js)
        if "id" in data:
            del data["id"]  # remove id to get new
        ctx = _deserialize_context(data)
        ctxids.append(ctx.id)
    return ctxids


def export_json_chat(context: AgentContext):
    """Export context as JSON string"""
    data = _serialize_context(context)
    js = _safe_json_serialize(data, ensure_ascii=False)
    return js


def fork_context(source_context: AgentContext, fork_at_log_no=None):
    """Deep-copy a context, optionally truncating at a log position.

    Args:
        source_context: The context to fork from.
        fork_at_log_no: If provided, truncate the fork's log and history
            to include only items up to this log number.

    Returns:
        A new AgentContext instance with its own ID and log GUID.
    """
    source_id = source_context.id
    source_name = source_context.name or "Chat"

    # 1. Serialize and deep-copy via JSON round-trip
    serialized = _serialize_context(source_context)
    data = json.loads(_safe_json_serialize(serialized, ensure_ascii=False))

    # 2. Optionally truncate at the fork point
    if fork_at_log_no is not None:
        _truncate_fork_data(data, fork_at_log_no)

    # 3. Remove ID so _deserialize_context generates a new one
    if "id" in data:
        del data["id"]

    # 4. Auto-name with collision check
    base_name = f"{source_name} (fork)"
    existing_names = {ctx.name for ctx in AgentContext.all()}
    fork_name = base_name
    counter = 2
    while fork_name in existing_names:
        fork_name = f"{source_name} (fork {counter})"
        counter += 1
    data["name"] = fork_name

    # 5. Store fork metadata (in both data and output_data so UI can see it)
    fork_info = {
        "forked_from": source_id,
        "fork_point": fork_at_log_no,
        "fork_timestamp": datetime.now().isoformat(),
    }
    data.setdefault("data", {})
    data["data"]["fork_info"] = fork_info
    data.setdefault("output_data", {})
    data["output_data"]["fork_info"] = fork_info

    # 6. Generate new log GUID for fresh polling state
    data.setdefault("log", {})
    data["log"]["guid"] = str(uuid.uuid4())

    # 7. Deserialize into a new context
    return _deserialize_context(data)


def _truncate_fork_data(data, fork_at_log_no):
    """Truncate serialized context data at a specific log item number.

    Filters the log to keep only items where no <= fork_at_log_no, then
    truncates agent 0's history to match the remaining user/response count.

    Args:
        data: Serialized context dict (mutated in place).
        fork_at_log_no: The log item number to truncate at (inclusive).
    """
    # 1. Filter log items
    logs = data.get("log", {}).get("logs", [])
    truncated_logs = [item for item in logs if item.get("no", 0) <= fork_at_log_no]
    data["log"]["logs"] = truncated_logs

    # 2. Count user-type and response-type (agent 0) log items
    user_count = 0
    response_count = 0
    for item in truncated_logs:
        item_type = item.get("type", "")
        if item_type == "user":
            user_count += 1
        elif item_type == "response" and item.get("agent_number", item.get("agentno", -1)) == 0:
            response_count += 1

    keep_messages = user_count + response_count

    # 3. Truncate agent 0's history
    agents = data.get("agents", [])
    for agent_data in agents:
        if agent_data.get("number", -1) != 0:
            continue
        history_str = agent_data.get("history", "")
        if not history_str:
            break
        try:
            hist = json.loads(history_str)
        except (json.JSONDecodeError, TypeError):
            break
        current = hist.get("current", {})
        messages = current.get("messages", [])
        if len(messages) > keep_messages:
            current["messages"] = messages[:keep_messages]
        hist["current"] = current
        agent_data["history"] = json.dumps(hist, ensure_ascii=False)
        break


def remove_chat(ctxid):
    """Remove a chat or task context"""
    path = get_chat_folder_path(ctxid)
    files.delete_dir(path)


def remove_msg_files(ctxid):
    """Remove all message files for a chat or task context"""
    path = get_chat_msg_files_folder(ctxid)
    files.delete_dir(path)


def _serialize_context(context: AgentContext):
    # serialize agents
    agents = []
    agent = context.agent0
    while agent:
        agents.append(_serialize_agent(agent))
        agent = agent.data.get(Agent.DATA_NAME_SUBORDINATE, None)


    data = {k: v for k, v in context.data.items() if not k.startswith("_")}
    output_data = {k: v for k, v in context.output_data.items() if not k.startswith("_")}

    return {
        "id": context.id,
        "name": context.name,
        "created_at": (
            context.created_at.isoformat()
            if context.created_at
            else datetime.fromtimestamp(0).isoformat()
        ),
        "type": context.type.value,
        "last_message": (
            context.last_message.isoformat()
            if context.last_message
            else datetime.fromtimestamp(0).isoformat()
        ),
        "agents": agents,
        "streaming_agent": (
            context.streaming_agent.number if context.streaming_agent else 0
        ),
        "log": _serialize_log(context.log),
        "data": data,
        "output_data": output_data,
    }


def _serialize_agent(agent: Agent):
    data = {k: v for k, v in agent.data.items() if not k.startswith("_")}

    history = agent.history.serialize()

    return {
        "number": agent.number,
        "data": data,
        "history": history,
    }


def _serialize_log(log: Log):
    # Guard against concurrent log mutations while serializing.
    with log._lock:
        logs = [item.output() for item in log.logs[-LOG_SIZE:]]  # serialize LogItem objects
        guid = log.guid
        progress = log.progress
        progress_no = log.progress_no
    return {
        "guid": guid,
        "logs": logs,
        "progress": progress,
        "progress_no": progress_no,
    }


def _deserialize_context(data):
    config = initialize_agent()
    log = _deserialize_log(data.get("log", None))

    context = AgentContext(
        config=config,
        id=data.get("id", None),  # get new id
        name=data.get("name", None),
        created_at=(
            datetime.fromisoformat(
                # older chats may not have created_at - backcompat
                data.get("created_at", datetime.fromtimestamp(0).isoformat())
            )
        ),
        type=AgentContextType(data.get("type", AgentContextType.USER.value)),
        last_message=(
            datetime.fromisoformat(
                data.get("last_message", datetime.fromtimestamp(0).isoformat())
            )
        ),
        log=log,
        paused=False,
        data=data.get("data", {}),
        output_data=data.get("output_data", {}),
        # agent0=agent0,
        # streaming_agent=straming_agent,
    )

    agents = data.get("agents", [])
    agent0 = _deserialize_agents(agents, config, context)
    streaming_agent = agent0
    while streaming_agent and streaming_agent.number != data.get("streaming_agent", 0):
        streaming_agent = streaming_agent.data.get(Agent.DATA_NAME_SUBORDINATE, None)

    context.agent0 = agent0
    context.streaming_agent = streaming_agent

    return context


def _deserialize_agents(
    agents: list[dict[str, Any]], config: AgentConfig, context: AgentContext
) -> Agent:
    prev: Agent | None = None
    zero: Agent | None = None

    for ag in agents:
        current = Agent(
            number=ag["number"],
            config=config,
            context=context,
        )
        current.data = ag.get("data", {})
        current.history = history.deserialize_history(
            ag.get("history", ""), agent=current
        )
        if not zero:
            zero = current

        if prev:
            prev.set_data(Agent.DATA_NAME_SUBORDINATE, current)
            current.set_data(Agent.DATA_NAME_SUPERIOR, prev)
        prev = current

    return zero or Agent(0, config, context)


# def _deserialize_history(history: list[dict[str, Any]]):
#     result = []
#     for hist in history:
#         content = hist.get("content", "")
#         msg = (
#             HumanMessage(content=content)
#             if hist.get("type") == "human"
#             else AIMessage(content=content)
#         )
#         result.append(msg)
#     return result


def _deserialize_log(data: dict[str, Any]) -> "Log":
    log = Log()
    log.guid = data.get("guid", str(uuid.uuid4()))
    log.set_initial_progress()

    # Deserialize the list of LogItem objects
    i = 0
    for item_data in data.get("logs", []):
        agentno = item_data.get("agentno")
        if agentno is None:
            agentno = item_data.get("agent_number", 0)
        log.logs.append(
            LogItem(
                log=log,  # restore the log reference
                no=i,  # item_data["no"],
                type=item_data["type"],
                heading=item_data.get("heading", ""),
                content=item_data.get("content", ""),
                kvps=OrderedDict(item_data["kvps"]) if item_data["kvps"] else None,
                timestamp=item_data.get("timestamp", 0.0),
                agentno=agentno,
                id=item_data.get("id"),
            )
        )
        log.updates.append(i)
        i += 1

    return log


def _safe_json_serialize(obj, **kwargs):
    def serializer(o):
        if isinstance(o, dict):
            return {k: v for k, v in o.items() if is_json_serializable(v)}
        elif isinstance(o, (list, tuple)):
            return [item for item in o if is_json_serializable(item)]
        elif is_json_serializable(o):
            return o
        else:
            return None  # Skip this property

    def is_json_serializable(item):
        try:
            json.dumps(item)
            return True
        except (TypeError, OverflowError):
            return False

    return json.dumps(obj, default=serializer, **kwargs)
