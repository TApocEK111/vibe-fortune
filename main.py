"""
Wheel of Fortune — simple wheel of fortune with GUI.

Run: python wheel_of_fortune.py

Importing options — three ways:

1) File (button "Import options…"):
   CSV format: <name>[<separator><weight>], separator — ',' or ';'.
   UTF-8 encoding. Empty lines and '#' — comments.

2) CSV paste (button "Import CSV (paste)"):
   Paste lines into the text field:
       Jackpot, 1
       Prize 1, 3
       Prize 2;3
       Nothing
       Small win, 20
   Weight may be omitted — then it equals 1.
   Separator — ',' or ';' (one type per line).

3) Two-step import (button "Import in 2 steps"):
   Step 1: list of names, one per line.
   Step 2: list of weights, one per line.
   The number of lines must MATCH, otherwise — an error
   with the actual counts.

Elimination mode — global: if enabled, any dropped option
is removed from the wheel (until only one remains — the winner).
"""

from __future__ import annotations

import math
import random
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk


# ---------------------------------------------------------------------------
# Localization
# ---------------------------------------------------------------------------

TRANSLATIONS = {
    "en": {
        "app_title": "Wheel of Fortune",
        "title_label": "Wheel of Fortune",
        "language": "Language:",
        "duration_label": "Spin duration (sec):",
        "eliminate_check": "Elimination mode\n(dropped option is removed)",
        "import_section": "Import:",
        "import_file": "📥 From file…",
        "import_csv": "📋 CSV — paste text…",
        "import_two_step": "🧮 Two steps: names + weights…",
        "load_example": "💾 Load example",
        "reset_eliminated": "♻ Restore eliminated",
        "spin_button": "🎡 SPIN",
        "result_label": "Result:",
        "options_label": "Options (probability):",
        "result_none": "—",
        "result_spinning": "…",
        "result_eliminated": "{name}\n(eliminated)",
        "result_winner": "{name}\n(eliminated)\n\n🏆 Winner: {last}",
        "stats": "Left: {count} opt.  |  Σweight = {total:.3f}",
        "listbox_item": "  {name}  —  {p:.2f}%",
        "no_options": "No options",
        "import_file_title": "Import options",
        "filetypes_csv": "CSV/text",
        "filetypes_all": "All files",
        # dialogs
        "dlg_csv_title": "Import CSV — paste lines",
        "dlg_csv_field": "Option lines",
        "dlg_csv_hint": (
            "Format: <name>,<weight>  or  <name>;<weight>.\n"
            "Weight may be omitted — then 1. Separator — ',' or ';'."
        ),
        "dlg_two_step_title": "Two-step import",
        "dlg_two_step_names": "Step 1. Names (one per line)",
        "dlg_two_step_names_hint": "Example:\nJackpot\nPrize 1\nNothing",
        "dlg_two_step_weights": "Step 2. Weights (one per line)",
        "dlg_two_step_weights_hint": (
            "Number of lines must match step 1.\nExample:\n1\n3\n10"
        ),
        "btn_cancel": "Cancel",
        "btn_import": "Import",
        "btn_paste": "Paste",
        "btn_copy": "Copy",
        "btn_cut": "Cut",
        "btn_select_all": "Select all",
        # errors
        "err_title": "Import error",
        "err_title_short": "Error",
        "err_no_options": "No options.",
        "err_all_weights": "All weights are non-positive or infinite.",
        "err_duration_num": "Spin duration must be a number.",
        "err_duration_range": "Spin duration — from 0.05 to 120 seconds.",
        # parser errors
        "err_weight_not_number": "Line {lineno}: weight '{token}' — not a number.",
        "err_weight_positive": "Line {lineno}: weight must be > 0.",
        "err_empty_name": "Line {lineno}: empty name.",
        "err_count_mismatch": (
            "Line counts do not match:\n"
            "  names:   {n}\n"
            "  weights: {w}\n"
            "The lists must be the same length."
        ),
    },
    "ru": {
        "app_title": "Колесо Фортуны",
        "title_label": "Колесо Фортуны",
        "language": "Язык:",
        "duration_label": "Время прокрутки (сек):",
        "eliminate_check": "Режим на выбывание\n(выпавший вариант удаляется)",
        "import_section": "Импорт:",
        "import_file": "📥 Из файла…",
        "import_csv": "📋 CSV — вставить текст…",
        "import_two_step": "🧮 Два шага: позиции + веса…",
        "load_example": "💾 Загрузить пример",
        "reset_eliminated": "♻ Восстановить выбывших",
        "spin_button": "🎡 КРУТИТЬ",
        "result_label": "Результат:",
        "options_label": "Варианты (вероятность):",
        "result_none": "—",
        "result_spinning": "…",
        "result_eliminated": "{name}\n(выбыл)",
        "result_winner": "{name}\n(выбыл)\n\n🏆 Победитель: {last}",
        "stats": "Осталось: {count} вар.  |  Σвес = {total:.3f}",
        "listbox_item": "  {name}  —  {p:.2f}%",
        "no_options": "Нет вариантов",
        "import_file_title": "Импорт вариантов",
        "filetypes_csv": "CSV/текст",
        "filetypes_all": "Все файлы",
        "dlg_csv_title": "Импорт CSV — вставьте строки",
        "dlg_csv_field": "Строки вариантов",
        "dlg_csv_hint": (
            "Формат: <название>,<вес>  или  <название>;<вес>.\n"
            "Вес можно опустить — тогда 1. Разделитель — ',' или ';'."
        ),
        "dlg_two_step_title": "Импорт в два шага",
        "dlg_two_step_names": "Шаг 1. Позиции (по одной в строке)",
        "dlg_two_step_names_hint": "Например:\nДжекпот\nПриз 1\nПусто",
        "dlg_two_step_weights": "Шаг 2. Веса (по одному в строке)",
        "dlg_two_step_weights_hint": (
            "Количество строк должно совпадать с шагом 1.\n"
            "Например:\n1\n3\n10"
        ),
        "btn_cancel": "Отмена",
        "btn_import": "Импортировать",
        "btn_paste": "Вставить",
        "btn_copy": "Копировать",
        "btn_cut": "Вырезать",
        "btn_select_all": "Выделить всё",
        "err_title": "Ошибка импорта",
        "err_title_short": "Ошибка",
        "err_no_options": "Нет ни одного варианта.",
        "err_all_weights": "Все веса неположительны или бесконечны.",
        "err_duration_num": "Время прокрутки должно быть числом.",
        "err_duration_range": "Время прокрутки — от 0.05 до 120 секунд.",
        "err_weight_not_number": "Строка {lineno}: вес '{token}' — не число.",
        "err_weight_positive": "Строка {lineno}: вес должен быть > 0.",
        "err_empty_name": "Строка {lineno}: пустое название.",
        "err_count_mismatch": (
            "Количество строк не сходится:\n"
            "  названий: {n}\n"
            "  весов:    {w}\n"
            "Списки должны быть одинаковой длины."
        ),
    },
}

DEFAULT_LANGUAGE = "en"


def tr(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    """Translate a key. Falls back to English, then to the key itself."""
    table = TRANSLATIONS.get(lang) or TRANSLATIONS[DEFAULT_LANGUAGE]
    template = table.get(key) or TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template
    return template


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Option:
    name: str
    weight: float


class Wheel:
    """Wheel with weights. Guarantees a valid probability distribution."""

    def __init__(self) -> None:
        self.options: list[Option] = []
        self._sectors: list[tuple[Option, float, float]] = []

    def set_options(self, options: list[Option], lang: str = DEFAULT_LANGUAGE) -> None:
        if not options:
            self.options = []
            self._sectors = []
            return
        clean = [o for o in options if o.weight > 0 and math.isfinite(o.weight)]
        if not clean:
            raise ValueError(tr("err_all_weights", lang))
        self.options = clean
        self._rebuild()

    def eliminate(self, option: Option) -> None:
        remaining = [o for o in self.options if o is not option]
        if remaining:
            self.set_options(remaining)
        else:
            self.options = []
            self._sectors = []

    def _rebuild(self) -> None:
        total = sum(o.weight for o in self.options)
        self._sectors = []
        start = 0.0
        for i, o in enumerate(self.options):
            if i == len(self.options) - 1:
                end = 360.0
            else:
                end = start + 360.0 * o.weight / total
            self._sectors.append((o, start, end))
            start = end

    def total_weight(self) -> float:
        return sum(o.weight for o in self.options)

    def sectors(self) -> list[tuple[Option, float, float]]:
        return list(self._sectors)

    def pick_index(self) -> int:
        r = random.random() * self.total_weight()
        acc = 0.0
        for i, o in enumerate(self.options):
            acc += o.weight
            if r < acc or i == len(self.options) - 1:
                return i
        return len(self.options) - 1

    def spin_target(self, index: int) -> float:
        _o, s, e = self._sectors[index]
        width = e - s
        if width <= 1e-12:
            return (s + e) / 2.0
        margin = min(width * 0.1, 1.0)
        return random.uniform(s + margin, e - margin)


# ---------------------------------------------------------------------------
# Import parser (unified rules for all scenarios)
# ---------------------------------------------------------------------------

class ImportParser:
    """Parse import text data. All errors are ValueError with a line number."""

    DEFAULT_WEIGHT = 1.0

    @classmethod
    def _parse_weight(cls, token: str, lineno: int, lang: str = DEFAULT_LANGUAGE) -> float:
        token = token.strip().replace(",", ".")
        try:
            w = float(token)
        except ValueError:
            raise ValueError(tr("err_weight_not_number", lang, lineno=lineno, token=token))
        if not math.isfinite(w) or w <= 0:
            raise ValueError(tr("err_weight_positive", lang, lineno=lineno))
        return w

    @classmethod
    def parse_csv(cls, text: str, lang: str = DEFAULT_LANGUAGE) -> list[Option]:
        """
        Parse CSV-like text.
        Line: <name>[<sep><weight>], sep = ',' or ';'.
        Weight is optional (defaults to 1). Name must not be empty.
        """
        options: list[Option] = []
        for lineno, raw in enumerate(text.splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            # Choose separator: ';' has priority, as ',' may appear in the name.
            if ";" in line:
                parts = [p.strip() for p in line.split(";", 1)]
            elif "," in line:
                parts = [p.strip() for p in line.split(",", 1)]
            else:
                parts = [line]

            name = parts[0]
            if not name:
                raise ValueError(tr("err_empty_name", lang, lineno=lineno))

            weight = cls.DEFAULT_WEIGHT
            if len(parts) == 2 and parts[1] != "":
                weight = cls._parse_weight(parts[1], lineno, lang)

            options.append(Option(name, weight))

        if not options:
            raise ValueError(tr("err_no_options", lang))
        return options

    @classmethod
    def parse_two_step(cls, names_text: str, weights_text: str,
                       lang: str = DEFAULT_LANGUAGE) -> list[Option]:
        """
        Two-step import: list of names + list of weights, line by line.
        Line counts must match.
        """
        names = [ln.strip() for ln in names_text.splitlines() if ln.strip()]
        weights_raw = [ln.strip() for ln in weights_text.splitlines() if ln.strip()]

        if len(names) != len(weights_raw):
            raise ValueError(
                tr("err_count_mismatch", lang, n=len(names), w=len(weights_raw))
            )
        if not names:
            raise ValueError(tr("err_no_options", lang))

        options: list[Option] = []
        for i, (name, w_raw) in enumerate(zip(names, weights_raw), 1):
            weight = cls._parse_weight(w_raw, i, lang)
            options.append(Option(name, weight))
        return options


# ---------------------------------------------------------------------------
# Import dialogs
# ---------------------------------------------------------------------------

class TextImportDialog(tk.Toplevel):
    """Modal window with one or two text fields."""

    def __init__(
        self,
        parent: "WheelApp",
        title: str,
        fields: list[tuple[str, str]],   # [(label, hint)]
        on_submit,                       # (list[str]) -> list[Option] | None
        lang: str = DEFAULT_LANGUAGE,
    ) -> None:
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.transient(parent)
        self.resizable(True, True)
        self.minsize(520, 360)

        self._fields = fields
        self._on_submit = on_submit
        self._texts: list[tk.Text] = []
        self._lang = lang

        outer = ttk.Frame(self, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        for label, hint in fields:
            ttk.Label(outer, text=label,
                      font=("Segoe UI", 11, "bold")).pack(anchor="w")
            ttk.Label(outer, text=hint,
                      foreground="#9aa4b8").pack(anchor="w", pady=(0, 4))
            txt = tk.Text(
                outer, height=8, wrap="none",
                bg="#2c3140", fg=FG, insertbackground=FG,
                relief="flat", borderwidth=0, padx=8, pady=6,
                undo=True,
            )
            txt.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            self._bind_text_shortcuts(txt)
            self._texts.append(txt)

        btn_row = ttk.Frame(outer)
        btn_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(btn_row, text=tr("btn_cancel", lang),
                   command=self.destroy).pack(side=tk.RIGHT)
        ttk.Button(btn_row, text=tr("btn_import", lang),
                   command=self._submit).pack(side=tk.RIGHT, padx=(0, 8))

        self.bind("<Escape>", lambda _e: self.destroy())
        self.grab_set()
        self._center_on(parent)

        self.focus_force()
        if self._texts:
            first = self._texts[0]
            first.focus_set()
            self.after_idle(lambda: first.focus_set())

    def _bind_text_shortcuts(self, txt: tk.Text) -> None:
        txt.bind("<Control-v>", lambda _e: (txt.event_generate("<<Paste>>"), "break")[1])
        txt.bind("<Control-V>", lambda _e: (txt.event_generate("<<Paste>>"), "break")[1])
        txt.bind("<Control-c>", lambda _e: (txt.event_generate("<<Copy>>"), "break")[1])
        txt.bind("<Control-C>", lambda _e: (txt.event_generate("<<Copy>>"), "break")[1])
        txt.bind("<Control-x>", lambda _e: (txt.event_generate("<<Cut>>"), "break")[1])
        txt.bind("<Control-X>", lambda _e: (txt.event_generate("<<Cut>>"), "break")[1])
        txt.bind("<Control-a>", self._select_all)
        txt.bind("<Control-A>", self._select_all)
        # macOS: Command instead of Control
        txt.bind("<Command-v>", lambda _e: (txt.event_generate("<<Paste>>"), "break")[1])
        txt.bind("<Command-c>", lambda _e: (txt.event_generate("<<Copy>>"), "break")[1])
        txt.bind("<Command-x>", lambda _e: (txt.event_generate("<<Cut>>"), "break")[1])
        txt.bind("<Command-a>", self._select_all)
        txt.bind("<Button-3>", self._on_right_click)
        txt.bind("<Button-2>", self._on_right_click)  # macOS sometimes Button-2
        txt.bind("<Button-1>", lambda _e: txt.focus_set(), add="+")

    @staticmethod
    def _select_all(event):
        event.widget.tag_add("sel", "1.0", "end-1c")
        return "break"

    def _on_right_click(self, event) -> str:
        txt = event.widget
        lang = self._lang
        menu = tk.Menu(txt, tearoff=0, bg="#2c3140", fg=FG,
                       activebackground="#3d4457", activeforeground=FG)
        try:
            has_sel = bool(txt.get("sel.first", "sel.last"))
        except tk.TclError:
            has_sel = False
        menu.add_command(label=tr("btn_paste", lang),
                         command=lambda: txt.event_generate("<<Paste>>"))
        menu.add_command(label=tr("btn_copy", lang),
                         state=("normal" if has_sel else "disabled"),
                         command=lambda: txt.event_generate("<<Copy>>"))
        menu.add_command(label=tr("btn_cut", lang),
                         state=("normal" if has_sel else "disabled"),
                         command=lambda: txt.event_generate("<<Cut>>"))
        menu.add_separator()
        menu.add_command(label=tr("btn_select_all", lang),
                         command=lambda: (txt.tag_add("sel", "1.0", "end-1c"),
                                          txt.focus_set()))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    def _center_on(self, parent: tk.Misc) -> None:
        self.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _submit(self) -> None:
        texts = [t.get("1.0", tk.END) for t in self._texts]
        try:
            result = self._on_submit(texts)
        except ValueError as e:
            messagebox.showerror(tr("err_title", self._lang), str(e), parent=self)
            return
        if result:
            self._on_result(result)
            self.destroy()

    _on_result = staticmethod(lambda _opts: None)


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

BG = "#1b1f2a"
FG = "#e8e8f0"
ACCENT = "#ffcc33"
SECTOR_COLORS = [
    "#e74c3c", "#3498db", "#2ecc71", "#9b59b6", "#e67e22",
    "#1abc9c", "#f1c40f", "#e91e63", "#00bcd4", "#8bc34a",
    "#ff5722", "#795548", "#607d8b", "#c0392b", "#2980b9",
]


class WheelApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.lang: str = DEFAULT_LANGUAGE
        self.wheel = Wheel()
        self._original_options: list[Option] = []
        self._spinning = False
        self._angle = 0.0
        self._timer_left: float = 0.0
        self._last_options: list[Option] | None = None

        self._build_ui()

    # ------------------------------------------------------------------ UI ---
    def _build_ui(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("TButton", padding=6)
        style.configure("TCheckbutton", background=BG, foreground=FG)
        style.configure("TEntry", fieldbackground="#2c3140", foreground=FG)
        style.map("TCheckbutton", background=[("active", BG)])

        # left container (rebuilt on language change)
        self.left = ttk.Frame(self, padding=12)
        self.left.pack(side=tk.LEFT, fill=tk.Y)

        self.right = ttk.Frame(self, padding=12)
        self.right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.right, bg=BG, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda _e: self._draw())

        self._build_left()

        self._load_default()

    def _build_left(self) -> None:
        """(Re)build the left panel, applying the current language."""
        for child in self.left.winfo_children():
            child.destroy()

        left = self.left
        lang = self.lang

        ttk.Label(left, text=tr("title_label", lang),
                  font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Separator(left).pack(fill=tk.X, pady=8)

        # language selector
        lang_row = ttk.Frame(left)
        lang_row.pack(anchor="w", pady=(0, 8))
        ttk.Label(lang_row, text=tr("language", lang)).pack(side=tk.LEFT)
        self.lang_var = tk.StringVar(value="English" if lang == "en" else "Русский")
        lang_combo = ttk.Combobox(
            lang_row, textvariable=self.lang_var, state="readonly",
            values=["English", "Русский"], width=10,
        )
        lang_combo.pack(side=tk.LEFT, padx=(6, 0))
        lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)

        ttk.Label(left, text=tr("duration_label", lang)).pack(anchor="w")
        if not hasattr(self, "duration_var"):
            self.duration_var = tk.DoubleVar(value=4.0)
        ttk.Entry(left, textvariable=self.duration_var, width=10).pack(
            anchor="w", pady=(2, 10))

        if not hasattr(self, "eliminate_var"):
            self.eliminate_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            left,
            text=tr("eliminate_check", lang),
            variable=self.eliminate_var,
        ).pack(anchor="w", pady=(0, 10))

        # --- import ---
        ttk.Label(left, text=tr("import_section", lang),
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Button(left, text=tr("import_file", lang),
                   command=self._import_file).pack(fill=tk.X, pady=2)
        ttk.Button(left, text=tr("import_csv", lang),
                   command=self._import_csv_paste).pack(fill=tk.X, pady=2)
        ttk.Button(left, text=tr("import_two_step", lang),
                   command=self._import_two_step).pack(fill=tk.X, pady=2)

        ttk.Separator(left).pack(fill=tk.X, pady=10)

        ttk.Button(left, text=tr("load_example", lang),
                   command=self._load_default).pack(fill=tk.X, pady=2)
        ttk.Button(left, text=tr("reset_eliminated", lang),
                   command=self._reset_eliminated).pack(fill=tk.X, pady=2)

        ttk.Separator(left).pack(fill=tk.X, pady=10)

        self.spin_btn = tk.Button(
            left,
            text=tr("spin_button", lang),
            font=("Segoe UI", 16, "bold"),
            bg=ACCENT, fg="#1b1f2a",
            activebackground="#ffdd66",
            relief="flat",
            command=self._spin,
        )
        self.spin_btn.pack(fill=tk.X, ipady=8, pady=(0, 10))

        if not hasattr(self, "result_var"):
            self.result_var = tk.StringVar(value=tr("result_none", lang))
        ttk.Label(left, text=tr("result_label", lang)).pack(anchor="w")
        self.result_label = tk.Label(
            left, textvariable=self.result_var,
            font=("Segoe UI", 15, "bold"),
            bg="#2c3140", fg=ACCENT,
            wraplength=240, justify="left", anchor="w",
            padx=8, pady=8,
        )
        self.result_label.pack(fill=tk.X, pady=(2, 10))

        ttk.Label(left, text=tr("options_label", lang)).pack(anchor="w")
        self.listbox = tk.Listbox(
            left, height=10,
            bg="#2c3140", fg=FG, selectbackground="#3d4457",
            relief="flat", borderwidth=0, activestyle="none",
        )
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=(2, 4))

        self.stats_var = tk.StringVar(value="")
        ttk.Label(left, textvariable=self.stats_var,
                  foreground="#9aa4b8").pack(anchor="w")

        self._refresh_list()

    def _on_language_change(self, _event=None) -> None:
        choice = self.lang_var.get()
        new_lang = "ru" if choice == "Русский" else "en"
        if new_lang == self.lang:
            return
        self.lang = new_lang
        self.title(tr("app_title", self.lang))
        # Preserve current result text as-is (it's user data).
        self._build_left()

    # ------------------------------------------------------------- imports ---
    def _import_file(self) -> None:
        path = filedialog.askopenfilename(
            title=tr("import_file_title", self.lang),
            filetypes=[
                (tr("filetypes_csv", self.lang), "*.csv *.txt"),
                (tr("filetypes_all", self.lang), "*.*"),
            ],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                text = f.read()
            options = ImportParser.parse_csv(text, self.lang)
        except Exception as e:
            messagebox.showerror(tr("err_title", self.lang), str(e))
            return
        self._apply_options(options)

    def _import_csv_paste(self) -> None:
        dlg = TextImportDialog(
            self,
            title=tr("dlg_csv_title", self.lang),
            fields=[(
                tr("dlg_csv_field", self.lang),
                tr("dlg_csv_hint", self.lang),
            )],
            on_submit=lambda texts: ImportParser.parse_csv(texts[0], self.lang),
            lang=self.lang,
        )
        dlg._on_result = self._apply_options  # type: ignore[method-assign]
        self.wait_window(dlg)

    def _import_two_step(self) -> None:
        dlg = TextImportDialog(
            self,
            title=tr("dlg_two_step_title", self.lang),
            fields=[
                (tr("dlg_two_step_names", self.lang),
                 tr("dlg_two_step_names_hint", self.lang)),
                (tr("dlg_two_step_weights", self.lang),
                 tr("dlg_two_step_weights_hint", self.lang)),
            ],
            on_submit=lambda texts: ImportParser.parse_two_step(
                texts[0], texts[1], self.lang),
            lang=self.lang,
        )
        dlg._on_result = self._apply_options  # type: ignore[method-assign]
        self.wait_window(dlg)

    # ------------------------------------------------------------- loading ---
    def _load_default(self) -> None:
        if self.lang == "ru":
            defaults = [
                ("Джекпот", 1.0),
                ("Приз 1", 3.0),
                ("Приз 2", 3.0),
                ("Пусто", 10.0),
                ("Мелочь", 20.0),
                ("Утешительный", 5.0),
            ]
        else:
            defaults = [
                ("Jackpot", 1.0),
                ("Prize 1", 3.0),
                ("Prize 2", 3.0),
                ("Nothing", 10.0),
                ("Small win", 20.0),
                ("Consolation", 5.0),
            ]
        self._apply_options([Option(n, w) for n, w in defaults])

    def _apply_options(self, options: list[Option]) -> None:
        try:
            self.wheel.set_options(options, self.lang)
        except ValueError as e:
            messagebox.showerror(tr("err_title_short", self.lang), str(e))
            return
        self._original_options = [Option(o.name, o.weight) for o in self.wheel.options]
        self._angle = 0.0
        self._spinning = False
        self.spin_btn.config(state=tk.NORMAL)
        self.result_var.set(tr("result_none", self.lang))
        self._refresh_list()
        self._draw()

    def _refresh_list(self) -> None:
        if not hasattr(self, "listbox"):
            return
        self.listbox.delete(0, tk.END)
        total = self.wheel.total_weight() or 1.0
        for o in self.wheel.options:
            p = 100.0 * o.weight / total
            self.listbox.insert(tk.END, tr("listbox_item", self.lang,
                                           name=o.name, p=p))
        self.stats_var.set(tr("stats", self.lang,
                              count=len(self.wheel.options), total=total))

    def _reset_eliminated(self) -> None:
        if not self._original_options:
            return
        self._apply_options([Option(o.name, o.weight) for o in self._original_options])
        self.result_var.set(tr("result_none", self.lang))

    # --------------------------------------------------------------- spin ---
    def _spin(self) -> None:
        if self._spinning or not self.wheel.options:
            return
        try:
            duration = float(self.duration_var.get())
        except (ValueError, tk.TclError):
            messagebox.showerror(tr("err_title_short", self.lang),
                                 tr("err_duration_num", self.lang))
            return
        if not (0.05 <= duration <= 120):
            messagebox.showerror(tr("err_title_short", self.lang),
                                 tr("err_duration_range", self.lang))
            return

        self._spinning = True
        self.spin_btn.config(state=tk.DISABLED)
        self.result_var.set(tr("result_spinning", self.lang))

        idx = self.wheel.pick_index()
        self._target_index = idx
        self._target_angle = self.wheel.spin_target(idx)

        start_angle = self._angle % 360.0
        turns = random.randint(4, 7)
        target_final = (360.0 - self._target_angle) % 360.0
        delta = (target_final - start_angle) % 360.0 + 360.0 * turns
        self._spin_start = start_angle
        self._spin_delta = delta
        self._spin_t0 = time.perf_counter()
        self._spin_duration = duration
        self._timer_left = duration

        self._animate()

    def _animate(self) -> None:
        if not self._spinning:
            return
        t = time.perf_counter() - self._spin_t0
        p = min(1.0, t / self._spin_duration)
        eased = 1.0 - (1.0 - p) ** 3
        self._angle = self._spin_start + self._spin_delta * eased
        self._timer_left = max(0.0, self._spin_duration - t)
        self._draw()
        if p < 1.0:
            self.after(16, self._animate)
        else:
            self._finish_spin()

    def _finish_spin(self) -> None:
        self._spinning = False
        self._timer_left = 0.0
        self._angle = (self._spin_start + self._spin_delta) % 360.0
        self._draw()

        winner = self.wheel.options[self._target_index]
        self.result_var.set(winner.name)

        if self.eliminate_var.get() and len(self.wheel.options) > 1:
            self.wheel.eliminate(winner)
            self._refresh_list()
            self._draw()
            self.result_var.set(tr("result_eliminated", self.lang, name=winner.name))
            if len(self.wheel.options) == 1:
                last = self.wheel.options[0]
                self.result_var.set(tr("result_winner", self.lang,
                                       name=winner.name, last=last.name))

        self.spin_btn.config(state=tk.NORMAL)

    # ----------------------------------------------------------- rendering ---
    def _draw(self) -> None:
        c = self.canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10 or h < 10:
            return

        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 60
        if r <= 0:
            return

        sectors = self.wheel.sectors()
        if not sectors:
            c.create_text(cx, cy, text=tr("no_options", self.lang),
                          fill=FG, font=("Segoe UI", 16))
            return

        # countdown above the wheel
        if self._spinning:
            top_y = cy - r - 50
            txt = f"{self._timer_left:0.1f} " + ("s" if self.lang == "en" else "с")
            c.create_text(cx + 2, top_y + 2, text=txt,
                          fill="#0d0f14",
                          font=("Segoe UI", 22, "bold"))
            c.create_text(cx, top_y, text=txt,
                          fill=ACCENT,
                          font=("Segoe UI", 22, "bold"))

        rot = self._angle

        for i, (opt, s, e) in enumerate(sectors):
            a1 = 90.0 - (s + rot)
            a2 = 90.0 - (e + rot)
            start = a2
            extent = a1 - a2
            color = SECTOR_COLORS[i % len(SECTOR_COLORS)]
            c.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=start, extent=extent,
                fill=color, outline="#0d0f14", width=2,
            )

            mid = (s + e) / 2.0
            a_screen = mid + rot
            rad = math.radians(a_screen)
            tx = cx + math.sin(rad) * r * 0.62
            ty = cy - math.cos(rad) * r * 0.62

            label = opt.name
            if len(label) > 14:
                label = label[:13] + "…"
            if abs(extent) >= 6:
                c.create_text(
                    tx, ty, text=label, fill="#ffffff",
                    font=("Segoe UI", 10, "bold"),
                    width=max(40, int(r * 0.5)),
                )

        c.create_oval(cx - r, cy - r, cx + r, cy + r,
                      outline="#0d0f14", width=4)

        c.create_polygon(
            cx - 12, cy - r - 4,
            cx + 12, cy - r - 4,
            cx, cy - r + 22,
            fill=ACCENT, outline="#0d0f14", width=2,
        )

        c.create_oval(cx - 14, cy - 14, cx + 14, cy + 14,
                      fill="#0d0f14", outline=ACCENT, width=2)
        c.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                      fill=ACCENT, outline="")


def main() -> None:
    app = WheelApp()
    app.mainloop()


if __name__ == "__main__":
    main()
