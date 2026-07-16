# -*- coding: utf-8 -*-
"""
interface.py — PDF Translator GUI
Run: python interface.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import subprocess

try:
    from core.pipeline import translate_pdf
    from config.settings import LANGUAGES, PROVIDERS
except ImportError:
    print("Error: project structure not found. Make sure you are in the correct folder.")
    sys.exit(1)


BG          = "#F7F8FA"
CARD_BG     = "#FFFFFF"
ACCENT      = "#4F6EF7"
ACCENT_DARK = "#3A55D4"
TEXT_DARK   = "#1A1A2E"
TEXT_MED    = "#555577"
TEXT_LIGHT  = "#999AAA"
SUCCESS     = "#27AE60"
ERROR_COLOR = "#E74C3C"
BORDER      = "#E0E2EE"

FONT_TITLE  = ("Segoe UI", 20, "bold")
FONT_LABEL  = ("Segoe UI", 10, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)
FONT_BTN    = ("Segoe UI", 11, "bold")


class PDFTranslatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Translator")
        self.configure(bg=BG)

        self._win_w, self._win_h = 620, 860

        self._pdf_path    = tk.StringVar()
        self._output_path = tk.StringVar()
        self._api_key     = tk.StringVar()
        self._target_lang = tk.StringVar(value="Portuguese")
        self._provider    = tk.StringVar(value="Groq")
        self._model       = tk.StringVar(value=PROVIDERS["Groq"]["models"][0])
        self._progress      = tk.DoubleVar(value=0)
        self._status_text   = tk.StringVar(value="")
        self._status_detail = tk.StringVar(value="")
        self._start_time    = None
        self._translating   = False
        self._timer_running = False
        self._elapsed_secs  = 0

        self._build_ui()
        self._center_window()

    def _center_window(self):
        """Aplica geometria após construir a UI.

        Necessário no macOS/Tk 9.0, onde definir a geometria antes dos
        widgets às vezes resulta em uma janela minúscula ou cortada.
        """
        self.update_idletasks()
        w, h = self._win_w, self._win_h
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        # Não deixa a janela maior que a tela disponível
        h = min(h, sh - 80)
        x = max((sw - w) // 2, 0)
        y = max((sh - h) // 2, 0)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(480, 600)
        self.lift()
        self.attributes("-topmost", True)
        self.after(300, lambda: self.attributes("-topmost", False))

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=ACCENT, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="📄 PDF Translator",
                 font=FONT_TITLE, bg=ACCENT, fg="white").pack(side="left", padx=24, pady=16)
        tk.Label(header, text="Multi-provider AI Translation",
                 font=FONT_SMALL, bg=ACCENT, fg="#C5CEFF").pack(side="right", padx=24)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=20)

        self._card(body, "1. Select the PDF to translate", self._build_pdf_section)
        self._card(body, "2. Where to save the translated PDF", self._build_output_section)
        self._card(body, "3. Translation settings", self._build_config_section)

        self._btn_translate = tk.Button(
            body, text="🚀  Translate PDF",
            font=FONT_BTN, bg=ACCENT, fg="white",
            activebackground=ACCENT_DARK, activeforeground="white",
            relief="flat", cursor="hand2", bd=0,
            pady=12, command=self._start_translation,
        )
        self._btn_translate.pack(fill="x", pady=(8, 0))

        progress_frame = tk.Frame(body, bg=CARD_BG, bd=1, relief="flat",
                                   highlightbackground=BORDER, highlightthickness=1)
        progress_frame.pack(fill="x", pady=(14, 0))

        # ── Cabeçalho do painel ──
        header_row = tk.Frame(progress_frame, bg=CARD_BG)
        header_row.pack(fill="x", padx=14, pady=(10, 4))

        self._lbl_status = tk.Label(
            header_row, textvariable=self._status_text,
            font=("Segoe UI", 10, "bold"), bg=CARD_BG, fg=TEXT_DARK, anchor="w",
        )
        self._lbl_status.pack(side="left", fill="x", expand=True)

        self._lbl_timer = tk.Label(
            header_row, text="",
            font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MED,
        )
        self._lbl_timer.pack(side="right")

        # ── Barra de progresso maior ──
        bar_frame = tk.Frame(progress_frame, bg=CARD_BG)
        bar_frame.pack(fill="x", padx=14, pady=(0, 4))

        self._progressbar = ttk.Progressbar(
            bar_frame, variable=self._progress,
            maximum=100, mode="determinate",
        )
        self._progressbar.pack(fill="x", ipady=4)

        # ── Linha de métricas: provider · model · blocos · páginas ──
        self._lbl_detail = tk.Label(
            progress_frame, textvariable=self._status_detail,
            font=("Segoe UI", 8), bg=CARD_BG, fg=TEXT_LIGHT, anchor="w",
        )
        self._lbl_detail.pack(fill="x", padx=14, pady=(0, 6))

        # ── Log rolável — eventos reais do pipeline (independente do heartbeat) ──
        log_frame = tk.Frame(progress_frame, bg="#F0F1F7")
        log_frame.pack(fill="x", padx=14, pady=(0, 12))

        log_header = tk.Frame(log_frame, bg="#F0F1F7")
        log_header.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(log_header, text="PIPELINE LOG", font=("Segoe UI", 7, "bold"),
                 bg="#F0F1F7", fg=TEXT_LIGHT).pack(side="left")
        self._lbl_log_count = tk.Label(log_header, text="",
                 font=("Segoe UI", 7), bg="#F0F1F7", fg=TEXT_LIGHT)
        self._lbl_log_count.pack(side="right")

        self._log_text = tk.Text(
            log_frame, height=10, font=("Consolas", 8),
            bg="#F0F1F7", fg=TEXT_DARK, relief="flat",
            state="disabled", wrap="word", bd=0,
            cursor="arrow",
        )
        self._log_text.pack(fill="x", padx=8, pady=(0, 6))

        # Tags de cor
        self._log_text.tag_configure("ok",      foreground=SUCCESS)
        self._log_text.tag_configure("warn",    foreground="#E67E22")
        self._log_text.tag_configure("info",    foreground=ACCENT)
        self._log_text.tag_configure("default", foreground=TEXT_DARK)
        self._log_text.tag_configure("sep",     foreground=TEXT_LIGHT)

        self._log_line_count = 0

    def _card(self, parent, title, build_fn):
        frame = tk.Frame(parent, bg=CARD_BG, bd=1, relief="flat",
                         highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="x", pady=(0, 12))
        tk.Label(frame, text=title, font=FONT_LABEL,
                 bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=16, pady=(12, 4))
        inner = tk.Frame(frame, bg=CARD_BG)
        inner.pack(fill="x", padx=16, pady=(0, 14))
        build_fn(inner)

    def _build_pdf_section(self, parent):
        row = tk.Frame(parent, bg=CARD_BG)
        row.pack(fill="x")
        entry = tk.Entry(row, textvariable=self._pdf_path,
                         font=FONT_NORMAL, fg=TEXT_DARK, bg="#F0F1F7",
                         relief="flat", bd=0, state="readonly")
        entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self._style_entry(entry)
        tk.Button(row, text="Choose file",
                  font=FONT_SMALL, bg=ACCENT, fg="white",
                  activebackground=ACCENT_DARK, activeforeground="white",
                  relief="flat", bd=0, cursor="hand2", padx=12, pady=6,
                  command=self._choose_pdf).pack(side="right")
        self._lbl_pdf_info = tk.Label(parent, text="No file selected.",
                                      font=FONT_SMALL, bg=CARD_BG, fg=TEXT_LIGHT)
        self._lbl_pdf_info.pack(anchor="w", pady=(6, 0))

    def _build_output_section(self, parent):
        row = tk.Frame(parent, bg=CARD_BG)
        row.pack(fill="x")
        entry = tk.Entry(row, textvariable=self._output_path,
                         font=FONT_NORMAL, fg=TEXT_DARK, bg="#F0F1F7",
                         relief="flat", bd=0, state="readonly")
        entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self._style_entry(entry)
        tk.Button(row, text="Choose destination",
                  font=FONT_SMALL, bg=ACCENT, fg="white",
                  activebackground=ACCENT_DARK, activeforeground="white",
                  relief="flat", bd=0, cursor="hand2", padx=12, pady=6,
                  command=self._choose_output).pack(side="right")
        tk.Label(parent, text="If not chosen, the file will be saved in the same folder as the original PDF.",
                 font=FONT_SMALL, bg=CARD_BG, fg=TEXT_LIGHT).pack(anchor="w", pady=(6, 0))

    def _build_config_section(self, parent):
        # Linha 1: idioma + provider
        row1 = tk.Frame(parent, bg=CARD_BG)
        row1.pack(fill="x", pady=(0, 10))

        tk.Label(row1, text="Translate to:",
                 font=FONT_NORMAL, bg=CARD_BG, fg=TEXT_MED).pack(side="left")
        ttk.Combobox(row1, textvariable=self._target_lang,
                     values=list(LANGUAGES.keys()), state="readonly",
                     font=FONT_NORMAL, width=14).pack(side="left", padx=(8, 20))

        tk.Label(row1, text="AI Provider:",
                 font=FONT_NORMAL, bg=CARD_BG, fg=TEXT_MED).pack(side="left")
        provider_combo = ttk.Combobox(
            row1, textvariable=self._provider,
            values=list(PROVIDERS.keys()), state="readonly",
            font=FONT_NORMAL, width=14,
        )
        provider_combo.pack(side="left", padx=(8, 0))
        provider_combo.bind("<<ComboboxSelected>>", self._on_provider_change)
        provider_combo.bind("<<ComboboxSelected>>", self._warn_unstable_provider, add="+")

        # Linha 2: modelo
        row2 = tk.Frame(parent, bg=CARD_BG)
        row2.pack(fill="x", pady=(0, 10))

        tk.Label(row2, text="Model:",
                 font=FONT_NORMAL, bg=CARD_BG, fg=TEXT_MED).pack(side="left")
        self._model_combo = ttk.Combobox(
            row2, textvariable=self._model,
            values=PROVIDERS["Groq"]["models"], state="readonly",
            font=FONT_NORMAL, width=38,
        )
        self._model_combo.pack(side="left", padx=(8, 0))

        # Linha 3: API Key (some para Ollama)
        self._api_frame = tk.Frame(parent, bg=CARD_BG)
        self._api_frame.pack(fill="x")

        tk.Label(self._api_frame, text="API Key:",
                 font=FONT_NORMAL, bg=CARD_BG, fg=TEXT_MED).pack(anchor="w")

        api_row = tk.Frame(self._api_frame, bg=CARD_BG)
        api_row.pack(fill="x", pady=(4, 0))

        self._api_entry = tk.Entry(api_row, textvariable=self._api_key,
                                   font=FONT_NORMAL, fg=TEXT_DARK, bg="#F0F1F7",
                                   relief="flat", bd=0, show="•")
        self._api_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self._style_entry(self._api_entry)
        tk.Button(api_row, text="👁",
                  font=FONT_SMALL, bg="#F0F1F7", fg=TEXT_MED,
                  relief="flat", bd=0, cursor="hand2",
                  command=self._toggle_api_visibility).pack(side="right")

        self._lbl_api_hint = tk.Label(self._api_frame, text="",
                                      font=FONT_SMALL, bg=CARD_BG, fg=TEXT_LIGHT)
        self._lbl_api_hint.pack(anchor="w", pady=(4, 0))

        # Carrega env key e atualiza hint
        self._on_provider_change()

    # ── Eventos ──

    def _warn_unstable_provider(self, event=None):
        provider = self._provider.get()
        if "Gemini" in provider:
            messagebox.showwarning(
                "Gemini — Compatibility Notice",
                "Gemini may not work in all regions.\n"
                "If translation fails, try Groq or Ollama instead."
            )
        elif "OpenRouter" in provider:
            messagebox.showwarning(
                "OpenRouter — Availability Notice",
                "Free models on OpenRouter change frequently and may be unavailable.\n"
                "If translation fails, switch to another model or use Groq instead."
            )

    def _on_provider_change(self, event=None):
        provider = self._provider.get()
        info = PROVIDERS[provider]

        # Atualiza modelos
        models = info["models"]
        self._model_combo["values"] = models
        self._model.set(models[0])

        # Mostra/esconde API Key
        if info["needs_key"]:
            self._api_frame.pack(fill="x")
            # Tenta carregar do ambiente
            env_map = {
                "Groq": "GROQ_API_KEY",
                "Gemini (alfa)(not recommended)": "GEMINI_API_KEY",
                "OpenRouter (alfa)(not recommended)": "OPENROUTER_API_KEY",
            }
            env_key = os.environ.get(env_map.get(provider, ""), "")
            if env_key:
                self._api_key.set(env_key)

            hints = {
                "Groq":       "Get your free key at: console.groq.com",
                "Gemini (alfa)(not recommended)":     "Get your free key at: aistudio.google.com/app/apikey",
                "OpenRouter (alfa)(not recommended)": "Get your free key at: openrouter.ai/keys",
            }
            self._lbl_api_hint.configure(text=hints.get(provider, ""))
        else:
            self._api_frame.pack_forget()

    def _style_entry(self, entry):
        entry.configure(highlightthickness=1,
                        highlightbackground=BORDER,
                        highlightcolor=ACCENT)

    def _toggle_api_visibility(self):
        current = self._api_entry.cget("show")
        self._api_entry.configure(show="" if current == "•" else "•")

    def _choose_pdf(self):
        path = filedialog.askopenfilename(
            title="Select the PDF",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not path:
            return
        self._pdf_path.set(path)
        size_kb = os.path.getsize(path) / 1024
        self._lbl_pdf_info.configure(
            text=f"✓ {os.path.basename(path)} ({size_kb:.1f} KB)", fg=SUCCESS)
        if not self._output_path.get():
            base, _ = os.path.splitext(path)
            lang = self._target_lang.get().lower()
            self._output_path.set(f"{base}_translated_{lang}.pdf")

    def _choose_output(self):
        lang = self._target_lang.get().lower()
        path = filedialog.asksaveasfilename(
            title="Save translated PDF as...",
            defaultextension=".pdf",
            initialfile=f"translated_{lang}.pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if path:
            self._output_path.set(path)

    def _start_translation(self):
        if self._translating:
            return
        if not self._pdf_path.get():
            messagebox.showwarning("Warning", "Please select a PDF file first.")
            return
        provider = self._provider.get()
        if PROVIDERS[provider]["needs_key"] and not self._api_key.get().strip():
            messagebox.showwarning("Warning", f"Please enter your {provider} API key.")
            return
        if not self._output_path.get():
            base, _ = os.path.splitext(self._pdf_path.get())
            lang = self._target_lang.get().lower()
            self._output_path.set(f"{base}_translated_{lang}.pdf")

        self._translating = True
        self._elapsed_secs = 0
        self._timer_running = True
        self._lbl_timer.configure(text="⏱  00:00")
        self._tick_timer()
        self._btn_translate.configure(state="disabled", text="⏳  Translating...")
        self._progress.set(0)
        self._status_text.set("Starting translation...")
        self._status_detail.set(f"Provider: {self._provider.get()}  ·  Model: {self._model.get()}")
        self._lbl_detail.configure(fg=TEXT_LIGHT)
        threading.Thread(target=self._run_translation, daemon=True).start()

    def _tick_timer(self):
        """Atualiza o timer a cada segundo, independente da tradução."""
        if self._timer_running:
            self._elapsed_secs += 1
            mins, secs = divmod(self._elapsed_secs, 60)
            self._lbl_timer.configure(text=f"⏱  {mins:02d}:{secs:02d}")
            self.after(1000, self._tick_timer)

    def _log(self, msg: str, tag: str = "default"):
        """Escreve uma linha no pipeline log com timestamp."""
        import time as _time
        elapsed = int(_time.time() - self._start_time) if self._start_time else 0
        mins, secs = divmod(elapsed, 60)
        timestamp = f"[{mins:02d}:{secs:02d}]"

        def _write():
            self._log_line_count += 1
            self._log_text.configure(state="normal")
            self._log_text.insert("end", f"{timestamp} {msg}\n", tag)
            self._log_text.see("end")
            self._log_text.configure(state="disabled")
            self._lbl_log_count.configure(text=f"{self._log_line_count} events")

        self.after(0, _write)

    def _run_translation(self):
        import time
        self._start_time = time.time()
        self._log_line_count = 0

        # Limpa o log ao iniciar nova tradução
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")
        self._lbl_log_count.configure(text="")

        try:
            def on_progress(current, total, msg):
                """Atualiza barra + status + heartbeat. NÃO escreve no log."""
                import time as _t
                pct = (current / total * 100) if total > 0 else 0
                elapsed = int(_t.time() - self._start_time)
                mins, secs = divmod(elapsed, 60)
                time_str = f"{mins:02d}:{secs:02d}"
                provider = self._provider.get()
                model    = self._model.get()
                blocks_info = f"{current}/{total} blocks" if total > 1 else ""
                detail = f"{provider}  ·  {model}  ·  {blocks_info}  ·  {time_str} elapsed"

                self.after(0, lambda: self._progress.set(pct))
                self.after(0, lambda m=msg: self._status_text.set(m))
                self.after(0, lambda d=detail: self._status_detail.set(d))

            def on_log(msg, tag="info"):
                """Escreve eventos reais do pipeline no log. Independente do heartbeat."""
                self._log(msg, tag)

            translate_pdf(
                input_path=self._pdf_path.get(),
                output_path=self._output_path.get(),
                target_lang_display=self._target_lang.get(),
                provider=self._provider.get(),
                model=self._model.get(),
                api_key=self._api_key.get().strip(),
                progress_callback=on_progress,
                log_callback=on_log,
            )
            self.after(0, self._on_success)
        except Exception as e:
            self.after(0, lambda err=str(e): self._on_error(err))

    def _on_success(self):
        self._translating = False
        self._timer_running = False
        self._btn_translate.configure(state="normal", text="🚀  Translate PDF")
        self._progress.set(100)
        import time
        elapsed = int(time.time() - self._start_time) if self._start_time else 0
        mins, secs = divmod(elapsed, 60)
        self._status_text.set("✅ PDF translated successfully!")
        self._status_detail.set(f"Completed in {mins:02d}:{secs:02d}  ·  {self._provider.get()}  ·  {self._model.get()}")
        self._lbl_status.configure(fg=SUCCESS)
        self._lbl_detail.configure(fg=SUCCESS)
        out = self._output_path.get()
        if messagebox.askyesno("Done!", f"Translated PDF saved at:\n{out}\n\nDo you want to open the file?"):
            self._open_file(out)

    def _on_error(self, error_msg):
        self._translating = False
        self._timer_running = False
        self._btn_translate.configure(state="normal", text="🚀  Translate PDF")
        self._status_text.set("❌ Translation failed.")
        self._status_detail.set(error_msg[:80] + ("..." if len(error_msg) > 80 else ""))
        self._lbl_status.configure(fg=ERROR_COLOR)
        self._lbl_detail.configure(fg=ERROR_COLOR)
        messagebox.showerror("Translation error", error_msg)

    def _open_file(self, path):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except Exception:
            pass


def main():
    app = PDFTranslatorApp()
    style = ttk.Style(app)
    style.theme_use("clam")
    style.configure("TCombobox", fieldbackground="#F0F1F7", background="#F0F1F7",
                    relief="flat", borderwidth=0)
    style.configure("Horizontal.TProgressbar",
                    troughcolor="#E0E2EE", background="#4F6EF7",
                    thickness=8, borderwidth=0)
    app.mainloop()


if __name__ == "__main__":
    main()