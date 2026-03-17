import json
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from python.survey_assistant.browser_render import render_url
from python.survey_assistant.extract import extract_form_fields
from python.survey_assistant.llm import ollama_available, suggest_answers_with_ollama
from python.survey_assistant.profile import SurveyProfile, DEFAULT_PROFILE_PATH


class SurveyHelperGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Survey Helper (Human-in-the-loop)")
        self.root.minsize(1100, 720)

        self.url_var = tk.StringVar(value="")
        self.ollama_model_var = tk.StringVar(value=os.environ.get("OLLAMA_MODEL", "llama3"))
        self.status_var = tk.StringVar(value="Ready")

        self._last_html: str | None = None
        self._last_title: str | None = None
        self._last_final_url: str | None = None
        self._screenshot_path: str | None = None
        self._screenshot_img = None  # keep reference

        self._build_layout()
        self._load_profile_into_editor()

    def _build_layout(self) -> None:
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=2)
        main.columnconfigure(1, weight=3)
        main.rowconfigure(1, weight=1)

        top = ttk.Frame(main)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="URL").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(top, textvariable=self.url_var).grid(row=0, column=1, sticky="ew")

        ttk.Button(top, text="Load (render + screenshot)", command=self.on_load).grid(
            row=0, column=2, sticky="ew", padx=(8, 0)
        )
        ttk.Button(top, text="Extract questions", command=self.on_extract).grid(
            row=0, column=3, sticky="ew", padx=(8, 0)
        )

        ttk.Label(top, text="Ollama model").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(top, textvariable=self.ollama_model_var, width=18).grid(
            row=1, column=1, sticky="w", pady=(8, 0)
        )
        ttk.Button(top, text="Suggest answers", command=self.on_suggest).grid(
            row=1, column=2, sticky="ew", padx=(8, 0), pady=(8, 0)
        )

        left = ttk.LabelFrame(main, text="Preview + extracted questions")
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        self.preview_label = ttk.Label(left, text="(No preview loaded)")
        self.preview_label.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        self.questions_text = ScrolledText(left, wrap="word")
        self.questions_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        right = ttk.Notebook(main)
        right.grid(row=1, column=1, sticky="nsew")

        tab_profile = ttk.Frame(right, padding=8)
        tab_suggestions = ttk.Frame(right, padding=8)
        right.add(tab_profile, text="Profile (editable JSON)")
        right.add(tab_suggestions, text="Suggestions")

        tab_profile.rowconfigure(0, weight=1)
        tab_profile.columnconfigure(0, weight=1)

        self.profile_editor = ScrolledText(tab_profile, wrap="word")
        self.profile_editor.grid(row=0, column=0, sticky="nsew")

        prof_btns = ttk.Frame(tab_profile)
        prof_btns.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(prof_btns, text="Reload from disk", command=self._load_profile_into_editor).pack(
            side="left"
        )
        ttk.Button(prof_btns, text="Save to disk", command=self._save_profile_from_editor).pack(
            side="left", padx=(8, 0)
        )
        ttk.Label(prof_btns, text=f"Path: {DEFAULT_PROFILE_PATH}").pack(side="left", padx=(12, 0))

        tab_suggestions.rowconfigure(0, weight=1)
        tab_suggestions.columnconfigure(0, weight=1)
        self.suggestions_text = ScrolledText(tab_suggestions, wrap="word")
        self.suggestions_text.grid(row=0, column=0, sticky="nsew")

        status = ttk.Label(self.root, textvariable=self.status_var, anchor="w")
        status.pack(fill="x")

    def _set_status(self, msg: str) -> None:
        self.status_var.set(msg)

    def _load_profile_into_editor(self) -> None:
        profile = SurveyProfile.load()
        self.profile_editor.delete("1.0", "end")
        self.profile_editor.insert("end", json.dumps(profile.as_dict(), indent=2, ensure_ascii=False))

    def _save_profile_from_editor(self) -> None:
        try:
            data = json.loads(self.profile_editor.get("1.0", "end").strip() or "{}")
            if not isinstance(data, dict):
                raise ValueError("Profile JSON must be an object")
        except Exception as exc:
            messagebox.showerror("Invalid JSON", str(exc))
            return

        profile = SurveyProfile.load()
        profile.merge_updates(data)
        profile.save()
        self._set_status("Profile saved.")

    def on_load(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            return

        self._set_status("Loading and rendering URL...")
        self.questions_text.delete("1.0", "end")
        self.questions_text.insert("end", "Loading...\n")

        def worker() -> None:
            try:
                self._screenshot_path = os.path.join("tmp", "survey_helper", "preview.png")
                result = render_url(url, screenshot_path=self._screenshot_path)
                self._last_html = result.html
                self._last_title = result.title
                self._last_final_url = result.final_url
                self.root.after(0, self._update_preview)
                self.root.after(
                    0,
                    lambda: self._set_status(
                        f"Loaded: {self._last_title or '(no title)'}"
                    ),
                )
            except Exception as exc:
                self.root.after(0, lambda: self._set_status(f"Load failed: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _update_preview(self) -> None:
        if self._last_final_url:
            self.preview_label.configure(text=f"{self._last_final_url}")
        if self._screenshot_path and os.path.exists(self._screenshot_path):
            try:
                self._screenshot_img = tk.PhotoImage(file=self._screenshot_path)
                # show a scaled-down preview if very large
                if self._screenshot_img.width() > 560:
                    subsample = max(1, self._screenshot_img.width() // 560)
                    self._screenshot_img = self._screenshot_img.subsample(subsample)
                self.preview_label.configure(image=self._screenshot_img, compound="top")
            except Exception:
                # preview is best-effort; ignore if tk cannot decode the screenshot
                pass

    def on_extract(self) -> None:
        if not self._last_html:
            self._set_status("Nothing to extract yet. Load a URL first.")
            return
        self._set_status("Extracting questions...")
        fields = extract_form_fields(self._last_html)
        lines = []
        for i, f in enumerate(fields, start=1):
            label = f.label or f.name or f.id or "(unlabeled)"
            t = f.input_type or f.kind
            req = " (required)" if f.required else ""
            lines.append(f"{i}. {label} — {t}{req}")
            if f.options:
                for opt in f.options[:30]:
                    lines.append(f"   - {opt.get('label')}")
                if len(f.options) > 30:
                    lines.append("   - ...")
        self.questions_text.delete("1.0", "end")
        self.questions_text.insert("end", "\n".join(lines) if lines else "(No form fields detected)")
        self._set_status(f"Extracted {len(fields)} fields.")

    def on_suggest(self) -> None:
        questions = self.questions_text.get("1.0", "end").strip()
        if not questions or questions.startswith("Loading"):
            self._set_status("No extracted questions to suggest answers for.")
            return

        model = self.ollama_model_var.get().strip() or "llama3"
        profile_json = self.profile_editor.get("1.0", "end").strip() or "{}"

        if not ollama_available():
            self.suggestions_text.delete("1.0", "end")
            self.suggestions_text.insert(
                "end",
                "Ollama not detected at http://localhost:11434.\n"
                "Start Ollama and try again, or fill answers manually.\n",
            )
            self._set_status("Ollama not available.")
            return

        self._set_status("Generating suggestions (no submission)...")

        def worker() -> None:
            try:
                out = suggest_answers_with_ollama(
                    model=model,
                    questions_text=questions,
                    profile_json=profile_json,
                )
                self.root.after(0, lambda: self._set_suggestions(out))
            except Exception as exc:
                self.root.after(0, lambda: self._set_status(f"Suggest failed: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _set_suggestions(self, text: str) -> None:
        self.suggestions_text.delete("1.0", "end")
        self.suggestions_text.insert("end", text or "(Empty response)")
        self._set_status("Suggestions ready. Review and submit manually in your browser.")


def main() -> None:
    root = tk.Tk()
    app = SurveyHelperGUI(root)
    app._set_status(
        "Ready. This tool extracts questions and suggests answers; it does not submit surveys."
    )
    root.mainloop()


if __name__ == "__main__":
    main()

