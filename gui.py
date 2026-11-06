"""Module 7 - Frontend GUI (tkinter).

Required widgets:
  * a search input box            (self.entry)
  * a Search button               (self.search_button)
  * a read-only result area       (self.results, state="disabled" except while updating)

Also: Choose Folder / Build Index (fires the indexer), a Boolean / Ranked mode
switch, a dark "slate + teal" theme, example query chips, highlighted
snippets, notes about wildcard / spelling / Soundex fallbacks, and a status bar.
"""
from __future__ import annotations

import time
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import font as tkfont
from tkinter import ttk

from ir.engine import SearchEngine, SearchResponse

# ---- theme -------------------------------------------------------------------
THEME = {
    "bg": "#0f172a",          # window background
    "surface": "#1e293b",     # input + result panels
    "border": "#334155",
    "text": "#e2e8f0",
    "muted": "#94a3b8",
    "accent": "#14b8a6",      # teal
    "accent_hover": "#2dd4bf",
    "accent_text": "#042f2e",
    "match_bg": "#fde68a",    # highlighted query terms
    "match_fg": "#1f2937",
    "error": "#f87171",
}
FONT_CANDIDATES = ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Inter", "DejaVu Sans", "Arial")
EXAMPLES = ("network AND security", "comput*", "s?arch", "netwerk", "~sekurity",
            "title:network", "author:iyer")
HELP = ("Boolean: network AND security | cricket OR football | comput* NOT network | (a OR b) AND c\n"
        "Wildcard: comput*  *work  n*k  s?arch      Spelling / Soundex: netwerk, ~sekurity\n"
        "Zones: title:network  body:network      Fields: author:iyer  date:2006-03  doc:5  name:cricket")


class SearchApp(tk.Tk):
    def __init__(self, engine: SearchEngine) -> None:
        super().__init__()
        self.engine = engine
        self.title("WSM Search Engine")
        self.geometry("920x720")
        self.minsize(700, 520)
        self.configure(bg=THEME["bg"])

        self._pick_fonts()
        self._setup_styles()
        self._build_header()
        self._build_folder_bar()
        self._build_search_bar()
        self._build_mode_row()
        self._build_examples()
        self._build_results()
        self._build_status_bar()
        self.entry.focus_set()

        if engine.is_ready:                      # index already built by main.py
            self._on_index_ready()
        else:
            self._set_search_enabled(False)
            self._render([('Click "Build Index" to load the documents and run the indexer.', "info")])

    # ---- setup ---------------------------------------------------------------
    def _pick_fonts(self) -> None:
        available = set(tkfont.families(self))
        family = next((f for f in FONT_CANDIDATES if f in available), "TkDefaultFont")
        self.f_title = (family, 20, "bold")
        self.f_body = (family, 11)
        self.f_bold = (family, 11, "bold")
        self.f_small = (family, 9)
        self.f_input = (family, 13)

    def _setup_styles(self) -> None:
        t = THEME
        style = ttk.Style(self)
        style.theme_use("clam")  # the only built-in theme that honours custom colours everywhere

        style.configure("TFrame", background=t["bg"])
        style.configure("TLabel", background=t["bg"], foreground=t["text"], font=self.f_body)
        style.configure("Title.TLabel", font=self.f_title, foreground=t["text"])
        style.configure("Sub.TLabel", foreground=t["muted"], font=self.f_small)

        style.configure("Search.TEntry", fieldbackground=t["surface"], foreground=t["text"],
                        insertcolor=t["accent_hover"], bordercolor=t["border"],
                        lightcolor=t["border"], darkcolor=t["border"], padding=(10, 8))
        style.map("Search.TEntry", bordercolor=[("focus", t["accent"])],
                  lightcolor=[("focus", t["accent"])], darkcolor=[("focus", t["accent"])])

        style.configure("Accent.TButton", background=t["accent"], foreground=t["accent_text"],
                        font=self.f_bold, padding=(18, 9), borderwidth=0, focusthickness=0)
        style.map("Accent.TButton",
                  background=[("disabled", t["border"]), ("active", t["accent_hover"]),
                              ("pressed", t["accent_hover"])],
                  foreground=[("disabled", t["muted"])])

        style.configure("Outline.TButton", background=t["bg"], foreground=t["accent_hover"],
                        font=self.f_small, padding=(12, 5), borderwidth=1,
                        bordercolor=t["accent"], lightcolor=t["bg"], darkcolor=t["bg"],
                        focusthickness=0)
        style.map("Outline.TButton", background=[("active", t["surface"])])

        style.configure("Ghost.TButton", background=t["bg"], foreground=t["muted"],
                        font=self.f_small, padding=(12, 5), borderwidth=1,
                        bordercolor=t["border"], lightcolor=t["bg"], darkcolor=t["bg"],
                        focusthickness=0)
        style.map("Ghost.TButton", foreground=[("active", t["text"])],
                  background=[("active", t["surface"])])

        style.configure("Chip.TButton", background=t["surface"], foreground=t["muted"],
                        font=self.f_small, padding=(10, 4), borderwidth=1,
                        bordercolor=t["border"], lightcolor=t["surface"], darkcolor=t["surface"],
                        focusthickness=0)
        style.map("Chip.TButton", foreground=[("active", t["accent_hover"])],
                  background=[("active", t["surface"])], bordercolor=[("active", t["accent"])])

        style.configure("Mode.TRadiobutton", background=t["bg"], foreground=t["text"],
                        font=self.f_small, indicatorcolor=t["surface"], focusthickness=0)
        style.map("Mode.TRadiobutton",
                  background=[("active", t["bg"])],
                  indicatorcolor=[("selected", t["accent"]), ("!selected", t["surface"])],
                  foreground=[("active", t["accent_hover"])])

        style.configure("Vertical.TScrollbar", background=t["border"], troughcolor=t["surface"],
                        bordercolor=t["surface"], arrowcolor=t["muted"],
                        lightcolor=t["border"], darkcolor=t["border"])
        style.map("Vertical.TScrollbar", background=[("active", t["muted"])])

    def _build_header(self) -> None:
        head = ttk.Frame(self, padding=(20, 16, 20, 4))
        head.pack(fill="x")
        ttk.Label(head, text="WSM Search Engine", style="Title.TLabel").pack(anchor="w")
        ttk.Label(head, text="Boolean + ranked retrieval · wildcards · zones · spelling · Soundex",
                  style="Sub.TLabel").pack(anchor="w")

    def _build_folder_bar(self) -> None:
        bar = ttk.Frame(self, padding=(20, 8, 20, 0))
        bar.pack(fill="x")
        # the folder path is kept internally but not displayed
        self.folder_var = tk.StringVar(value=str(self.engine.folder or ""))
        ttk.Button(bar, text="Build Index", style="Outline.TButton", cursor="hand2",
                   command=self.build_index).pack(side="right")
        ttk.Button(bar, text="Choose Folder", style="Ghost.TButton", cursor="hand2",
                   command=self.choose_folder).pack(side="right", padx=(0, 6))

    def _build_search_bar(self) -> None:
        bar = ttk.Frame(self, padding=(20, 10, 20, 4))
        bar.pack(fill="x")
        self.query_var = tk.StringVar()
        self.entry = ttk.Entry(bar, textvariable=self.query_var, style="Search.TEntry",
                               font=self.f_input)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda _e: self.on_search())
        self.entry.bind("<Escape>", lambda _e: self.query_var.set(""))
        self.search_button = ttk.Button(bar, text="Search", style="Accent.TButton",
                                        command=self.on_search, cursor="hand2")
        self.search_button.pack(side="left", padx=(10, 0))

    def _build_mode_row(self) -> None:
        row = ttk.Frame(self, padding=(20, 0, 20, 2))
        row.pack(fill="x")
        ttk.Label(row, text="Mode", style="Sub.TLabel").pack(side="left", padx=(0, 8))
        self.mode_var = tk.StringVar(value="boolean")
        for text, value in (("Boolean", "boolean"), ("Ranked (overlap + score)", "ranked")):
            ttk.Radiobutton(row, text=text, value=value, variable=self.mode_var,
                            style="Mode.TRadiobutton", cursor="hand2").pack(side="left", padx=(0, 12))
        ttk.Button(row, text="What can I search?", style="Ghost.TButton", cursor="hand2",
                   command=self._show_welcome).pack(side="right")

    def _build_examples(self) -> None:
        row = ttk.Frame(self, padding=(20, 4, 20, 2))
        row.pack(fill="x")
        ttk.Label(row, text="Try", style="Sub.TLabel").pack(side="left", padx=(0, 6))
        for example in EXAMPLES:
            ttk.Button(row, text=example, style="Chip.TButton", cursor="hand2",
                       command=lambda q=example: self._run_example(q)).pack(side="left", padx=(0, 5))
        ttk.Label(self, text=HELP, style="Sub.TLabel", justify="left", padding=(20, 4, 20, 6)
                  ).pack(fill="x")

    def _build_results(self) -> None:
        t = THEME
        body = ttk.Frame(self, padding=(20, 0, 20, 8))
        body.pack(fill="both", expand=True)
        frame = tk.Frame(body, bg=t["surface"], highlightthickness=1,
                         highlightbackground=t["border"], highlightcolor=t["border"])
        frame.pack(fill="both", expand=True)

        self.results = tk.Text(frame, wrap="word", state="disabled", cursor="arrow",
                               bg=t["surface"], fg=t["text"], font=self.f_body, relief="flat",
                               borderwidth=0, highlightthickness=0, padx=18, pady=14,
                               selectbackground=t["accent"], selectforeground=t["accent_text"],
                               spacing1=2, spacing3=2)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.results.yview)
        self.results.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.results.pack(side="left", fill="both", expand=True)
        self.results.bind("<Button-1>", lambda _e: self.results.focus_set())  # allow select/copy

        r = self.results
        r.tag_configure("summary", font=self.f_bold, foreground=t["accent_hover"], spacing3=6)
        r.tag_configure("rank", foreground=t["muted"], font=self.f_small)
        r.tag_configure("title", font=self.f_bold, foreground=t["text"])
        r.tag_configure("meta", foreground=t["muted"], font=self.f_small)
        r.tag_configure("score", foreground=t["accent_hover"], font=self.f_small, lmargin1=14, lmargin2=14)
        r.tag_configure("detail", foreground=t["muted"], font=self.f_small, lmargin1=24, lmargin2=24)
        r.tag_configure("snippet", foreground=t["muted"], lmargin1=14, lmargin2=14, spacing1=4, spacing3=12)
        r.tag_configure("match", background=t["match_bg"], foreground=t["match_fg"])
        r.tag_configure("info", foreground=t["muted"], font=self.f_small, spacing3=2)
        r.tag_configure("error", foreground=t["error"], font=self.f_bold)
        r.tag_configure("h", font=self.f_bold, foreground=t["text"], spacing1=8)

    def _build_status_bar(self) -> None:
        bar = ttk.Frame(self, padding=(20, 0, 20, 12))
        bar.pack(fill="x")
        self.status_left = ttk.Label(bar, style="Sub.TLabel", text="Index not built.")
        self.status_left.pack(side="left")
        self.status_right = ttk.Label(bar, style="Sub.TLabel", text="Ready")
        self.status_right.pack(side="right")

    # ---- actions -------------------------------------------------------------
    def _set_search_enabled(self, enabled: bool) -> None:
        self.search_button.state(["!disabled"] if enabled else ["disabled"])

    def choose_folder(self) -> None:
        chosen = filedialog.askdirectory(title="Select folder of .txt files")
        if chosen:
            self.folder_var.set(chosen)
            self._set_search_enabled(False)
            self.status_left.configure(text="Index not built.")
            self._render([('Folder changed. Click "Build Index".', "info")])

    def build_index(self) -> None:
        try:
            self.engine.build_index(self.folder_var.get())
        except (FileNotFoundError, ValueError) as err:
            messagebox.showerror("Cannot build index", str(err))
            return
        self._on_index_ready(announce=True)

    def _on_index_ready(self, announce: bool = False) -> None:
        stats = self.engine.stats()
        self._set_search_enabled(True)
        self.status_left.configure(text=stats)
        self.status_right.configure(text="Index ready")
        if announce:
            self._render([
                ("INDEXER FIRED\n", "summary"),
                (stats + "\n\n", "info"),
                ("Pipeline: tokenize → case fold → stopwords → stem → "
                 "title / body / all zone indexes + parametric fields.\n", "info"),
                ("Now enter a query.", "info"),
            ])
        else:
            self._show_welcome()

    def _run_example(self, query: str) -> None:
        self.query_var.set(query)
        self.on_search()

    def on_search(self) -> None:
        query = self.query_var.get().strip()
        if not query:
            self._render([("Please enter a query.", "error")])
            self.status_right.configure(text="Empty query")
            return
        started = time.perf_counter()
        response = self.engine.search(query, self.mode_var.get())
        elapsed_ms = (time.perf_counter() - started) * 1000
        self._show_response(response)
        if response.error:
            self.status_right.configure(text="Error")
        else:
            self.status_right.configure(text=f"{len(response.hits)} result(s) · {elapsed_ms:.2f} ms")

    # ---- rendering -----------------------------------------------------------
    def _show_welcome(self) -> None:
        """Guide: how to search and what is in the collection (built from the index)."""
        if not self.engine.is_ready:
            self._render([('Click "Build Index" first, then this guide lists what you can search.', "info")])
            return
        docs = self.engine.documents
        parts = [
            ("What can I search?\n", "summary"),
            (f"The index holds {len(docs)} documents. Search for any word that appears in "
             "their titles or text. Words to try:\n", "info"),
            ("   " + ", ".join(self.engine.suggested_terms(16)) + "\n\n", "title"),
            ("How to search\n", "h"),
            ("• Words are combined with AND; use AND, OR, NOT and parentheses.\n", "info"),
            ("• Wildcards: * matches any characters (comput*), ? matches one (s?arch).\n", "info"),
            ("• Misspelled words are corrected (netwerk); ~word matches by sound (~sekurity).\n", "info"),
            ("• Restrict to a zone (title:network) or a field (author:iyer, date:2006-03, doc:5, name:cricket).\n", "info"),
            ("• Ranked mode orders documents by overlap, then tf × idf score (title counts double).\n", "info"),
            ("• Searching ignores upper / lower case and common stopwords.\n\n", "info"),
            ("Documents in the collection (type doc:N to read one)\n", "h"),
        ]
        for d in docs:
            parts.append((f"{d.doc_id:>3}.  ", "rank"))
            parts.append((d.title, "title"))
            parts.append((f"   {d.author} · {d.date}\n", "meta"))
        self._render(parts)

    def _show_response(self, resp: SearchResponse) -> None:
        if resp.error:
            self._render([(resp.error, "error")])
            return

        parts, marks = [], {}
        n = len(resp.hits)
        quoted = f"“{resp.query}”"
        if resp.mode == "ranked":
            summary = (f"{n} ranked result(s) for {quoted}" if n else f"No documents matched {quoted}.")
        elif resp.mode == "documents":
            summary = (f"{n} document(s) for {quoted}" if n else f"No document matches {quoted}.")
        else:
            summary = (f"{n} document(s) matched {quoted}" if n else f"No documents matched {quoted}.")
        parts.append((summary + "\n", "summary"))
        if resp.mode == "ranked" and n:
            parts.append(("ordered by overlap (distinct query terms found), then accumulated score\n", "info"))
        for note in resp.notes:
            parts.append((f"• {note}\n", "info"))
        if n:
            parts.append(("\n", "info"))

        for rank, hit in enumerate(resp.hits, start=1):
            d = hit.document
            parts.append((f"{rank:>2}.  ", "rank"))
            parts.append((f"{d.name}", "title"))
            parts.append((f"   {d.title} · {d.author} · {d.date}\n", "meta"))
            if resp.mode == "ranked":
                parts.append((f"overlap {hit.overlap}/{resp.n_terms} · score {hit.score:.2f}\n", "score"))
                for term, matched, tf, idf, weight in hit.details:
                    parts.append((f'"{term}" → {matched}: tf {tf:g} × idf {idf:.2f} = +{weight:.2f}\n', "detail"))
            marks[len(parts)] = hit.highlights
            parts.append((hit.snippet + "\n", "snippet"))
        self._render(parts, marks)

    def _render(self, parts, marks=None) -> None:
        r = self.results
        r.configure(state="normal")
        r.delete("1.0", "end")
        marks = marks or {}
        for i, (text, tag) in enumerate(parts):
            base = r.index("end-1c")
            r.insert("end", text, tag)
            for s, e in marks.get(i, ()):
                r.tag_add("match", f"{base}+{s}c", f"{base}+{e}c")
        r.configure(state="disabled")  # keep the result area read-only
        r.yview_moveto(0)
