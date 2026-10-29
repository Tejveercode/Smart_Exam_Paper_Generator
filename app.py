"""
Smart Exam Paper Generator
A beginner-friendly Tkinter application for Linux.

Supported input: text-based PDF, DOCX and TXT files.
Dependencies: PyMuPDF, python-docx, ReportLab
"""

import os
import random
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path

try:
    import fitz  # PyMuPDF
    from docx import Document
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    )
except ImportError as error:
    fitz = None
    Document = None
    IMPORT_ERROR = str(error)


APP_TITLE = "Smart Exam Paper Generator"
MARK_HEADINGS = {
    2: ("2 MARK QUESTIONS", "2 MARK QUESTION", "2-MARK QUESTIONS",
        "2 MARKS QUESTIONS", "TWO MARK QUESTIONS"),
    5: ("5 MARK QUESTIONS", "5 MARK QUESTION", "5-MARK QUESTIONS",
        "5 MARKS QUESTIONS", "FIVE MARK QUESTIONS"),
    10: ("10 MARK QUESTIONS", "10 MARK QUESTION", "10-MARK QUESTIONS",
         "10 MARKS QUESTIONS", "TEN MARK QUESTIONS"),
}


def read_file(file_path):
    """Return readable text from a supported file."""
    suffix = Path(file_path).suffix.lower()

    if suffix == ".txt":
        return Path(file_path).read_text(encoding="utf-8", errors="replace")

    if suffix == ".docx":
        document = Document(file_path)
        return "\n".join(p.text for p in document.paragraphs if p.text.strip())

    if suffix == ".pdf":
        pages = []
        with fitz.open(file_path) as pdf:
            for page in pdf:
                pages.append(page.get_text("text"))
        return "\n".join(pages)

    raise ValueError("Unsupported file type. Use PDF, DOCX or TXT.")


def clean_question(text):
    """Normalize spaces without changing the question's wording."""
    return re.sub(r"\s+", " ", text).strip()


def parse_question_bank(text, source_name):
    """
    Read marks headings and numbered questions.
    Example:
        2 MARK QUESTIONS
        1. Define Python.
        2. What is a variable?
    """
    questions = []
    current_marks = None
    current_question = []
    unclassified = []

    def save_current():
        nonlocal current_question
        if current_question:
            value = clean_question(" ".join(current_question))
            if value:
                target_marks = current_marks
                item = {
                    "text": value,
                    "marks": target_marks,
                    "source": source_name,
                }
                if target_marks in (2, 5, 10):
                    questions.append(item)
                else:
                    unclassified.append(item)
        current_question = []

    lines = text.replace("\r", "\n").splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        upper = re.sub(r"[\s:_-]+", " ", line.upper()).strip()
        detected_marks = None

        for marks, headings in MARK_HEADINGS.items():
            if any(upper == re.sub(r"[\s:_-]+", " ", h).strip()
                   for h in headings):
                detected_marks = marks
                break

        # Also accept headings such as "Section A (2 marks)" or "2 Marks"
        if detected_marks is None:
            heading_match = re.fullmatch(
                r"(?:SECTION\s+[A-Z]\s*[\(:-]?\s*)?"
                r"(2|5|10)\s*[- ]?\s*MARKS?"
                r"(?:\s+QUESTIONS?)?\s*\)?", upper
            )
            if heading_match:
                detected_marks = int(heading_match.group(1))

        if detected_marks is not None:
            save_current()
            current_marks = detected_marks
            continue

        # A numbered question starts a new question; numbered sub-points may
        # also match, so teachers should review the extracted bank.
        if re.match(r"^(?:Q(?:UESTION)?\s*)?\d{1,3}\s*[.)\-:]\s+\S", line, re.I):
            save_current()
            line = re.sub(
                r"^(?:Q(?:UESTION)?\s*)?\d{1,3}\s*[.)\-:]\s*", "", line, flags=re.I
            )
            current_question = [line]
        elif current_question:
            current_question.append(line)
        elif line:
            # Unnumbered text is kept for visibility, but not silently treated
            # as a confidently identified question.
            unclassified.append({
                "text": clean_question(line),
                "marks": None,
                "source": source_name,
            })

    save_current()
    return questions, unclassified


class SmartExamApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1080x760")
        self.root.minsize(850, 620)

        self.bank = []
        self.unclassified = []
        self.selected = []
        self.sections = []

        self._build_ui()
        self._update_status()

    def _build_ui(self):
        header = ttk.Frame(self.root, padding=(14, 12))
        header.pack(fill="x")
        ttk.Label(
            header, text=APP_TITLE,
            font=("TkDefaultFont", 17, "bold")
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Import a question bank, configure the paper, review questions, and export a PDF.",
        ).pack(anchor="w", pady=(3, 0))

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.bank_tab = ttk.Frame(self.tabs, padding=10)
        self.setup_tab = ttk.Frame(self.tabs, padding=10)
        self.review_tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.bank_tab, text="1. Question Bank")
        self.tabs.add(self.setup_tab, text="2. Exam Setup")
        self.tabs.add(self.review_tab, text="3. Review & Export")

        self._build_bank_tab()
        self._build_setup_tab()
        self._build_review_tab()

        self.status = ttk.Label(self.root, text="", relief="sunken", anchor="w", padding=5)
        self.status.pack(fill="x", side="bottom")

    def _build_bank_tab(self):
        bar = ttk.Frame(self.bank_tab)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Button(bar, text="Upload PDF / DOCX / TXT", command=self.upload_files).pack(side="left")
        ttk.Button(bar, text="Add Question Manually", command=self.add_question).pack(side="left", padx=6)
        ttk.Button(bar, text="Remove Selected", command=self.remove_bank_question).pack(side="left")
        ttk.Button(bar, text="Help: Prepare a Bank", command=self.show_help).pack(side="right")

        ttk.Label(
            self.bank_tab,
            text="Marks headings supported: 2 MARK QUESTIONS, 5 MARK QUESTIONS, 10 MARK QUESTIONS. "
                 "Review extracted questions before generating a paper.",
            wraplength=950,
        ).pack(anchor="w", pady=(0, 8))

        columns = ("marks", "question", "source")
        self.bank_tree = ttk.Treeview(self.bank_tab, columns=columns, show="headings", height=18)
        self.bank_tree.heading("marks", text="Marks")
        self.bank_tree.heading("question", text="Question")
        self.bank_tree.heading("source", text="Source")
        self.bank_tree.column("marks", width=70, anchor="center")
        self.bank_tree.column("question", width=650)
        self.bank_tree.column("source", width=180)
        scroll = ttk.Scrollbar(self.bank_tab, orient="vertical", command=self.bank_tree.yview)
        self.bank_tree.configure(yscrollcommand=scroll.set)
        self.bank_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _build_setup_tab(self):
        # Keep the scrollbar outside the canvas so it remains available while
        # the embedded setup form is scrolled.
        container = ttk.Frame(self.setup_tab)
        container.pack(fill="both", expand=True)

        self.setup_canvas = tk.Canvas(container, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=self.setup_canvas.yview
        )
        self.setup_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.setup_canvas.pack(side="left", fill="both", expand=True)

        content = ttk.Frame(self.setup_canvas)
        self.setup_content = content
        window_id = self.setup_canvas.create_window(
            (0, 0), window=content, anchor="nw"
        )

        def update_scroll_region(_event=None):
            self.setup_canvas.configure(
                scrollregion=self.setup_canvas.bbox("all")
            )

        def fit_content_width(event):
            self.setup_canvas.itemconfigure(window_id, width=event.width)

        content.bind("<Configure>", update_scroll_region)
        self.setup_canvas.bind("<Configure>", fit_content_width)

        # Support Windows/macOS wheel events and Linux wheel-button events.
        def on_mousewheel(event):
            if getattr(event, "num", None) == 4:
                self.setup_canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                self.setup_canvas.yview_scroll(1, "units")
            elif getattr(event, "delta", 0):
                delta = -1 if event.delta > 0 else 1
                self.setup_canvas.yview_scroll(delta, "units")

        def enable_wheel(_event=None):
            self.setup_canvas.bind_all("<MouseWheel>", on_mousewheel)
            self.setup_canvas.bind_all("<Button-4>", on_mousewheel)
            self.setup_canvas.bind_all("<Button-5>", on_mousewheel)

        def disable_wheel(_event=None):
            self.setup_canvas.unbind_all("<MouseWheel>")
            self.setup_canvas.unbind_all("<Button-4>")
            self.setup_canvas.unbind_all("<Button-5>")

        self.setup_canvas.bind("<Enter>", enable_wheel)
        self.setup_canvas.bind("<Leave>", disable_wheel)
        content.bind("<Enter>", enable_wheel)
        content.bind("<Leave>", disable_wheel)

        form = ttk.Frame(content)
        form.pack(fill="x")

        self.fields = {}
        field_specs = [
            ("Institute name", "Institute / College Name"),
            ("University name", "University / School Name"),
            ("Academic year", "2026-2027"),
            ("Examination name", "In Semester Test"),
            ("Branch", "Bachelor of Computer Applications"),
            ("Subject code", "Subject code"),
            ("Subject title", "Subject title"),
            ("Semester / Class", "Semester / Class"),
            ("Date", ""),
            ("Duration", "1 Hour"),
            ("Instructions", "Attempt all questions"),
        ]

        for index, (label, default) in enumerate(field_specs):
            row, col = divmod(index, 2)
            cell = ttk.Frame(form, padding=(4, 4))
            cell.grid(row=row, column=col, sticky="ew")
            ttk.Label(cell, text=label).pack(anchor="w")
            if label == "Instructions":
                widget = tk.Text(cell, height=3, width=42, wrap="word")
                widget.insert("1.0", default)
                widget.pack(fill="x", expand=True)
            else:
                widget = ttk.Entry(cell, width=48)
                widget.insert(0, default)
                widget.pack(fill="x", expand=True)
            self.fields[label] = widget

        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        ttk.Separator(content).pack(fill="x", pady=12)
        ttk.Label(
            content, text="Question paper pattern",
            font=("TkDefaultFont", 11, "bold")
        ).pack(anchor="w")
        ttk.Label(
            content,
            text="Set marks per question and how many to select. Questions must exist in the matching marks group.",
            wraplength=900,
        ).pack(anchor="w", pady=(2, 8))

        pattern_frame = ttk.Frame(content)
        pattern_frame.pack(fill="x")
        self.pattern_tree = ttk.Treeview(
            pattern_frame, columns=("section", "marks", "count", "attempt"),
            show="headings", height=5
        )
        for key, title, width in [
            ("section", "Section", 220), ("marks", "Marks per question", 180),
            ("count", "Questions to select", 180), ("attempt", "Questions to attempt", 180)
        ]:
            self.pattern_tree.heading(key, text=title)
            self.pattern_tree.column(key, width=width, anchor="center")
        pattern_scroll = ttk.Scrollbar(
            pattern_frame, orient="vertical", command=self.pattern_tree.yview
        )
        self.pattern_tree.configure(yscrollcommand=pattern_scroll.set)
        self.pattern_tree.pack(side="left", fill="x", expand=True)
        pattern_scroll.pack(side="right", fill="y")
        for row in [
            ("Section A", "2", "5", "5"),
            ("Section B", "5", "2", "2"),
            ("Section C", "10", "0", "0"),
        ]:
            self.pattern_tree.insert("", "end", values=row)

        controls = ttk.Frame(content)
        controls.pack(fill="x", pady=8)
        ttk.Button(
            controls, text="Edit Selected Pattern Row", command=self.edit_pattern
        ).pack(side="left")
        ttk.Button(controls, text="Add Section", command=self.add_section).pack(
            side="left", padx=6
        )
        ttk.Button(controls, text="Remove Section", command=self.remove_section).pack(
            side="left"
        )
        ttk.Button(
            controls, text="Generate Random Paper", command=self.generate_selection
        ).pack(side="right")

        self.total_label = ttk.Label(
            content, text="Calculated maximum marks: 20"
        )
        self.total_label.pack(anchor="w", pady=(6, 12))
        self.pattern_tree.bind(
            "<<TreeviewSelect>>", lambda event: self._calculate_total()
        )
        self._calculate_total()

    def _build_review_tab(self):
        bar = ttk.Frame(self.review_tab)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Button(bar, text="Edit Question", command=self.edit_selected).pack(side="left")
        ttk.Button(bar, text="Replace Question", command=self.replace_selected).pack(side="left", padx=6)
        ttk.Button(bar, text="Remove Question", command=self.remove_selected).pack(side="left")
        ttk.Button(bar, text="Move Up", command=lambda: self.move_selected(-1)).pack(side="left", padx=(16, 3))
        ttk.Button(bar, text="Move Down", command=lambda: self.move_selected(1)).pack(side="left")
        ttk.Button(bar, text="Preview Paper", command=self.preview_paper).pack(side="right")
        ttk.Button(bar, text="Export PDF", command=self.export_pdf).pack(side="right", padx=6)

        columns = ("section", "number", "marks", "question")
        self.review_tree = ttk.Treeview(self.review_tab, columns=columns, show="headings", height=20)
        for key, title, width in [
            ("section", "Section", 120), ("number", "Q. No.", 65),
            ("marks", "Marks", 65), ("question", "Question", 700)
        ]:
            self.review_tree.heading(key, text=title)
            self.review_tree.column(key, width=width, anchor="w" if key == "question" else "center")
        scroll = ttk.Scrollbar(self.review_tab, orient="vertical", command=self.review_tree.yview)
        self.review_tree.configure(yscrollcommand=scroll.set)
        self.review_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _field_value(self, label):
        widget = self.fields[label]
        if isinstance(widget, tk.Text):
            return widget.get("1.0", "end").strip()
        return widget.get().strip()

    def _set_status(self, message):
        self.status.config(text=message)

    def _update_status(self):
        self._set_status(f"Question bank: {len(self.bank)} classified question(s) | "
                         f"Needs review: {len(self.unclassified)} item(s)")

    def upload_files(self):
        paths = filedialog.askopenfilenames(
            title="Choose question bank files",
            filetypes=[
                ("Supported files", "*.pdf *.docx *.txt"),
                ("PDF files", "*.pdf"), ("Word documents", "*.docx"),
                ("Text files", "*.txt"),
            ],
        )
        if not paths:
            return

        added = 0
        problems = []
        for path in paths:
            try:
                text = read_file(path)
                classified, unclassified = parse_question_bank(text, Path(path).name)
                self.bank.extend(classified)
                self.unclassified.extend(unclassified)
                added += len(classified)
                if not classified:
                    problems.append(f"{Path(path).name}: no numbered questions under a recognized marks heading")
            except Exception as error:
                problems.append(f"{Path(path).name}: {error}")

        self._refresh_bank()
        self._update_status()
        message = f"Imported {added} classified question(s)."
        if problems:
            message += "\n\nPlease review these files:\n" + "\n".join(problems)
        if self.unclassified:
            message += f"\n\n{len(self.unclassified)} unclassified item(s) were found. They are not used for random selection."
        messagebox.showinfo("Import result", message)

    def _refresh_bank(self):
        self.bank_tree.delete(*self.bank_tree.get_children())
        for index, item in enumerate(self.bank):
            self.bank_tree.insert("", "end", iid=str(index),
                                  values=(item["marks"], item["text"], item["source"]))

    def add_question(self):
        marks = simpledialog.askinteger("Question marks", "Enter marks (2, 5 or 10):",
                                        parent=self.root, minvalue=1)
        if marks is None:
            return
        text = simpledialog.askstring("Question text", "Enter the complete question:", parent=self.root)
        if not text or not text.strip():
            return
        source = "Added manually"
        self.bank.append({"text": clean_question(text), "marks": marks, "source": source})
        self._refresh_bank()
        self._update_status()

    def remove_bank_question(self):
        selection = self.bank_tree.selection()
        if not selection:
            messagebox.showwarning("Select a question", "Select a question to remove.")
            return
        index = int(selection[0])
        del self.bank[index]
        self._refresh_bank()
        self._update_status()

    def show_help(self):
        help_text = (
            "HOW TO PREPARE A QUESTION BANK\n\n"
            "1. Put a heading before each group, for example:\n"
            "   2 MARK QUESTIONS\n"
            "   5 MARK QUESTIONS\n"
            "   10 MARK QUESTIONS\n\n"
            "2. Number each question on a new line, for example:\n"
            "   1. Define Python.\n"
            "   2. What is a variable?\n\n"
            "3. A question can continue over multiple lines. Start the next question "
            "with a number and full stop, such as '3. '.\n\n"
            "4. Upload PDF, DOCX or TXT. Text-based PDFs work best; scanned PDFs "
            "may need OCR and are not supported reliably in this first version.\n\n"
            "5. Review the extracted question bank. If headings or numbering are "
            "unclear, correct the source file and upload it again.\n\n"
            "6. The app selects randomly without repeating a question within the same paper.\n\n"
            "7. Check the final preview and maximum marks before exporting."
        )
        messagebox.showinfo("Teacher help", help_text)

    def edit_pattern(self):
        selection = self.pattern_tree.selection()
        if not selection:
            messagebox.showwarning("Select a row", "Select a pattern row to edit.")
            return
        item_id = selection[0]
        old = self.pattern_tree.item(item_id, "values")
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit paper pattern")
        dialog.transient(self.root)
        dialog.grab_set()
        variables = []
        for row, (label, value) in enumerate(zip(
            ("Section name", "Marks per question", "Questions to select", "Questions to attempt"), old
        )):
            ttk.Label(dialog, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=5)
            var = tk.StringVar(value=value)
            ttk.Entry(dialog, textvariable=var, width=28).grid(row=row, column=1, padx=10, pady=5)
            variables.append(var)

        def save():
            try:
                marks, count, attempt = int(variables[1].get()), int(variables[2].get()), int(variables[3].get())
                if marks <= 0 or count < 0 or attempt < 0 or attempt > count:
                    raise ValueError
                if not variables[0].get().strip():
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid pattern", "Use a section name, positive marks, and valid non-negative counts. Attempt count cannot exceed selected count.", parent=dialog)
                return
            self.pattern_tree.item(item_id, values=tuple(v.get().strip() for v in variables))
            dialog.destroy()
            self._calculate_total()

        ttk.Button(dialog, text="Save", command=save).grid(row=4, column=0, columnspan=2, pady=10)

    def add_section(self):
        name = simpledialog.askstring("Section name", "Enter section name (e.g. Section D):", parent=self.root)
        if not name:
            return
        self.pattern_tree.insert("", "end", values=(name.strip(), "2", "0", "0"))
        self._calculate_total()

    def remove_section(self):
        selection = self.pattern_tree.selection()
        if not selection:
            messagebox.showwarning("Select a section", "Select a pattern row to remove.")
            return
        for item_id in selection:
            self.pattern_tree.delete(item_id)
        self._calculate_total()

    def _pattern(self):
        result = []
        for item_id in self.pattern_tree.get_children():
            section, marks, count, attempt = self.pattern_tree.item(item_id, "values")
            result.append({
                "section": section,
                "marks": int(marks),
                "count": int(count),
                "attempt": int(attempt),
            })
        return result

    def _calculate_total(self):
        try:
            total = sum(row["marks"] * row["count"] for row in self._pattern())
            self.total_label.config(text=f"Calculated maximum marks: {total}")
        except (ValueError, tk.TclError):
            self.total_label.config(text="Check the pattern values.")

    def generate_selection(self):
        if not self.bank:
            messagebox.showwarning("No question bank", "Upload or add questions first.")
            self.tabs.select(self.bank_tab)
            return
        try:
            pattern = self._pattern()
        except ValueError:
            messagebox.showerror("Invalid pattern", "Please correct the pattern values.")
            return

        chosen = []
        shortages = []
        used_texts = set()
        for section in pattern:
            if section["count"] == 0:
                continue
            candidates = [
                q for q in self.bank
                if q["marks"] == section["marks"] and q["text"].casefold() not in used_texts
            ]
            if len(candidates) < section["count"]:
                shortages.append(
                    f'{section["section"]}: needs {section["count"]} question(s) worth '
                    f'{section["marks"]} mark(s), but only {len(candidates)} available.'
                )
                continue
            picks = random.sample(candidates, section["count"])
            for question in picks:
                item = dict(question)
                item["section"] = section["section"]
                item["attempt"] = section["attempt"]
                chosen.append(item)
                used_texts.add(item["text"].casefold())

        if shortages:
            messagebox.showerror("Not enough questions", "\n".join(shortages) +
                                 "\n\nAdd more questions or reduce the section counts.")
            return

        if not chosen:
            messagebox.showwarning("Empty paper", "Set at least one question in the paper pattern.")
            return

        self.selected = chosen
        self._refresh_review()
        self.tabs.select(self.review_tab)
        self._set_status(f"Generated {len(self.selected)} question(s). Review and edit before exporting.")

    def _refresh_review(self):
        self.review_tree.delete(*self.review_tree.get_children())
        section_numbers = {}
        for index, item in enumerate(self.selected):
            section = item["section"]
            section_numbers[section] = section_numbers.get(section, 0) + 1
            item["number"] = section_numbers[section]
            self.review_tree.insert(
                "", "end", iid=str(index),
                values=(section, item["number"], item["marks"], item["text"])
            )

    def edit_selected(self):
        selection = self.review_tree.selection()
        if not selection:
            messagebox.showwarning("Select a question", "Select a question to edit.")
            return
        index = int(selection[0])
        old = self.selected[index]["text"]
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit question")
        dialog.geometry("620x260")
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(dialog, text=f'Question ({self.selected[index]["marks"]} marks)').pack(anchor="w", padx=10, pady=8)
        editor = tk.Text(dialog, wrap="word", height=7)
        editor.pack(fill="both", expand=True, padx=10)
        editor.insert("1.0", old)

        def save():
            new_text = clean_question(editor.get("1.0", "end"))
            if not new_text:
                messagebox.showwarning("Empty question", "Question text cannot be empty.", parent=dialog)
                return
            self.selected[index]["text"] = new_text
            self._refresh_review()
            dialog.destroy()

        ttk.Button(dialog, text="Save changes", command=save).pack(pady=8)

    def replace_selected(self):
        selection = self.review_tree.selection()
        if not selection:
            messagebox.showwarning("Select a question", "Select a question to replace.")
            return
        index = int(selection[0])
        old_item = self.selected[index]
        used = {q["text"].casefold() for i, q in enumerate(self.selected) if i != index}
        candidates = [
            q for q in self.bank
            if q["marks"] == old_item["marks"] and q["text"].casefold() not in used
        ]
        if not candidates:
            messagebox.showwarning("No replacement", "No unused question with the same marks is available.")
            return
        replacement = dict(random.choice(candidates))
        replacement["section"] = old_item["section"]
        replacement["attempt"] = old_item["attempt"]
        self.selected[index] = replacement
        self._refresh_review()

    def remove_selected(self):
        selection = self.review_tree.selection()
        if not selection:
            messagebox.showwarning("Select a question", "Select a question to remove.")
            return
        del self.selected[int(selection[0])]
        self._refresh_review()

    def move_selected(self, direction):
        selection = self.review_tree.selection()
        if not selection:
            messagebox.showwarning("Select a question", "Select a question to move.")
            return
        index = int(selection[0])
        target = index + direction
        if target < 0 or target >= len(self.selected):
            return
        self.selected[index], self.selected[target] = self.selected[target], self.selected[index]
        self._refresh_review()
        self.review_tree.selection_set(str(target))

    def _build_pdf_story(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="PaperTitle", parent=styles["Title"], fontName="Helvetica-Bold",
            fontSize=14, leading=17, alignment=TA_CENTER, spaceAfter=5
        ))
        styles.add(ParagraphStyle(
            name="PaperSubTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=10, leading=13, alignment=TA_CENTER, spaceAfter=4
        ))
        styles.add(ParagraphStyle(
            name="QuestionText", parent=styles["BodyText"], fontName="Helvetica",
            fontSize=9.5, leading=12, alignment=TA_LEFT
        ))
        styles.add(ParagraphStyle(
            name="SectionHeading", parent=styles["Heading2"], fontName="Helvetica-Bold",
            fontSize=10, leading=13, alignment=TA_CENTER, spaceBefore=7, spaceAfter=5
        ))
        styles.add(ParagraphStyle(
            name="SmallText", parent=styles["BodyText"], fontSize=9, leading=11
        ))

        story = []
        university = self._field_value("University name")
        institute = self._field_value("Institute name")
        if university:
            story.append(Paragraph(university.upper(), styles["PaperTitle"]))
        if institute:
            story.append(Paragraph(institute, styles["PaperSubTitle"]))
        story.append(Spacer(1, 3 * mm))

        name = self._field_value("Examination name")
        year = self._field_value("Academic year")
        if name or year:
            story.append(Paragraph(
                " — ".join(value for value in (name, f"Academic Year {year}" if year else "") if value),
                styles["PaperSubTitle"]
            ))
        story.append(Spacer(1, 3 * mm))

        details = [
            ("Branch", self._field_value("Branch")),
            ("Subject Code", self._field_value("Subject code")),
            ("Subject Title", self._field_value("Subject title")),
            ("Semester / Class", self._field_value("Semester / Class")),
            ("Date", self._field_value("Date")),
        ]
        details = [(label, value) for label, value in details if value]
        if details:
            rows = []
            for label, value in details:
                rows.append([
                    Paragraph(f"<b>{label}:</b>", styles["SmallText"]),
                    Paragraph(value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), styles["SmallText"])
                ])
            details_table = Table(rows, colWidths=[32 * mm, 125 * mm], hAlign="LEFT")
            details_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            story.append(details_table)

        duration = self._field_value("Duration")
        maximum = sum(q["marks"] for q in self.selected)
        summary = Table([[
            Paragraph(f"<b>Time:</b> {duration or '____________'}", styles["SmallText"]),
            Paragraph(f"<b>Maximum Marks:</b> {maximum}", styles["SmallText"]),
        ]], colWidths=[78 * mm, 78 * mm])
        summary.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.extend([summary, Spacer(1, 2 * mm)])

        instructions = self._field_value("Instructions")
        if instructions:
            story.append(Paragraph(f"<b>Instructions:</b> {instructions.replace(chr(10), '<br/>')}", styles["SmallText"]))
            story.append(Spacer(1, 3 * mm))

        pattern = self._pattern()
        for section in pattern:
            questions = [q for q in self.selected if q["section"] == section["section"]]
            if not questions:
                continue
            # Reflect the questions that are actually present after review edits.
            total = sum(question["marks"] for question in questions)
            story.append(Paragraph(
                f'{section["section"]} — {len(questions)} × {section["marks"]} = {total} marks',
                styles["SectionHeading"]
            ))
            if section["attempt"] < len(questions):
                story.append(Paragraph(
                    f'Attempt any {min(section["attempt"], len(questions))} question(s).',
                    styles["SmallText"]
                ))
                story.append(Spacer(1, 2 * mm))

            rows = [[
                Paragraph("<b>Q. No.</b>", styles["SmallText"]),
                Paragraph("<b>Statement</b>", styles["SmallText"]),
                Paragraph("<b>Marks</b>", styles["SmallText"]),
            ]]
            for number, question in enumerate(questions, start=1):
                safe_text = (question["text"].replace("&", "&amp;")
                             .replace("<", "&lt;").replace(">", "&gt;"))
                rows.append([
                    Paragraph(str(number), styles["SmallText"]),
                    Paragraph(safe_text, styles["QuestionText"]),
                    Paragraph(str(question["marks"]), styles["SmallText"]),
                ])
            table = Table(rows, colWidths=[15 * mm, 132 * mm, 15 * mm], repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDEDED")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (-1, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(table)
            story.append(Spacer(1, 3 * mm))
        return story

    def _make_pdf(self, path):
        document = SimpleDocTemplate(
            path, pagesize=A4,
            rightMargin=18 * mm, leftMargin=18 * mm,
            topMargin=15 * mm, bottomMargin=17 * mm,
            title=self._field_value("Subject title") or APP_TITLE,
            author="Smart Exam Paper Generator",
        )

        def add_page_number(canvas, doc):
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.drawCentredString(A4[0] / 2, 8 * mm, f"Page {doc.page}")
            canvas.restoreState()

        document.build(self._build_pdf_story(), onFirstPage=add_page_number, onLaterPages=add_page_number)

    def preview_paper(self):
        """Create a temporary PDF and open it with the operating system's viewer."""
        if not self.selected:
            messagebox.showwarning("No paper", "Generate questions first.")
            return
        try:
            import subprocess
            import tempfile
            import sys

            # A unique filename avoids conflicts if multiple previews are opened.
            handle = tempfile.NamedTemporaryFile(
                prefix="smart_exam_paper_preview_", suffix=".pdf", delete=False
            )
            preview_path = handle.name
            handle.close()
            self._make_pdf(preview_path)

            if sys.platform.startswith("win"):
                os.startfile(preview_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", preview_path])
            else:
                import shutil
                viewer = next((shutil.which(name) for name in ("xdg-open", "gio", "evince", "okular")
                               if shutil.which(name)), None)
                if viewer:
                    command = [viewer, "open", preview_path] if viewer.endswith("gio") else [viewer, preview_path]
                    subprocess.Popen(command)
                else:
                    messagebox.showinfo(
                        "Preview created",
                        f"No PDF viewer launcher was found. The preview was saved here:\n{preview_path}"
                    )
        except Exception as error:
            messagebox.showerror("Preview failed", str(error))

    def export_pdf(self):
        if not self.selected:
            messagebox.showwarning("No paper", "Generate questions first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save question paper",
            defaultextension=".pdf",
            filetypes=[("PDF document", "*.pdf")],
            initialfile="question_paper.pdf",
        )
        if not path:
            return
        try:
            self._make_pdf(path)
            messagebox.showinfo("PDF created", f"Question paper saved successfully:\n{path}")
            self._set_status(f"PDF exported: {path}")
        except Exception as error:
            messagebox.showerror("PDF export failed", str(error))


def main():
    root = tk.Tk()
    if fitz is None or Document is None:
        messagebox.showerror(
            "Missing dependencies",
            "Please install the required packages first:\n\n"
            "python3 -m pip install -r requirements.txt\n\n"
            f"Import detail: {globals().get('IMPORT_ERROR', 'A required package is missing.')}"
        )
        root.destroy()
        return
    SmartExamApp(root)
    root.mainloop()


if __name__ == "__main__":
    import os
    main()
