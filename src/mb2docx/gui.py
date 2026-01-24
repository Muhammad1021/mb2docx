"""Tkinter GUI for mb2docx."""
from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from . import __version__
from .config import (
    CV_STYLE,
    CL_STYLE,
    OutputConfig,
    default_output_dir,
    load_saved_author,
    save_author,
    save_output_dir,
)
from .logging_utils import configure_logging
from .pipeline import generate_documents

log = logging.getLogger(__name__)


class App(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=10)
        self.master = master
        self.master.title(f"Markdown Box → DOCX (CV/CL) v{__version__}")
        self.master.minsize(1000, 700)

        # Load saved author name or use empty default
        saved_author = load_saved_author()
        self.author_name = tk.StringVar(value=saved_author)

        self.out_dir = tk.StringVar(value=str(default_output_dir()))

        self.generate_combined = tk.BooleanVar(value=False)
        self.only_combined = tk.BooleanVar(value=False)

        self.cv_text: tk.Text
        self.cl_text: tk.Text

        self.pack(fill="both", expand=True)
        self._build_ui()

    def _build_ui(self) -> None:
        # Author row
        author_row = ttk.Frame(self)
        author_row.pack(fill="x", pady=(0, 5))
        ttk.Label(author_row, text="Author name:").pack(side="left")
        author_entry = ttk.Entry(author_row, textvariable=self.author_name, width=30)
        author_entry.pack(side="left", padx=8)
        # Save author on change
        self.author_name.trace_add("write", self._on_author_change)

        # Output row
        out_row = ttk.Frame(self)
        out_row.pack(fill="x", pady=(0, 10))
        ttk.Label(out_row, text="Output folder:").pack(side="left")
        ttk.Entry(out_row, textvariable=self.out_dir).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(out_row, text="Browse…", command=self._browse_out_dir).pack(side="left")

        # Options row
        opt = ttk.Frame(self)
        opt.pack(fill="x", pady=(0, 10))
        ttk.Checkbutton(
            opt, text="Also generate combined CV+CL docx (default OFF)", variable=self.generate_combined
        ).pack(side="left")
        ttk.Checkbutton(
            opt, text="Only combined (skip separate files)", variable=self.only_combined
        ).pack(side="left", padx=(15, 0))


        # Two panes
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)

        cv_frame = ttk.Labelframe(paned, text="CV (paste markdown-box content here)")
        cl_frame = ttk.Labelframe(paned, text="Cover Letter (optional)")

        paned.add(cv_frame, weight=1)
        paned.add(cl_frame, weight=1)

        self.cv_text = self._build_text_panel(cv_frame, load_cb=self._load_cv_file)
        self.cl_text = self._build_text_panel(cl_frame, load_cb=self._load_cl_file)

        # Actions
        act = ttk.Frame(self)
        act.pack(fill="x", pady=(10, 0))

        ttk.Button(act, text="Generate DOCX", command=self._generate).pack(side="right")
        ttk.Button(act, text="Clear All", command=self._clear_all).pack(side="right", padx=(0, 10))

    def _build_text_panel(self, parent: ttk.Labelframe, *, load_cb) -> tk.Text:
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x", padx=8, pady=(8, 0))

        ttk.Button(toolbar, text="Load .txt/.md…", command=load_cb).pack(side="left")
        ttk.Button(toolbar, text="Load .docx…", command=lambda: self._load_docx_file(parent)).pack(side="left", padx=(4, 0))

        body = ttk.Frame(parent)
        body.pack(fill="both", expand=True, padx=8, pady=8)

        text = tk.Text(body, wrap="word", font=("Consolas", 10))
        yscroll = ttk.Scrollbar(body, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=yscroll.set)

        text.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        # Add right-click context menu
        self._create_context_menu(text)

        ttk.Button(toolbar, text="Clear", command=lambda: self._clear(text)).pack(side="left", padx=(8, 0))

        # Store reference to text widget in parent for docx loading
        parent._text_widget = text
        return text

    def _create_context_menu(self, text_widget: tk.Text) -> None:
        """Add right-click copy/paste/select-all menu."""
        menu = tk.Menu(text_widget, tearoff=0)
        menu.add_command(label="Cut", command=lambda: text_widget.event_generate("<<Cut>>"))
        menu.add_command(label="Copy", command=lambda: text_widget.event_generate("<<Copy>>"))
        menu.add_command(label="Paste", command=lambda: text_widget.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Select All", command=lambda: self._select_all(text_widget))

        def show_menu(event):
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        text_widget.bind("<Button-3>", show_menu)  # Windows/Linux right-click

    def _select_all(self, text_widget: tk.Text) -> None:
        """Select all text in widget."""
        text_widget.tag_add("sel", "1.0", "end")
        text_widget.mark_set("insert", "1.0")
        text_widget.see("insert")

    def _on_author_change(self, *args) -> None:
        """Save author name when changed."""
        author = self.author_name.get().strip()
        if author:
            save_author(author)

    def _clear(self, widget: tk.Text) -> None:
        widget.delete("1.0", tk.END)

    def _clear_all(self) -> None:
        self._clear(self.cv_text)
        self._clear(self.cl_text)

    def _browse_out_dir(self) -> None:
        chosen = filedialog.askdirectory(initialdir=self.out_dir.get() or str(Path.home()))
        if chosen:
            self.out_dir.set(chosen)
            save_output_dir(chosen)

    def _load_text_from_dialog(self) -> Optional[str]:
        path_str = filedialog.askopenfilename(
            title="Choose a text/markdown file",
            filetypes=[("Text/Markdown", "*.txt *.md"), ("All files", "*")],
        )
        if not path_str:
            return None
        return Path(path_str).read_text(encoding="utf-8", errors="replace")

    def _load_docx_from_dialog(self) -> Optional[str]:
        """Load text from a .docx file."""
        path_str = filedialog.askopenfilename(
            title="Choose a Word document",
            filetypes=[("Word Documents", "*.docx"), ("All files", "*")],
        )
        if not path_str:
            return None

        try:
            from docx import Document
            doc = Document(path_str)
            paragraphs = []
            for p in doc.paragraphs:
                text = p.text.strip()
                if text:
                    paragraphs.append(text)
            return "\n\n".join(paragraphs)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read .docx file:\n{e}")
            return None

    def _load_cv_file(self) -> None:
        txt = self._load_text_from_dialog()
        if txt is not None:
            self._clear(self.cv_text)
            self.cv_text.insert("1.0", txt)

    def _load_cl_file(self) -> None:
        txt = self._load_text_from_dialog()
        if txt is not None:
            self._clear(self.cl_text)
            self.cl_text.insert("1.0", txt)

    def _load_docx_file(self, parent: ttk.Labelframe) -> None:
        """Load .docx file into the appropriate text widget."""
        txt = self._load_docx_from_dialog()
        if txt is not None:
            text_widget = getattr(parent, '_text_widget', None)
            if text_widget:
                self._clear(text_widget)
                text_widget.insert("1.0", txt)

    def _generate(self) -> None:
        out_dir = Path(self.out_dir.get()).expanduser().resolve()
        configure_logging(out_dir / "logs", verbose=False)

        cv_text = self.cv_text.get("1.0", tk.END)
        cl_text = self.cl_text.get("1.0", tk.END)

        if not cv_text.strip():
            messagebox.showerror("Error", "CV text is empty!")
            return

        try:
            author = self.author_name.get().strip() or "Author"

            # Save author for next session
            if author and author != "Author":
                save_author(author)

            # Update filenames based on author
            author_filename = author.replace(" ", "_")
            output = OutputConfig(
                out_dir=out_dir,
                author_name=author,
                cv_filename=f"CV_{author_filename}.docx",
                cl_filename=f"CoverLetter_{author_filename}.docx",
                combined_filename=f"CV_and_CoverLetter_{author_filename}.docx",
            )

            paths = generate_documents(
                cv_text=cv_text,
                cl_text=cl_text,
                output=output,
                cv_style=CV_STYLE,
                cl_style=CL_STYLE,
                also_generate_combined=bool(self.generate_combined.get()),
                only_combined=bool(self.only_combined.get()),
            )
        except Exception as e:
            log.exception("Generation failed")
            messagebox.showerror("Error", str(e))
            return

        msg = "Generated:\n" + "\n".join(str(p) for p in paths)
        messagebox.showinfo("Success", msg)


def main() -> None:
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
