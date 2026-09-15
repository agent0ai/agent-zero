import base64
import json
import os
import re
import socketserver
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from python.helpers import files, tokens


BASE54_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstyz"
BASE54_INDEX = {char: idx for idx, char in enumerate(BASE54_ALPHABET)}
BASE54_BASE = len(BASE54_ALPHABET)

CONTROL_TAG_SHOW_SAVINGS = "**show savings**"
CONTROL_TAG_SHOW_TOTAL = "**show total**"


def _safe_count_tokens(text: str) -> int:
    if not text:
        return 0
    try:
        return tokens.count_tokens(text)
    except Exception:
        return max(1, len(text.split()))


def _token_stats(raw_text: str, encoded_text: str) -> Dict[str, int]:
    raw_tokens = _safe_count_tokens(raw_text)
    encoded_tokens = _safe_count_tokens(encoded_text)
    saved = raw_tokens - encoded_tokens
    if saved < 0:
        saved = 0
    return {
        "raw": raw_tokens,
        "encoded": encoded_tokens,
        "saved": saved,
    }


def _strip_control_tags(text: str) -> Tuple[str, bool, bool]:
    show_savings = False
    show_total = False
    if not text:
        return text, show_savings, show_total

    if re.search(re.escape(CONTROL_TAG_SHOW_SAVINGS), text, flags=re.IGNORECASE):
        show_savings = True
        text = re.sub(
            re.escape(CONTROL_TAG_SHOW_SAVINGS), "", text, flags=re.IGNORECASE
        )
    if re.search(re.escape(CONTROL_TAG_SHOW_TOTAL), text, flags=re.IGNORECASE):
        show_total = True
        show_savings = True
        text = re.sub(
            re.escape(CONTROL_TAG_SHOW_TOTAL), "", text, flags=re.IGNORECASE
        )

    return text.strip(), show_savings, show_total


def b54encode(payload: bytes) -> str:
    if not payload:
        return ""
    num = int.from_bytes(payload, "big")
    encoded: List[str] = []
    while num > 0:
        num, rem = divmod(num, BASE54_BASE)
        encoded.append(BASE54_ALPHABET[rem])
    pad = 0
    for byte in payload:
        if byte == 0:
            pad += 1
        else:
            break
    encoded_str = "".join(reversed(encoded)) if encoded else ""
    return (BASE54_ALPHABET[0] * pad) + encoded_str


def b54decode(payload: str) -> bytes:
    if payload == "":
        return b""
    num = 0
    for char in payload:
        if char not in BASE54_INDEX:
            raise ValueError(f"Invalid base54 character: {char!r}")
        num = num * BASE54_BASE + BASE54_INDEX[char]
    pad = 0
    for char in payload:
        if char == BASE54_ALPHABET[0]:
            pad += 1
        else:
            break
    decoded = b""
    if num > 0:
        byte_len = (num.bit_length() + 7) // 8
        decoded = num.to_bytes(byte_len, "big")
    return (b"\x00" * pad) + decoded


def _b64encode_text(text: str, encoding: str) -> str:
    return base64.b64encode(text.encode(encoding, errors="replace")).decode("ascii")


def _context_text(messages: List[Dict[str, str]]) -> str:
    return "\n".join(f"{entry['role']}: {entry['text']}" for entry in messages).strip()


@dataclass
class ConversationState:
    conversation_id: str
    encoding: str = "utf-8"
    language: str = "unknown"
    messages: List[Dict[str, str]] = field(default_factory=list)
    context_b64: str = ""
    context_tokens: Dict[str, int] = field(default_factory=dict)
    prompt_tokens_raw: int = 0
    prompt_tokens_encoded: int = 0
    response_tokens_raw: int = 0
    response_tokens_encoded: int = 0
    last_prompt_stats: Dict[str, int] = field(default_factory=dict)
    last_response_stats: Dict[str, int] = field(default_factory=dict)
    pending_show_savings: bool = False
    pending_show_total: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "encoding": self.encoding,
            "language": self.language,
            "messages": self.messages,
            "context_b64": self.context_b64,
            "context_tokens": self.context_tokens,
            "prompt_tokens_raw": self.prompt_tokens_raw,
            "prompt_tokens_encoded": self.prompt_tokens_encoded,
            "response_tokens_raw": self.response_tokens_raw,
            "response_tokens_encoded": self.response_tokens_encoded,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ConversationState":
        return cls(
            conversation_id=payload.get("conversation_id", ""),
            encoding=payload.get("encoding", "utf-8"),
            language=payload.get("language", "unknown"),
            messages=payload.get("messages", []),
            context_b64=payload.get("context_b64", ""),
            context_tokens=payload.get("context_tokens", {}),
            prompt_tokens_raw=payload.get("prompt_tokens_raw", 0),
            prompt_tokens_encoded=payload.get("prompt_tokens_encoded", 0),
            response_tokens_raw=payload.get("response_tokens_raw", 0),
            response_tokens_encoded=payload.get("response_tokens_encoded", 0),
        )


class ContextStore:
    def __init__(self, dataset_path: str, refresh_interval: float = 5.0):
        self.dataset_path = dataset_path
        self.refresh_interval = refresh_interval
        self._lock = threading.Lock()
        self._dirty = False
        self._conversations: Dict[str, ConversationState] = {}
        self._stop_event = threading.Event()
        self._load()
        self._thread = threading.Thread(
            target=self._maintenance_loop,
            name="tcp-context-maintainer",
            daemon=True,
        )
        self._thread.start()

    def _load(self) -> None:
        if not os.path.exists(self.dataset_path):
            return
        try:
            with open(self.dataset_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return
        conversations = data.get("conversations", {})
        for conv_id, payload in conversations.items():
            state = ConversationState.from_dict(payload)
            if not state.conversation_id:
                state.conversation_id = conv_id
            self._conversations[conv_id] = state

    def _maintenance_loop(self) -> None:
        while not self._stop_event.wait(self.refresh_interval):
            self._flush_if_dirty()

    def _flush_if_dirty(self) -> None:
        with self._lock:
            if not self._dirty:
                return
            snapshot = self._snapshot_locked()
            self._dirty = False
        self._persist_snapshot(snapshot)

    def _snapshot_locked(self) -> Dict[str, Any]:
        for state in self._conversations.values():
            self._refresh_context_locked(state)
        return {
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "conversations": {
                conv_id: state.to_dict()
                for conv_id, state in self._conversations.items()
            },
        }

    def _persist_snapshot(self, snapshot: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.dataset_path), exist_ok=True)
        tmp_path = f"{self.dataset_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, ensure_ascii=True, indent=2)
        os.replace(tmp_path, self.dataset_path)

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=self.refresh_interval)
        self._flush_if_dirty()

    def get_or_create(
        self,
        conversation_id: Optional[str],
        encoding: Optional[str],
        language: Optional[str],
    ) -> ConversationState:
        with self._lock:
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            state = self._conversations.get(conversation_id)
            if state is None:
                state = ConversationState(conversation_id=conversation_id)
                self._conversations[conversation_id] = state
            if encoding:
                state.encoding = encoding
            if language:
                state.language = language
            return state

    def list_contexts(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            contexts = {}
            for conv_id, state in self._conversations.items():
                self._refresh_context_locked(state)
                contexts[conv_id] = {
                    "context_b64": state.context_b64,
                    "encoding": state.encoding,
                    "language": state.language,
                    "context_tokens": state.context_tokens,
                }
            return contexts

    def get_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            state = self._conversations.get(conversation_id)
            if not state:
                return None
            self._refresh_context_locked(state)
            return {
                "conversation_id": state.conversation_id,
                "context_b64": state.context_b64,
                "encoding": state.encoding,
                "language": state.language,
                "context_tokens": state.context_tokens,
            }

    def record_prompt(
        self,
        conversation_id: Optional[str],
        text: str,
        encoding: Optional[str],
        language: Optional[str],
    ) -> Dict[str, Any]:
        state = self.get_or_create(conversation_id, encoding, language)
        clean_text, show_savings, show_total = _strip_control_tags(text)
        encoded_prompt = _b64encode_text(clean_text, state.encoding)
        prompt_stats = _token_stats(clean_text, encoded_prompt)
        with self._lock:
            state.messages.append({"role": "user", "text": clean_text})
            state.prompt_tokens_raw += prompt_stats["raw"]
            state.prompt_tokens_encoded += prompt_stats["encoded"]
            state.last_prompt_stats = prompt_stats
            state.pending_show_savings = show_savings or show_total
            state.pending_show_total = show_total
            self._refresh_context_locked(state)
            self._dirty = True
            response = {
                "conversation_id": state.conversation_id,
                "encoding": state.encoding,
                "language": state.language,
                "encoded_prompt_b64": encoded_prompt,
                "context_b64": state.context_b64,
                "context_tokens": state.context_tokens,
                "prompt_tokens": prompt_stats,
                "savings_request": {
                    "show_savings": state.pending_show_savings,
                    "show_total": state.pending_show_total,
                },
            }
        return response

    def record_response(
        self,
        conversation_id: str,
        payload_b54: str,
    ) -> Dict[str, Any]:
        with self._lock:
            state = self._conversations.get(conversation_id)
            if not state:
                raise KeyError("Unknown conversation_id")
            encoding = state.encoding
            language = state.language

        decoded_bytes = b54decode(payload_b54)
        decoded_text = decoded_bytes.decode(encoding, errors="replace")
        response_stats = _token_stats(decoded_text, payload_b54)

        with self._lock:
            state.messages.append({"role": "assistant", "text": decoded_text})
            state.response_tokens_raw += response_stats["raw"]
            state.response_tokens_encoded += response_stats["encoded"]
            state.last_response_stats = response_stats
            self._refresh_context_locked(state)
            savings_payload = None
            tagline = None
            decoded_text_with_tagline = None
            if state.pending_show_savings:
                savings_payload = self._build_savings_payload(state)
                tagline = self._format_tagline(
                    savings_payload,
                    include_total=state.pending_show_total,
                )
                decoded_text_with_tagline = (
                    decoded_text + "\n" + tagline if decoded_text else tagline
                )
            state.pending_show_savings = False
            state.pending_show_total = False
            self._dirty = True
            response = {
                "conversation_id": state.conversation_id,
                "encoding": encoding,
                "language": language,
                "response_b54": payload_b54,
                "decoded_text": decoded_text,
                "response_tokens": response_stats,
                "context_b64": state.context_b64,
                "context_tokens": state.context_tokens,
            }
            if savings_payload:
                response["savings"] = savings_payload
            if tagline:
                response["tagline"] = tagline
                response["decoded_text_with_tagline"] = decoded_text_with_tagline
        return response

    def _refresh_context_locked(self, state: ConversationState) -> None:
        context_text = _context_text(state.messages)
        state.context_b64 = _b64encode_text(context_text, state.encoding)
        state.context_tokens = _token_stats(context_text, state.context_b64)

    def _build_savings_payload(self, state: ConversationState) -> Dict[str, Any]:
        prompt_stats = state.last_prompt_stats or {"raw": 0, "encoded": 0, "saved": 0}
        response_stats = state.last_response_stats or {
            "raw": 0,
            "encoded": 0,
            "saved": 0,
        }
        context_stats = state.context_tokens or {"raw": 0, "encoded": 0, "saved": 0}
        combined_saved = (
            prompt_stats.get("saved", 0)
            + response_stats.get("saved", 0)
            + context_stats.get("saved", 0)
        )
        totals = {
            "prompt": {
                "raw": state.prompt_tokens_raw,
                "encoded": state.prompt_tokens_encoded,
                "saved": max(
                    0, state.prompt_tokens_raw - state.prompt_tokens_encoded
                ),
            },
            "response": {
                "raw": state.response_tokens_raw,
                "encoded": state.response_tokens_encoded,
                "saved": max(
                    0, state.response_tokens_raw - state.response_tokens_encoded
                ),
            },
            "context": context_stats,
        }
        totals["combined_saved"] = (
            totals["prompt"]["saved"]
            + totals["response"]["saved"]
            + totals["context"]["saved"]
        )
        return {
            "prompt": prompt_stats,
            "response": response_stats,
            "context": context_stats,
            "combined_saved": combined_saved,
            "totals": totals,
        }

    def _format_tagline(self, savings: Dict[str, Any], include_total: bool) -> str:
        prompt_saved = savings["prompt"]["saved"]
        response_saved = savings["response"]["saved"]
        context_saved = savings["context"]["saved"]
        combined_saved = savings["combined_saved"]
        tagline = (
            "Token savings (prompt/response/context/combined): "
            f"{prompt_saved}/{response_saved}/{context_saved}/{combined_saved}."
        )
        if include_total:
            totals = savings.get("totals", {})
            totals_prompt = totals.get("prompt", {}).get("saved", 0)
            totals_response = totals.get("response", {}).get("saved", 0)
            totals_context = totals.get("context", {}).get("saved", 0)
            totals_combined = totals.get("combined_saved", 0)
            tagline += (
                " Total savings (prompt/response/context/combined): "
                f"{totals_prompt}/{totals_response}/{totals_context}/{totals_combined}."
            )
        return tagline


class TokenCompressionProtocolProcessor:
    def __init__(self, store: ContextStore):
        self.store = store

    def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action")
        if not action:
            return {"ok": False, "error": "missing_action"}

        if action == "prompt":
            text = payload.get("text", "")
            if not isinstance(text, str) or text == "":
                return {"ok": False, "error": "missing_text"}
            response = self.store.record_prompt(
                conversation_id=payload.get("conversation_id"),
                text=text,
                encoding=payload.get("encoding"),
                language=payload.get("language"),
            )
            return {"ok": True, "result": response}

        if action == "response":
            conversation_id = payload.get("conversation_id")
            if not conversation_id:
                return {"ok": False, "error": "missing_conversation_id"}
            payload_b54 = payload.get("payload_b54", "")
            if not isinstance(payload_b54, str) or payload_b54 == "":
                return {"ok": False, "error": "missing_payload_b54"}
            try:
                response = self.store.record_response(
                    conversation_id=conversation_id,
                    payload_b54=payload_b54,
                )
            except KeyError:
                return {"ok": False, "error": "unknown_conversation_id"}
            except ValueError as exc:
                return {"ok": False, "error": "invalid_base54", "detail": str(exc)}
            return {"ok": True, "result": response}

        if action == "context_get":
            conversation_id = payload.get("conversation_id")
            if conversation_id:
                context = self.store.get_context(conversation_id)
                if not context:
                    return {"ok": False, "error": "unknown_conversation_id"}
                return {"ok": True, "result": context}
            return {"ok": True, "result": {"contexts": self.store.list_contexts()}}

        if action == "context_reset":
            conversation_id = payload.get("conversation_id")
            if not conversation_id:
                return {"ok": False, "error": "missing_conversation_id"}
            with self.store._lock:
                if conversation_id in self.store._conversations:
                    del self.store._conversations[conversation_id]
                    self.store._dirty = True
                    return {"ok": True, "result": {"conversation_id": conversation_id}}
            return {"ok": False, "error": "unknown_conversation_id"}

        if action == "ping":
            return {"ok": True, "result": {"message": "pong"}}

        return {"ok": False, "error": "unknown_action"}


class TokenCompressionTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass, processor):
        super().__init__(server_address, RequestHandlerClass)
        self.processor = processor


class TokenCompressionRequestHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        while True:
            raw_line = self.rfile.readline()
            if not raw_line:
                break
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                request = json.loads(raw_line.decode("utf-8"))
            except json.JSONDecodeError as exc:
                self._send({"ok": False, "error": "invalid_json", "detail": str(exc)})
                continue
            if not isinstance(request, dict):
                self._send({"ok": False, "error": "invalid_payload"})
                continue
            response = self.server.processor.handle(request)
            self._send(response)

    def _send(self, payload: Dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=True).encode("utf-8") + b"\n"
        self.wfile.write(encoded)


def run_tcp_server(
    host: str = "127.0.0.1",
    port: int = 7543,
    dataset_path: Optional[str] = None,
    refresh_interval: float = 5.0,
) -> None:
    dataset_path = dataset_path or files.get_abs_path(
        "memory", "token_compression_context.json"
    )
    store = ContextStore(dataset_path=dataset_path, refresh_interval=refresh_interval)
    processor = TokenCompressionProtocolProcessor(store)
    server = TokenCompressionTCPServer(
        (host, port), TokenCompressionRequestHandler, processor
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        store.stop()
        server.server_close()


if __name__ == "__main__":
    run_tcp_server()
