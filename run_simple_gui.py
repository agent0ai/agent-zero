import json
import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from urllib import error as url_error
from urllib import request as url_request

from python.helpers import tokens


class SimpleChatGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Simple LLM Chat")
        self.root.minsize(980, 640)

        self.messages: list[dict[str, str]] = []
        self.context_text = ""

        self.provider_var = tk.StringVar(value="Ollama")
        self.model_var = tk.StringVar(
            value=os.environ.get("OLLAMA_MODEL", "llama3")
        )
        self.api_key_var = tk.StringVar(value=os.environ.get("OPENROUTER_API_KEY", ""))
        self.status_var = tk.StringVar(value="Ready")
        self.prompt_tokens_var = tk.StringVar(value="Prompt tokens: 0")
        self.response_tokens_var = tk.StringVar(value="Response tokens: 0")
        self.context_tokens_var = tk.StringVar(value="Context tokens: 0")
        self.total_tokens_var = tk.StringVar(value="Total tokens: 0")

        self._build_layout()
        self._bind_events()

    def _build_layout(self) -> None:
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        chat_frame = ttk.Frame(main_frame)
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        chat_frame.rowconfigure(0, weight=1)
        chat_frame.columnconfigure(0, weight=1)

        self.chat_display = ScrolledText(chat_frame, wrap="word", state="disabled")
        self.chat_display.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.input_text = ScrolledText(chat_frame, height=6, wrap="word")
        self.input_text.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        button_frame = ttk.Frame(chat_frame)
        button_frame.grid(row=1, column=1, sticky="se", padx=(10, 0), pady=(10, 0))

        self.send_button = ttk.Button(button_frame, text="Send", command=self.on_send)
        self.send_button.pack(fill="x", pady=(0, 6))

        self.clear_button = ttk.Button(
            button_frame, text="New Chat", command=self.on_clear
        )
        self.clear_button.pack(fill="x")

        sidebar = ttk.Frame(main_frame)
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.rowconfigure(2, weight=1)
        sidebar.columnconfigure(0, weight=1)

        settings_frame = ttk.LabelFrame(sidebar, text="Settings")
        settings_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)

        ttk.Label(settings_frame, text="Provider").grid(
            row=0, column=0, sticky="w", padx=8, pady=4
        )
        provider_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.provider_var,
            values=["Ollama", "OpenRouter"],
            state="readonly",
        )
        provider_combo.grid(row=0, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(settings_frame, text="Model").grid(
            row=1, column=0, sticky="w", padx=8, pady=4
        )
        self.model_combo = ttk.Combobox(
            settings_frame, textvariable=self.model_var, values=[]
        )
        self.model_combo.grid(row=1, column=1, sticky="ew", padx=8, pady=4)

        self.refresh_button = ttk.Button(
            settings_frame, text="Load Ollama Models", command=self.on_refresh_models
        )
        self.refresh_button.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=4)

        ttk.Label(settings_frame, text="OpenRouter API Key").grid(
            row=3, column=0, sticky="w", padx=8, pady=4
        )
        self.api_key_entry = ttk.Entry(
            settings_frame, textvariable=self.api_key_var, show="*"
        )
        self.api_key_entry.grid(row=3, column=1, sticky="ew", padx=8, pady=4)

        context_frame = ttk.LabelFrame(sidebar, text="Conversation Context")
        context_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        context_frame.columnconfigure(0, weight=1)
        context_frame.rowconfigure(0, weight=1)

        self.context_display = ScrolledText(
            context_frame, wrap="word", height=12, state="disabled"
        )
        self.context_display.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        tokens_frame = ttk.LabelFrame(sidebar, text="Token Counts")
        tokens_frame.grid(row=2, column=0, sticky="ew")

        ttk.Label(tokens_frame, textvariable=self.prompt_tokens_var).pack(
            anchor="w", padx=8, pady=2
        )
        ttk.Label(tokens_frame, textvariable=self.response_tokens_var).pack(
            anchor="w", padx=8, pady=2
        )
        ttk.Label(tokens_frame, textvariable=self.context_tokens_var).pack(
            anchor="w", padx=8, pady=2
        )
        ttk.Label(tokens_frame, textvariable=self.total_tokens_var).pack(
            anchor="w", padx=8, pady=2
        )

        status_bar = ttk.Label(
            self.root, textvariable=self.status_var, anchor="w"
        )
        status_bar.pack(fill="x")

        self._refresh_provider_ui()

    def _bind_events(self) -> None:
        self.input_text.bind("<Control-Return>", lambda _evt: self.on_send())
        self.provider_var.trace_add("write", lambda *_: self._refresh_provider_ui())

    def _refresh_provider_ui(self) -> None:
        provider = self.provider_var.get().strip()
        if provider == "Ollama":
            self.refresh_button.state(["!disabled"])
            self.api_key_entry.state(["disabled"])
        else:
            self.api_key_entry.state(["!disabled"])
            if not self.model_var.get().strip():
                self.model_var.set(
                    os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
                )
            self.refresh_button.state(["disabled"])

    def on_refresh_models(self) -> None:
        if self.provider_var.get() != "Ollama":
            return
        self._set_status("Loading Ollama models...")
        threading.Thread(target=self._load_ollama_models, daemon=True).start()

    def _load_ollama_models(self) -> None:
        try:
            response = self._post_json(
                "http://localhost:11434/api/tags", payload={}, method="GET"
            )
            models = sorted([entry["name"] for entry in response.get("models", [])])
        except Exception as exc:
            self.root.after(
                0, lambda: self._set_status(f"Failed to load Ollama models: {exc}")
            )
            return

        def update_models() -> None:
            self.model_combo["values"] = models
            if models and self.model_var.get() not in models:
                self.model_var.set(models[0])
            self._set_status("Ollama models loaded.")

        self.root.after(0, update_models)

    def on_send(self) -> None:
        user_text = self.input_text.get("1.0", "end").strip()
        if not user_text:
            return
        if not self.model_var.get().strip():
            self._set_status("Please enter a model name.")
            return

        if self.provider_var.get() == "OpenRouter" and not self.api_key_var.get().strip():
            self._set_status("OpenRouter API key is required.")
            return

        self._append_chat("user", user_text)
        self.messages.append({"role": "user", "content": user_text})
        self._update_context_display()
        self._update_prompt_tokens(user_text)
        self.response_tokens_var.set("Response tokens: 0")
        self._set_status("Sending...")
        self._set_busy(True)

        self.input_text.delete("1.0", "end")

        messages_snapshot = list(self.messages)
        provider = self.provider_var.get()
        model = self.model_var.get().strip()
        api_key = self.api_key_var.get().strip()

        threading.Thread(
            target=self._call_model,
            args=(provider, model, api_key, messages_snapshot),
            daemon=True,
        ).start()

    def _call_model(
        self,
        provider: str,
        model: str,
        api_key: str,
        messages: list[dict[str, str]],
    ) -> None:
        try:
            if provider == "Ollama":
                response_text = self._call_ollama(model, messages)
            else:
                response_text = self._call_openrouter(model, api_key, messages)
        except Exception as exc:
            self.root.after(0, lambda: self._handle_error(exc))
            return
        self.root.after(0, lambda: self._handle_response(response_text))

    def _handle_response(self, response_text: str) -> None:
        self._append_chat("assistant", response_text)
        self.messages.append({"role": "assistant", "content": response_text})
        self._update_context_display()
        self._update_token_counts(response_text)
        self._set_busy(False)
        self._set_status("Ready")

    def _handle_error(self, exc: Exception) -> None:
        self._append_chat("assistant", f"[Error] {exc}")
        self._set_busy(False)
        self._set_status("Error while calling model.")

    def on_clear(self) -> None:
        self.messages.clear()
        self.context_text = ""
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self._append_chat("assistant", "[New conversation started]")
        self._update_context_display()
        self.prompt_tokens_var.set("Prompt tokens: 0")
        self.response_tokens_var.set("Response tokens: 0")
        self.context_tokens_var.set("Context tokens: 0")
        self.total_tokens_var.set("Total tokens: 0")

    def _append_chat(self, role: str, content: str) -> None:
        self.chat_display.configure(state="normal")
        label = "You" if role == "user" else "Assistant"
        self.chat_display.insert("end", f"{label}: {content}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _update_context_display(self) -> None:
        self.context_text = "\n".join(
            f"{message['role']}: {message['content']}" for message in self.messages
        )
        self.context_display.configure(state="normal")
        self.context_display.delete("1.0", "end")
        self.context_display.insert("end", self.context_text)
        self.context_display.configure(state="disabled")
        self._update_context_tokens()

    def _update_token_counts(self, response_text: str) -> None:
        prompt_text = self.messages[-2]["content"] if len(self.messages) >= 2 else ""
        prompt_tokens = self._safe_count_tokens(prompt_text)
        response_tokens = self._safe_count_tokens(response_text)
        context_tokens = self._safe_count_tokens(self.context_text)
        total_tokens = context_tokens

        self.prompt_tokens_var.set(f"Prompt tokens: {prompt_tokens}")
        self.response_tokens_var.set(f"Response tokens: {response_tokens}")
        self.context_tokens_var.set(f"Context tokens: {context_tokens}")
        self.total_tokens_var.set(f"Total tokens: {total_tokens}")

    def _update_prompt_tokens(self, prompt_text: str) -> None:
        prompt_tokens = self._safe_count_tokens(prompt_text)
        self.prompt_tokens_var.set(f"Prompt tokens: {prompt_tokens}")

    def _update_context_tokens(self) -> None:
        context_tokens = self._safe_count_tokens(self.context_text)
        self.context_tokens_var.set(f"Context tokens: {context_tokens}")
        self.total_tokens_var.set(f"Total tokens: {context_tokens}")

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)

    def _set_busy(self, busy: bool) -> None:
        if busy:
            self.send_button.state(["disabled"])
        else:
            self.send_button.state(["!disabled"])

    def _safe_count_tokens(self, text: str) -> int:
        if not text:
            return 0
        try:
            return tokens.count_tokens(text)
        except Exception:
            return len(text.split())

    def _call_ollama(self, model: str, messages: list[dict[str, str]]) -> str:
        payload = {"model": model, "messages": messages, "stream": False}
        response = self._post_json("http://localhost:11434/api/chat", payload=payload)
        message = response.get("message", {})
        return str(message.get("content", "")).strip()

    def _call_openrouter(
        self, model: str, api_key: str, messages: list[dict[str, str]]
    ) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Agent Zero Simple GUI",
        }
        response = self._post_json(
            "https://openrouter.ai/api/v1/chat/completions",
            payload=payload,
            headers=headers,
        )
        choices = response.get("choices", [])
        if not choices:
            return ""
        message = choices[0].get("message", {})
        return str(message.get("content", "")).strip()

    def _post_json(
        self,
        url: str,
        payload: dict[str, object],
        headers: dict[str, str] | None = None,
        method: str = "POST",
    ) -> dict[str, object]:
        data = None if method == "GET" else json.dumps(payload).encode("utf-8")
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)
        req = url_request.Request(url, data=data, headers=req_headers, method=method)
        try:
            with url_request.urlopen(req, timeout=120) as resp:
                body = resp.read().decode("utf-8")
        except url_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except url_error.URLError as exc:
            raise RuntimeError(f"Connection error: {exc}") from exc
        return json.loads(body) if body else {}


def main() -> None:
    root = tk.Tk()
    app = SimpleChatGUI(root)
    app._append_chat("assistant", "Welcome! Enter a prompt to begin.")
    root.mainloop()


if __name__ == "__main__":
    main()
