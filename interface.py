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
    from translator import translate_pdf, LANGUAGES
except ImportError:
    print("Error: translator.py not found in the same folder.")
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
        self.resizable(False, False)
        self.configure(bg=BG)

        w, h = 600, 680
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        self._pdf_path = tk.StringVar()
        self._output_path = tk.StringVar()
        self._api_key = tk.StringVar()
        self._target_lang = tk.StringVar(value="Portuguese")
        self._progress = tk.DoubleVar(value=0)
        self._status_text = tk.StringVar(value="")
        self._translating = False

        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=ACCENT, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="📄 PDF Translator",
                 font=FONT_TITLE, bg=ACCENT, fg="white").pack(side="left", padx=24, pady=16)
        tk.Label(header, text="Powered by Groq + Llama",
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

        progress_frame = tk.Frame(body, bg=BG)
        progress_frame.pack(fill="x", pady=(14, 0))

        self._progressbar = ttk.Progressbar(
            progress_frame, variable=self._progress,
            maximum=100, mode="determinate",
        )
        self._progressbar.pack(fill="x")

        self._lbl_status = tk.Label(
            progress_frame, textvariable=self._status_text,
            font=FONT_SMALL, bg=BG, fg=TEXT_MED,
        )
        self._lbl_status.pack(anchor="w", pady=(4, 0))

        tk.Label(self,
                 text="Tip: save your key as the GROQ_API_KEY environment variable to avoid typing it every time.",
                 font=("Segoe UI", 8), bg=BG, fg=TEXT_LIGHT,
                 wraplength=560).pack(pady=(0, 10))

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
        lang_row = tk.Frame(parent, bg=CARD_BG)
        lang_row.pack(fill="x", pady=(0, 10))
        tk.Label(lang_row, text="Translate to:",
                 font=FONT_NORMAL, bg=CARD_BG, fg=TEXT_MED).pack(side="left")
        combo = ttk.Combobox(lang_row, textvariable=self._target_lang,
                             values=list(LANGUAGES.keys()), state="readonly",
                             font=FONT_NORMAL, width=18)
        combo.pack(side="left", padx=(10, 0))

        tk.Label(parent, text="Groq API Key:",
                 font=FONT_NORMAL, bg=CARD_BG, fg=TEXT_MED).pack(anchor="w")
        api_row = tk.Frame(parent, bg=CARD_BG)
        api_row.pack(fill="x", pady=(4, 0))

        env_key = os.environ.get("GROQ_API_KEY", "")
        if env_key:
            self._api_key.set(env_key)

        self._api_entry = tk.Entry(api_row, textvariable=self._api_key,
                                   font=FONT_NORMAL, fg=TEXT_DARK, bg="#F0F1F7",
                                   relief="flat", bd=0, show="•")
        self._api_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self._style_entry(self._api_entry)
        tk.Button(api_row, text="👁",
                  font=FONT_SMALL, bg="#F0F1F7", fg=TEXT_MED,
                  relief="flat", bd=0, cursor="hand2",
                  command=self._toggle_api_visibility).pack(side="right")
        tk.Label(parent, text="Get your free API key at: console.groq.com",
                 font=FONT_SMALL, bg=CARD_BG, fg=TEXT_LIGHT).pack(anchor="w", pady=(6, 0))

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
        if not self._api_key.get().strip():
            messagebox.showwarning("Warning", "Please enter your Groq API key.")
            return
        if not self._output_path.get():
            base, _ = os.path.splitext(self._pdf_path.get())
            lang = self._target_lang.get().lower()
            self._output_path.set(f"{base}_translated_{lang}.pdf")

        self._translating = True
        self._btn_translate.configure(state="disabled", text="⏳  Translating...")
        self._progress.set(0)
        threading.Thread(target=self._run_translation, daemon=True).start()

    def _run_translation(self):
        try:
            def on_progress(current, total, msg):
                pct = (current / total * 100) if total > 0 else 0
                self.after(0, lambda: self._progress.set(pct))
                self.after(0, lambda: self._status_text.set(msg))

            translate_pdf(
                input_path=self._pdf_path.get(),
                output_path=self._output_path.get(),
                target_lang_display=self._target_lang.get(),
                api_key=self._api_key.get().strip(),
                progress_callback=on_progress,
            )
            self.after(0, self._on_success)
        except Exception as e:
            self.after(0, lambda err=str(e): self._on_error(err))

    def _on_success(self):
        self._translating = False
        self._btn_translate.configure(state="normal", text="🚀  Translate PDF")
        self._progress.set(100)
        self._status_text.set("✅ PDF translated successfully!")
        self._lbl_status.configure(fg=SUCCESS)
        out = self._output_path.get()
        if messagebox.askyesno("Done!", f"Translated PDF saved at:\n{out}\n\nDo you want to open the file?"):
            self._open_file(out)

    def _on_error(self, error_msg):
        self._translating = False
        self._btn_translate.configure(state="normal", text="🚀  Translate PDF")
        self._status_text.set(f"❌ Error: {error_msg}")
        self._lbl_status.configure(fg=ERROR_COLOR)
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