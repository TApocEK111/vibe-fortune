"""
Wheel of Fortune — простое колесо фортуны с GUI.

Запуск: python wheel_of_fortune.py

Импорт вариантов — три способа:

1) Файл (кнопка «Импорт вариантов…»):
   Формат CSV: <название>[<разделитель><вес>], разделитель — ',' или ';'.
   Кодировка UTF-8. Пустые строки и '#' — комментарии.

2) CSV-вставка (кнопка «Импорт CSV (вставить)»):
   Вставьте строки в текстовое поле:
       Джекпот, 1
       Приз 1, 3
       Приз 2;3
       Пусто
       Мелочь, 20
   Вес можно опустить — тогда он равен 1.
   Разделитель — ',' или ';' (в одной строке — один тип).

3) Двухшаговый импорт (кнопка «Импорт 2 шага»):
   Шаг 1: список названий, по одному в строке.
   Шаг 2: список весов, по одному в строке.
   Количество строк должно СОВПАДАТЬ, иначе — ошибка
   с указанием фактических количеств.

Режим на выбывание — глобальный: если включён, любой выпавший
вариант удаляется из колеса (пока не останется один — он победитель).
"""

from __future__ import annotations

import math
import random
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk


# ---------------------------------------------------------------------------
# Модель данных
# ---------------------------------------------------------------------------

@dataclass
class Option:
    name: str
    weight: float


class Wheel:
    """Колесо с весами. Гарантирует корректное вероятностное распределение."""

    def __init__(self) -> None:
        self.options: list[Option] = []
        self._sectors: list[tuple[Option, float, float]] = []

    def set_options(self, options: list[Option]) -> None:
        if not options:
            self.options = []
            self._sectors = []
            return
        clean = [o for o in options if o.weight > 0 and math.isfinite(o.weight)]
        if not clean:
            raise ValueError("Все веса неположительны или бесконечны.")
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
# Парсер импорта (единые правила для всех сценариев)
# ---------------------------------------------------------------------------

class ImportParser:
    """Разбор текстовых данных импорта. Все ошибки — ValueError с номером строки."""

    DEFAULT_WEIGHT = 1.0

    @classmethod
    def _parse_weight(cls, token: str, lineno: int) -> float:
        token = token.strip().replace(",", ".")
        try:
            w = float(token)
        except ValueError:
            raise ValueError(f"Строка {lineno}: вес '{token}' — не число.")
        if not math.isfinite(w) or w <= 0:
            raise ValueError(f"Строка {lineno}: вес должен быть > 0.")
        return w

    @classmethod
    def parse_csv(cls, text: str) -> list[Option]:
        """
        Разбор CSV-подобного текста.
        Строка: <название>[<sep><вес>], sep = ',' или ';'.
        Вес опционален (по умолчанию 1). Название не может быть пустым.
        """
        options: list[Option] = []
        for lineno, raw in enumerate(text.splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            # Выбираем разделитель: ';' приоритетнее, т.к. ',' может быть в названии.
            if ";" in line:
                parts = [p.strip() for p in line.split(";", 1)]
            elif "," in line:
                parts = [p.strip() for p in line.split(",", 1)]
            else:
                parts = [line]

            name = parts[0]
            if not name:
                raise ValueError(f"Строка {lineno}: пустое название.")

            weight = cls.DEFAULT_WEIGHT
            if len(parts) == 2 and parts[1] != "":
                weight = cls._parse_weight(parts[1], lineno)

            options.append(Option(name, weight))

        if not options:
            raise ValueError("Нет ни одного варианта.")
        return options

    @classmethod
    def parse_two_step(cls, names_text: str, weights_text: str) -> list[Option]:
        """
        Двухшаговый импорт: список названий + список весов, построчно.
        Количество строк обязано совпадать.
        """
        names = [ln.strip() for ln in names_text.splitlines() if ln.strip()]
        weights_raw = [ln.strip() for ln in weights_text.splitlines() if ln.strip()]

        if len(names) != len(weights_raw):
            raise ValueError(
                "Количество строк не сходится:\n"
                f"  названий: {len(names)}\n"
                f"  весов:    {len(weights_raw)}\n"
                "Списки должны быть одинаковой длины."
            )
        if not names:
            raise ValueError("Нет ни одного варианта.")

        options: list[Option] = []
        for i, (name, w_raw) in enumerate(zip(names, weights_raw), 1):
            # Вес может содержать только число; запятая как десятичный разделитель — ок.
            weight = cls._parse_weight(w_raw, i)
            options.append(Option(name, weight))
        return options


# ---------------------------------------------------------------------------
# Диалоги импорта
# ---------------------------------------------------------------------------

class TextImportDialog(tk.Toplevel):
    """Модальное окно с одним или двумя текстовыми полями."""

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        fields: list[tuple[str, str]],   # [(заголовок, подсказка)]
        on_submit,                       # (list[str]) -> list[Option] | None
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
        # Кнопки создаём ПОСЛЕ полей — но фокус всё равно принудительно
        # переведём на первое поле в конце __init__.
        ttk.Button(btn_row, text="Отмена",
                   command=self.destroy).pack(side=tk.RIGHT)
        ttk.Button(btn_row, text="Импортировать",
                   command=self._submit).pack(side=tk.RIGHT, padx=(0, 8))

        self.bind("<Escape>", lambda _e: self.destroy())
        self.grab_set()
        self._center_on(parent)

        # --- ключевые исправления фокуса ---
        # 1) Окно должно получить фокус клавиатуры.
        self.focus_force()
        # 2) Первое поле — целевой виджет ввода.
        if self._texts:
            first = self._texts[0]
            first.focus_set()
            # 3) На некоторых WM фокус «съезжает» после появления окна —
            #    повторяем через короткую задержку.
            self.after_idle(lambda: first.focus_set())

    # --- горячие клавиши для Text: Ctrl+V / Ctrl+C / Ctrl+X / Cmd+V на macOS ---
    def _bind_text_shortcuts(self, txt: tk.Text) -> None:
        # Явные привязки — не полагаемся на дефолт tkinter.
        txt.bind("<Control-v>", lambda _e: (txt.event_generate("<<Paste>>"), "break")[1])
        txt.bind("<Control-V>", lambda _e: (txt.event_generate("<<Paste>>"), "break")[1])
        txt.bind("<Control-c>", lambda _e: (txt.event_generate("<<Copy>>"), "break")[1])
        txt.bind("<Control-C>", lambda _e: (txt.event_generate("<<Copy>>"), "break")[1])
        txt.bind("<Control-x>", lambda _e: (txt.event_generate("<<Cut>>"), "break")[1])
        txt.bind("<Control-X>", lambda _e: (txt.event_generate("<<Cut>>"), "break")[1])
        txt.bind("<Control-a>", self._select_all)
        txt.bind("<Control-A>", self._select_all)
        # macOS: Command вместо Control
        txt.bind("<Command-v>", lambda _e: (txt.event_generate("<<Paste>>"), "break")[1])
        txt.bind("<Command-c>", lambda _e: (txt.event_generate("<<Copy>>"), "break")[1])
        txt.bind("<Command-x>", lambda _e: (txt.event_generate("<<Cut>>"), "break")[1])
        txt.bind("<Command-a>", self._select_all)
        # Правый клик — контекстное меню «Вставить».
        txt.bind("<Button-3>", self._on_right_click)
        txt.bind("<Button-2>", self._on_right_click)  # macOS иногда Button-2
        # Возврат фокуса при клике в поле — на всякий случай.
        txt.bind("<Button-1>", lambda _e: txt.focus_set(), add="+")

    @staticmethod
    def _select_all(event):
        event.widget.tag_add("sel", "1.0", "end-1c")
        return "break"

    def _on_right_click(self, event) -> str:
        txt = event.widget
        menu = tk.Menu(txt, tearoff=0, bg="#2c3140", fg=FG,
                       activebackground="#3d4457", activeforeground=FG)
        try:
            has_sel = bool(txt.get("sel.first", "sel.last"))
        except tk.TclError:
            has_sel = False
        menu.add_command(label="Вставить",
                         command=lambda: txt.event_generate("<<Paste>>"))
        menu.add_command(label="Копировать",
                         state=("normal" if has_sel else "disabled"),
                         command=lambda: txt.event_generate("<<Copy>>"))
        menu.add_command(label="Вырезать",
                         state=("normal" if has_sel else "disabled"),
                         command=lambda: txt.event_generate("<<Cut>>"))
        menu.add_separator()
        menu.add_command(label="Выделить всё",
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
            messagebox.showerror("Ошибка импорта", str(e), parent=self)
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
        self.title("Колесо Фортуны")
        self.geometry("1100x760")
        self.configure(bg=BG)
        self.minsize(900, 640)

        self.wheel = Wheel()
        self._original_options: list[Option] = []
        self._spinning = False
        self._angle = 0.0

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

        left = ttk.Frame(self, padding=12)
        left.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left, text="Колесо Фортуны",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Separator(left).pack(fill=tk.X, pady=8)

        ttk.Label(left, text="Время прокрутки (сек):").pack(anchor="w")
        self.duration_var = tk.DoubleVar(value=4.0)
        ttk.Entry(left, textvariable=self.duration_var, width=10).pack(
            anchor="w", pady=(2, 10))

        self.eliminate_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            left,
            text="Режим на выбывание\n(выпавший вариант удаляется)",
            variable=self.eliminate_var,
        ).pack(anchor="w", pady=(0, 10))

        # --- импорт ---
        ttk.Label(left, text="Импорт:",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Button(left, text="📥 Из файла…",
                   command=self._import_file).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="📋 CSV — вставить текст…",
                   command=self._import_csv_paste).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="🧮 Два шага: позиции + веса…",
                   command=self._import_two_step).pack(fill=tk.X, pady=2)

        ttk.Separator(left).pack(fill=tk.X, pady=10)

        ttk.Button(left, text="💾 Загрузить пример",
                   command=self._load_default).pack(fill=tk.X, pady=2)
        ttk.Button(left, text="♻ Восстановить выбывших",
                   command=self._reset_eliminated).pack(fill=tk.X, pady=2)

        ttk.Separator(left).pack(fill=tk.X, pady=10)

        self.spin_btn = tk.Button(
            left,
            text="🎡 КРУТИТЬ",
            font=("Segoe UI", 16, "bold"),
            bg=ACCENT, fg="#1b1f2a",
            activebackground="#ffdd66",
            relief="flat",
            command=self._spin,
        )
        self.spin_btn.pack(fill=tk.X, ipady=8, pady=(0, 10))

        self.result_var = tk.StringVar(value="—")
        ttk.Label(left, text="Результат:").pack(anchor="w")
        self.result_label = tk.Label(
            left, textvariable=self.result_var,
            font=("Segoe UI", 15, "bold"),
            bg="#2c3140", fg=ACCENT,
            wraplength=240, justify="left", anchor="w",
            padx=8, pady=8,
        )
        self.result_label.pack(fill=tk.X, pady=(2, 10))

        ttk.Label(left, text="Варианты (вероятность):").pack(anchor="w")
        self.listbox = tk.Listbox(
            left, height=10,
            bg="#2c3140", fg=FG, selectbackground="#3d4457",
            relief="flat", borderwidth=0, activestyle="none",
        )
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=(2, 4))

        self.stats_var = tk.StringVar(value="")
        ttk.Label(left, textvariable=self.stats_var,
                  foreground="#9aa4b8").pack(anchor="w")

        right = ttk.Frame(self, padding=12)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(right, bg=BG, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda _e: self._draw())

        self._load_default()

    # ------------------------------------------------------------- импорты ---
    def _import_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Импорт вариантов",
            filetypes=[("CSV/текст", "*.csv *.txt"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                text = f.read()
            options = ImportParser.parse_csv(text)
        except Exception as e:
            messagebox.showerror("Ошибка импорта", str(e))
            return
        self._apply_options(options)

    def _import_csv_paste(self) -> None:
        dlg = TextImportDialog(
            self,
            title="Импорт CSV — вставьте строки",
            fields=[(
                "Строки вариантов",
                "Формат: <название>,<вес>  или  <название>;<вес>.\n"
                "Вес можно опустить — тогда 1. Разделитель — ',' или ';'."
            )],
            on_submit=lambda texts: ImportParser.parse_csv(texts[0]),
        )
        dlg._on_result = self._apply_options  # type: ignore[method-assign]
        self.wait_window(dlg)

    def _import_two_step(self) -> None:
        dlg = TextImportDialog(
            self,
            title="Импорт в два шага",
            fields=[
                ("Шаг 1. Позиции (по одной в строке)",
                 "Например:\nДжекпот\nПриз 1\nПусто"),
                ("Шаг 2. Веса (по одному в строке)",
                 "Количество строк должно совпадать с шагом 1.\nНапример:\n1\n3\n10"),
            ],
            on_submit=lambda texts: ImportParser.parse_two_step(texts[0], texts[1]),
        )
        dlg._on_result = self._apply_options  # type: ignore[method-assign]
        self.wait_window(dlg)

    # ------------------------------------------------------------- загрузка ---
    def _load_default(self) -> None:
        defaults = [
            ("Джекпот", 1.0),
            ("Приз 1", 3.0),
            ("Приз 2", 3.0),
            ("Пусто", 10.0),
            ("Мелочь", 20.0),
            ("Утешительный", 5.0),
        ]
        self._apply_options([Option(n, w) for n, w in defaults])

    def _apply_options(self, options: list[Option]) -> None:
        try:
            self.wheel.set_options(options)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return
        self._original_options = [Option(o.name, o.weight) for o in self.wheel.options]
        self._angle = 0.0
        self._spinning = False
        self.spin_btn.config(state=tk.NORMAL)
        self.result_var.set("—")
        self._refresh_list()
        self._draw()

    def _refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        total = self.wheel.total_weight() or 1.0
        for o in self.wheel.options:
            p = 100.0 * o.weight / total
            self.listbox.insert(tk.END, f"  {o.name}  —  {p:.2f}%")
        self.stats_var.set(
            f"Осталось: {len(self.wheel.options)} вар.  |  Σвес = {total:.3f}"
        )

    def _reset_eliminated(self) -> None:
        if not self._original_options:
            return
        self._apply_options([Option(o.name, o.weight) for o in self._original_options])
        self.result_var.set("—")

    # --------------------------------------------------------------- спин ---
    def _spin(self) -> None:
        if self._spinning or not self.wheel.options:
            return
        try:
            duration = float(self.duration_var.get())
        except (ValueError, tk.TclError):
            messagebox.showerror("Ошибка", "Время прокрутки должно быть числом.")
            return
        if not (0.05 <= duration <= 120):
            messagebox.showerror("Ошибка", "Время прокрутки — от 0.05 до 120 секунд.")
            return

        self._spinning = True
        self.spin_btn.config(state=tk.DISABLED)
        self.result_var.set("…")

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

        self._animate()

    def _animate(self) -> None:
        if not self._spinning:
            return
        t = time.perf_counter() - self._spin_t0
        p = min(1.0, t / self._spin_duration)
        eased = 1.0 - (1.0 - p) ** 3
        self._angle = self._spin_start + self._spin_delta * eased
        self._draw()
        if p < 1.0:
            self.after(16, self._animate)
        else:
            self._finish_spin()

    def _finish_spin(self) -> None:
        self._spinning = False
        self._angle = (self._spin_start + self._spin_delta) % 360.0
        self._draw()

        winner = self.wheel.options[self._target_index]
        self.result_var.set(winner.name)

        if self.eliminate_var.get() and len(self.wheel.options) > 1:
            self.wheel.eliminate(winner)
            self._refresh_list()
            self._draw()
            self.result_var.set(f"{winner.name}\n(выбыл)")
            if len(self.wheel.options) == 1:
                last = self.wheel.options[0]
                self.result_var.set(
                    f"{winner.name}\n(выбыл)\n\n🏆 Победитель: {last.name}"
                )

        self.spin_btn.config(state=tk.NORMAL)

    # -------------------------------------------------------------- отрисовка ---
    def _draw(self) -> None:
        c = self.canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10 or h < 10:
            return

        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 30
        if r <= 0:
            return

        sectors = self.wheel.sectors()
        if not sectors:
            c.create_text(cx, cy, text="Нет вариантов",
                          fill=FG, font=("Segoe UI", 16))
            return

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
