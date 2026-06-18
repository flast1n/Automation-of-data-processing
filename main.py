"""
main.py — АРМ Оператора АТ «Укрпошта».
Запуск: python main.py
"""

import customtkinter as ctk
import tkinter as tk

import database as db

# ─── Тема ────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

C_YELLOW   = "#FFD700"
C_YELLOW_H = "#FFC200"
C_DARK     = "#1A1A2E"
C_SIDEBAR  = "#1C2B4A"
C_SIDEBAR2 = "#253857"
C_WHITE    = "#FFFFFF"
C_BG       = "#F4F6FA"
C_TEXT     = "#1A1A2E"
C_MUTED    = "#6B7A99"
C_SUCCESS  = "#27AE60"
C_ERROR    = "#E74C3C"
C_BORDER   = "#DDE3EE"
C_ADMIN    = "#8E44AD"
C_OPER     = "#2980B9"


# ════════════════════════════════════════════════════════════════════════════
#  Допоміжні віджети
# ════════════════════════════════════════════════════════════════════════════

class ClipboardEntry(ctk.CTkEntry):
    """
    CTkEntry з контекстним меню (правий клік):
    Вставити / Копіювати / Вирізати / Очистити.
    """

    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        inner = getattr(self, "_entry", self)
        inner.bind("<Button-3>", self._show_menu)

    def _show_menu(self, event):
        menu = tk.Menu(
            self, tearoff=0, bg="white", fg=C_TEXT,
            font=("Helvetica", 11), relief="flat",
            activebackground=C_YELLOW, activeforeground=C_DARK,
        )
        menu.add_command(label="  📋  Вставити       Ctrl+V",
                         command=self._paste)
        menu.add_command(label="  📄  Копіювати      Ctrl+C",
                         command=self._copy)
        menu.add_command(label="  ✂️   Вирізати        Ctrl+X",
                         command=self._cut)
        menu.add_separator()
        menu.add_command(label="  ✖   Очистити поле",
                         command=lambda: self.delete(0, "end"))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _paste(self, _=None):
        try:
            text = self.clipboard_get()
        except tk.TclError:
            return
        inner = getattr(self, "_entry", self)
        try:
            s = inner.index(tk.SEL_FIRST)
            e = inner.index(tk.SEL_LAST)
            self.delete(s, e)
        except tk.TclError:
            pass
        self.insert(inner.index(tk.INSERT), text)

    def _copy(self, _=None):
        inner = getattr(self, "_entry", self)
        try:
            self.clipboard_clear()
            self.clipboard_append(inner.selection_get())
        except tk.TclError:
            pass

    def _cut(self, _=None):
        self._copy()
        inner = getattr(self, "_entry", self)
        try:
            self.delete(inner.index(tk.SEL_FIRST),
                        inner.index(tk.SEL_LAST))
        except tk.TclError:
            pass


class FieldEntry(ClipboardEntry):
    """Стилізоване поле вводу."""
    def __init__(self, master, placeholder="", width=280, **kw):
        super().__init__(
            master, placeholder_text=placeholder,
            width=width, height=38, corner_radius=8,
            border_color=C_BORDER, fg_color=C_WHITE,
            text_color=C_TEXT, font=ctk.CTkFont("Helvetica", 13),
            **kw,
        )


class PrimaryButton(ctk.CTkButton):
    def __init__(self, master, text, command=None, width=160, **kw):
        super().__init__(
            master, text=text, command=command,
            width=width, height=42, corner_radius=10,
            fg_color=C_YELLOW, hover_color=C_YELLOW_H,
            text_color=C_DARK, font=ctk.CTkFont("Helvetica", 13, "bold"),
            **kw,
        )


class StatusCard(ctk.CTkFrame):
    def __init__(self, master, success=True, **kw):
        super().__init__(
            master, fg_color=C_WHITE,
            border_color=C_SUCCESS if success else C_ERROR,
            border_width=2, corner_radius=12, **kw,
        )

    def set_text(self, lines: list[tuple[str, str]]):
        for w in self.winfo_children():
            w.destroy()
        for label, value in lines:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(row, text=label, width=160, anchor="w",
                         font=ctk.CTkFont("Helvetica", 12),
                         text_color=C_MUTED).pack(side="left")
            ctk.CTkLabel(row, text=value, anchor="w",
                         font=ctk.CTkFont("Helvetica", 13, "bold"),
                         text_color=C_TEXT).pack(side="left", padx=(4, 0))


# ════════════════════════════════════════════════════════════════════════════
#  Панелі (сторінки)
# ════════════════════════════════════════════════════════════════════════════

class TrackingPanel(ctk.CTkFrame):
    """Блок 1 — Пошук посилки за трек-номером."""

    def __init__(self, master, current_user: dict, **kw):
        super().__init__(master, fg_color=C_BG, **kw)
        self._user = current_user
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="🔍  Трекінг посилки",
                     font=ctk.CTkFont("Helvetica", 22, "bold"),
                     text_color=C_DARK).pack(anchor="w", padx=32, pady=(28, 4))
        ctk.CTkLabel(
            self,
            text="Введіть 13-значний трек-номер, щоб дізнатись інформацію про відправлення",
            font=ctk.CTkFont("Helvetica", 13),
            text_color=C_MUTED,
        ).pack(anchor="w", padx=32, pady=(0, 20))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(anchor="w", padx=32, pady=(0, 20))
        self.entry = FieldEntry(row, placeholder="0500041234567", width=320)
        self.entry.pack(side="left", padx=(0, 12))
        self.entry.bind("<Return>", lambda e: self._search())
        PrimaryButton(row, "Знайти", command=self._search, width=120).pack(side="left")

        self.result_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.result_frame.pack(fill="x", padx=32)

    def _search(self):
        track = self.entry.get().strip()
        if len(track) != 13 or not track.isdigit():
            self._display(False, [("", "⚠️  Трек-номер має містити рівно 13 цифр")])
            return

        parcel = db.find_parcel(track)

        if parcel is None:
            db.log_action(self._user["user_id"],
                          "Пошук посилки — не знайдено", f"Трек: {track}")
            self._display(False, [("", f"❌  Посилку «{track}» не знайдено в базі")])
            return

        db.log_action(self._user["user_id"],
                      "Пошук посилки — знайдено", f"Трек: {track}")
        icon = {"Укрпошта Експрес": "⚡", "Укрпошта Стандарт": "📦"}.get(
            parcel["delivery_type"], "📮"
        )
        self._display(True, [
            ("✅  Посилка знайдена!", ""),
            ("Трек-номер:",    parcel["track_number"]),
            ("Тип доставки:",  f"{icon}  {parcel['delivery_type']}"),
            ("Вага:",          f"{parcel['weight']} кг"),
            ("Вартість:",      f"{parcel['price']} грн"),
            ("Відправник:",    parcel["sender_name"]),
            ("Тел. відпр.:",   parcel["sender_phone"]),
            ("Отримувач:",     parcel["receiver_name"]),
            ("Тел. отрим.:",   parcel["receiver_phone"]),
            ("Оформив:",       parcel["employee_name"]),
        ])

    def _display(self, success: bool, lines: list[tuple[str, str]]):
        for w in self.result_frame.winfo_children():
            w.destroy()
        card = StatusCard(self.result_frame, success=success)
        card.pack(fill="x", pady=4)
        card.set_text(lines)


# ─────────────────────────────────────────────────────────────────────────────

class RegisterPanel(ctk.CTkFrame):
    """Блок 2 — Реєстрація нового відправлення."""

    DELIVERY_TYPES = [
        "Укрпошта Стандарт",
        "Укрпошта Експрес",
        "Укрпошта Першокласна",
    ]

    def __init__(self, master, current_user: dict, **kw):
        super().__init__(master, fg_color=C_BG, **kw)
        self._user      = current_user
        self._employees = db.get_employees()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="📦  Реєстрація відправлення",
                     font=ctk.CTkFont("Helvetica", 22, "bold"),
                     text_color=C_DARK).pack(anchor="w", padx=32, pady=(28, 4))
        ctk.CTkLabel(self, text="Заповніть дані клієнтів та параметри посилки",
                     font=ctk.CTkFont("Helvetica", 13),
                     text_color=C_MUTED).pack(anchor="w", padx=32, pady=(0, 20))

        cols = ctk.CTkFrame(self, fg_color="transparent")
        cols.pack(anchor="w", padx=32, fill="x")

        left  = ctk.CTkFrame(cols, fg_color="transparent")
        left.pack(side="left", anchor="n", padx=(0, 32))
        right = ctk.CTkFrame(cols, fg_color="transparent")
        right.pack(side="left", anchor="n")

        # ── Ліворуч ──────────────────────────────────────────────────────
        ctk.CTkLabel(left, text="ВІДПРАВНИК",
                     font=ctk.CTkFont("Helvetica", 11, "bold"),
                     text_color=C_MUTED).pack(anchor="w", pady=(0, 6))
        self.e_sender_name  = self._field(left, "ПІБ відправника")
        self.e_sender_phone = self._field(left, "+380XXXXXXXXX")

        ctk.CTkLabel(left, text="ОТРИМУВАЧ",
                     font=ctk.CTkFont("Helvetica", 11, "bold"),
                     text_color=C_MUTED).pack(anchor="w", pady=(16, 6))
        self.e_recv_name  = self._field(left, "ПІБ отримувача")
        self.e_recv_phone = self._field(left, "+380XXXXXXXXX")

        # ── Праворуч ─────────────────────────────────────────────────────
        ctk.CTkLabel(right, text="ПАРАМЕТРИ ПОСИЛКИ",
                     font=ctk.CTkFont("Helvetica", 11, "bold"),
                     text_color=C_MUTED).pack(anchor="w", pady=(0, 6))
        self.e_weight = self._field(right, "Вага (кг), напр. 2.5")
        self.e_price  = self._field(right, "Вартість (грн), напр. 65.00")

        ctk.CTkLabel(right, text="Тип доставки",
                     font=ctk.CTkFont("Helvetica", 12),
                     text_color=C_MUTED).pack(anchor="w", pady=(10, 4))
        self.delivery_var = ctk.StringVar(value=self.DELIVERY_TYPES[0])
        ctk.CTkOptionMenu(
            right, values=self.DELIVERY_TYPES,
            variable=self.delivery_var,
            width=280, height=38, corner_radius=8,
            fg_color=C_WHITE, button_color=C_YELLOW,
            button_hover_color=C_YELLOW_H,
            text_color=C_TEXT, font=ctk.CTkFont("Helvetica", 13),
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(right, text="Оператор",
                     font=ctk.CTkFont("Helvetica", 12),
                     text_color=C_MUTED).pack(anchor="w", pady=(2, 4))

        emp_labels = [f"{e['fullname']} ({e['position']})"
                      for e in self._employees]
        is_admin   = self._user["role"] == "admin"

        default = emp_labels[0] if emp_labels else ""
        if not is_admin and self._user.get("employee_id"):
            emp = next(
                (e for e in self._employees
                 if e["employee_id"] == self._user["employee_id"]), None
            )
            if emp:
                default = f"{emp['fullname']} ({emp['position']})"

        self.employee_var = ctk.StringVar(value=default)
        ctk.CTkOptionMenu(
            right, values=emp_labels,
            variable=self.employee_var,
            width=280, height=38, corner_radius=8,
            fg_color=C_WHITE if is_admin else "#EFEFEF",
            button_color=C_YELLOW if is_admin else C_MUTED,
            button_hover_color=C_YELLOW_H if is_admin else C_MUTED,
            text_color=C_TEXT, font=ctk.CTkFont("Helvetica", 13),
            state="normal" if is_admin else "disabled",
        ).pack(anchor="w")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(anchor="w", padx=32, pady=20)
        PrimaryButton(btn_row, "✅  Оформити посилку",
                      command=self._submit, width=220).pack(side="left")

        self.result_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.result_frame.pack(fill="x", padx=32)

    @staticmethod
    def _field(parent, placeholder) -> FieldEntry:
        e = FieldEntry(parent, placeholder=placeholder, width=280)
        e.pack(anchor="w", pady=4)
        return e

    def _submit(self):
        s_name  = self.e_sender_name.get().strip()
        s_phone = self.e_sender_phone.get().strip()
        r_name  = self.e_recv_name.get().strip()
        r_phone = self.e_recv_phone.get().strip()

        errors = []
        if not s_name:  errors.append("ПІБ відправника")
        if not s_phone: errors.append("Телефон відправника")
        if not r_name:  errors.append("ПІБ отримувача")
        if not r_phone: errors.append("Телефон отримувача")

        weight = price = 0.0
        try:
            weight = float(self.e_weight.get())
            assert weight > 0
        except (ValueError, AssertionError):
            errors.append("Вага (число > 0)")
        try:
            price = float(self.e_price.get())
            assert price > 0
        except (ValueError, AssertionError):
            errors.append("Вартість (число > 0)")

        if errors:
            self._feedback(False, f"Заповніть поля: {', '.join(errors)}")
            return

        emp_labels = [f"{e['fullname']} ({e['position']})"
                      for e in self._employees]
        emp_id = self._employees[
            emp_labels.index(self.employee_var.get())
        ]["employee_id"]

        try:
            track = db.register_parcel(
                s_name, s_phone, r_name, r_phone,
                weight, price, self.delivery_var.get(), emp_id,
            )
            db.log_action(
                self._user["user_id"], "Реєстрація посилки",
                f"Трек: {track} | Відправник: {s_name} | "
                f"Вага: {weight} кг | {self.delivery_var.get()}",
            )
            self._feedback(True,
                           f"Посилку успішно оформлено!\nТрек-номер: {track}")
            for e in [self.e_sender_name, self.e_sender_phone,
                      self.e_recv_name,   self.e_recv_phone,
                      self.e_weight,      self.e_price]:
                e.delete(0, "end")
        except Exception as exc:
            self._feedback(False, f"Помилка бази даних: {exc}")

    def _feedback(self, success: bool, msg: str):
        for w in self.result_frame.winfo_children():
            w.destroy()
        card  = StatusCard(self.result_frame, success=success)
        card.pack(fill="x", pady=4)
        color = C_SUCCESS if success else C_ERROR
        icon  = "✅" if success else "❌"
        for line in f"{icon}  {msg}".split("\n"):
            ctk.CTkLabel(
                card, text=line, anchor="w",
                font=ctk.CTkFont("Helvetica", 13,
                                 "bold" if success else "normal"),
                text_color=color,
            ).pack(anchor="w", padx=16, pady=3)


# ─────────────────────────────────────────────────────────────────────────────

class AdminPanel(ctk.CTkFrame):
    """Блок 3 — Адмін-панель / Звіти."""

    def __init__(self, master, current_user: dict, **kw):
        super().__init__(master, fg_color=C_BG, **kw)
        self._user = current_user
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="📊  Адмін-панель  /  Звіти",
                     font=ctk.CTkFont("Helvetica", 22, "bold"),
                     text_color=C_DARK).pack(anchor="w", padx=32, pady=(28, 4))
        ctk.CTkLabel(self, text="Оперативна статистика по відділенню",
                     font=ctk.CTkFont("Helvetica", 13),
                     text_color=C_MUTED).pack(anchor="w", padx=32, pady=(0, 20))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(anchor="w", padx=32, pady=(0, 16))
        PrimaryButton(btn_row, "💰  Звіт по касі",
                      command=self._cashier, width=180).pack(
            side="left", padx=(0, 12))
        PrimaryButton(btn_row, "👷  Ефективність",
                      command=self._efficiency, width=180).pack(
            side="left", padx=(0, 12))
        PrimaryButton(btn_row, "📋  Всі посилки",
                      command=self._all_parcels, width=180).pack(side="left")

        self.tbl = ctk.CTkScrollableFrame(
            self, fg_color=C_WHITE, corner_radius=12,
            border_width=1, border_color=C_BORDER,
        )
        self.tbl.pack(fill="both", expand=True, padx=32, pady=(0, 20))

    def _render(self, title: str, headers: list, rows: list):
        for w in self.tbl.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.tbl, text=title,
                     font=ctk.CTkFont("Helvetica", 15, "bold"),
                     text_color=C_DARK).pack(anchor="w", padx=12, pady=(12, 8))

        if not rows:
            ctk.CTkLabel(self.tbl, text="Даних немає",
                         font=ctk.CTkFont("Helvetica", 13),
                         text_color=C_MUTED).pack(pady=12)
            return

        cw = max(80, 700 // len(headers))

        h_row = ctk.CTkFrame(self.tbl, fg_color=C_SIDEBAR, corner_radius=8)
        h_row.pack(fill="x", padx=8, pady=(0, 4))
        for h in headers:
            ctk.CTkLabel(h_row, text=h, anchor="w", width=cw,
                         font=ctk.CTkFont("Helvetica", 11, "bold"),
                         text_color=C_WHITE).pack(side="left", padx=10, pady=7)

        for i, row in enumerate(rows):
            bg = C_WHITE if i % 2 == 0 else "#F0F3F9"
            d = ctk.CTkFrame(self.tbl, fg_color=bg, corner_radius=6)
            d.pack(fill="x", padx=8, pady=1)
            for cell in row:
                ctk.CTkLabel(d,
                             text=str(cell) if cell is not None else "—",
                             anchor="w", width=cw,
                             font=ctk.CTkFont("Helvetica", 12),
                             text_color=C_TEXT).pack(
                    side="left", padx=10, pady=6)

    def _cashier(self):
        db.log_action(self._user["user_id"], "Перегляд звіту", "Каса")
        data = db.report_cashier()
        self._render("💰  Звіт по касі",
                     ["Співробітник", "Посада", "Посилок", "Сума (грн)"],
                     [[d["employee_name"], d["position"],
                       d["parcel_count"], d["total_sum"]] for d in data])

    def _efficiency(self):
        db.log_action(self._user["user_id"], "Перегляд звіту", "Ефективність")
        data = db.report_efficiency()
        self._render(
            "👷  Ефективність",
            ["Співробітник", "Посада", "Посилок",
             "Сер. вага", "Сума", "Сер. ціна"],
            [[d["employee_name"], d["position"], d["parcel_count"],
              d["avg_weight"], d["total_sum"], d["avg_price"]]
             for d in data],
        )

    def _all_parcels(self):
        db.log_action(self._user["user_id"], "Перегляд звіту", "Всі посилки")
        data = db.report_all_parcels()
        self._render(
            "📋  Всі посилки",
            ["ID", "Трек-номер", "Відправник", "Отримувач",
             "Вага", "Ціна", "Тип", "Оператор"],
            [[d["parcel_id"], d["track_number"], d["sender"], d["receiver"],
              f"{d['weight']} кг", f"{d['price']} грн",
              d["delivery_type"], d["employee"]] for d in data],
        )


# ─────────────────────────────────────────────────────────────────────────────

class LogPanel(ctk.CTkFrame):
    """Журнал дій — тільки для адміністратора."""

    def __init__(self, master, current_user: dict, **kw):
        super().__init__(master, fg_color=C_BG, **kw)
        self._user = current_user
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=32, pady=(28, 0))
        ctk.CTkLabel(hdr, text="📜  Журнал дій",
                     font=ctk.CTkFont("Helvetica", 22, "bold"),
                     text_color=C_DARK).pack(side="left")
        PrimaryButton(hdr, "🔄  Оновити",
                      command=self._load, width=130).pack(side="right")

        ctk.CTkLabel(
            self,
            text="Всі дії операторів та адміністратора в системі (останні 300)",
            font=ctk.CTkFont("Helvetica", 13),
            text_color=C_MUTED,
        ).pack(anchor="w", padx=32, pady=(4, 16))

        self.tbl = ctk.CTkScrollableFrame(
            self, fg_color=C_WHITE, corner_radius=12,
            border_width=1, border_color=C_BORDER,
        )
        self.tbl.pack(fill="both", expand=True, padx=32, pady=(0, 20))
        self._load()

    def _load(self):
        for w in self.tbl.winfo_children():
            w.destroy()

        logs       = db.get_logs()
        headers    = ["#",  "Час", "Користувач", "Роль", "Дія",  "Деталі"]
        col_widths = [40,   140,   110,           80,     160,    300]

        h_row = ctk.CTkFrame(self.tbl, fg_color=C_SIDEBAR, corner_radius=8)
        h_row.pack(fill="x", padx=8, pady=(8, 4))
        for h, w in zip(headers, col_widths):
            ctk.CTkLabel(h_row, text=h, anchor="w", width=w,
                         font=ctk.CTkFont("Helvetica", 11, "bold"),
                         text_color=C_WHITE).pack(side="left", padx=8, pady=7)

        if not logs:
            ctk.CTkLabel(self.tbl, text="Журнал порожній",
                         font=ctk.CTkFont("Helvetica", 13),
                         text_color=C_MUTED).pack(pady=20)
            return

        for i, log in enumerate(logs):
            bg         = C_WHITE if i % 2 == 0 else "#F0F3F9"
            role_color = C_ADMIN if log.get("role") == "admin" else C_OPER
            values     = [
                str(log["log_id"]),
                log["timestamp"] or "",
                log["username"]  or "—",
                log["role"]      or "—",
                log["action"],
                log["details"]   or "",
            ]
            colors = [C_MUTED, C_MUTED, C_TEXT, role_color, C_TEXT, C_MUTED]

            d = ctk.CTkFrame(self.tbl, fg_color=bg, corner_radius=6)
            d.pack(fill="x", padx=8, pady=1)
            for val, w, color in zip(values, col_widths, colors):
                ctk.CTkLabel(d, text=str(val), anchor="w", width=w,
                             font=ctk.CTkFont("Helvetica", 11),
                             text_color=color).pack(side="left", padx=8, pady=5)


# ════════════════════════════════════════════════════════════════════════════
#  Вікно входу
# ════════════════════════════════════════════════════════════════════════════

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Укрпошта — Вхід в систему")
        self.geometry("460x580")
        self.resizable(False, False)
        self.configure(fg_color=C_BG)
        self.current_user: dict | None = None
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 460) // 2
        y = (self.winfo_screenheight() - 580) // 2
        self.geometry(f"460x580+{x}+{y}")

    def _build(self):
        # Шапка
        banner = ctk.CTkFrame(self, fg_color=C_SIDEBAR,
                              corner_radius=0, height=100)
        banner.pack(fill="x")
        banner.pack_propagate(False)
        ctk.CTkLabel(banner, text="📮",
                     font=ctk.CTkFont("Helvetica", 40)).place(
            relx=0.28, rely=0.5, anchor="center")
        ctk.CTkLabel(banner, text="УКРПОШТА",
                     font=ctk.CTkFont("Helvetica", 24, "bold"),
                     text_color=C_YELLOW).place(
            relx=0.63, rely=0.36, anchor="center")
        ctk.CTkLabel(banner, text="АРМ Оператора відділення",
                     font=ctk.CTkFont("Helvetica", 11),
                     text_color="#8DA0BB").place(
            relx=0.63, rely=0.68, anchor="center")

        # Картка
        card = ctk.CTkFrame(self, fg_color=C_WHITE, corner_radius=16,
                            border_width=1, border_color=C_BORDER)
        card.pack(padx=36, pady=22, fill="x")

        ctk.CTkLabel(card, text="Вхід в систему",
                     font=ctk.CTkFont("Helvetica", 18, "bold"),
                     text_color=C_DARK).pack(pady=(22, 2))
        ctk.CTkLabel(card, text="Введіть ваші облікові дані",
                     font=ctk.CTkFont("Helvetica", 12),
                     text_color=C_MUTED).pack(pady=(0, 18))

        ctk.CTkLabel(card, text="Логін", anchor="w",
                     font=ctk.CTkFont("Helvetica", 12),
                     text_color=C_MUTED).pack(anchor="w", padx=28)
        self.e_user = ClipboardEntry(
            card, placeholder_text="Введіть логін",
            width=360, height=40, corner_radius=8,
            border_color=C_BORDER, fg_color=C_BG,
            text_color=C_TEXT, font=ctk.CTkFont("Helvetica", 13),
        )
        self.e_user.pack(pady=(4, 12), padx=28)

        ctk.CTkLabel(card, text="Пароль", anchor="w",
                     font=ctk.CTkFont("Helvetica", 12),
                     text_color=C_MUTED).pack(anchor="w", padx=28)
        self.e_pass = ClipboardEntry(
            card, placeholder_text="Введіть пароль",
            width=360, height=40, corner_radius=8,
            border_color=C_BORDER, fg_color=C_BG,
            text_color=C_TEXT, font=ctk.CTkFont("Helvetica", 13),
            show="●",
        )
        self.e_pass.pack(pady=(4, 6), padx=28)
        self.e_pass.bind("<Return>", lambda _: self._do_login())

        self.lbl_err = ctk.CTkLabel(card, text="",
                                    font=ctk.CTkFont("Helvetica", 12),
                                    text_color=C_ERROR)
        self.lbl_err.pack(pady=(2, 6))

        PrimaryButton(card, "🔐  Увійти",
                      command=self._do_login, width=360).pack(
            pady=(0, 22), padx=28)

        # Підказки
        hints = ctk.CTkFrame(self, fg_color="transparent")
        hints.pack(pady=(0, 8))
        ctk.CTkLabel(hints, text="Тестові облікові дані:",
                     font=ctk.CTkFont("Helvetica", 11, "bold"),
                     text_color=C_MUTED).pack()
        for login, pwd, role in [
            ("admin",     "admin123", "Адміністратор"),
            ("operator1", "1234",     "Оператор зв'язку"),
        ]:
            ctk.CTkLabel(
                hints,
                text=f"  {role}:  логін «{login}»   пароль «{pwd}»",
                font=ctk.CTkFont("Helvetica", 11),
                text_color=C_MUTED,
            ).pack()

    def _do_login(self):
        username = self.e_user.get().strip()
        password = self.e_pass.get()

        if not username or not password:
            self.lbl_err.configure(text="⚠️  Введіть логін та пароль")
            return

        user = db.authenticate(username, password)
        if user is None:
            self.lbl_err.configure(text="❌  Невірний логін або пароль")
            self.e_pass.delete(0, "end")
            return

        db.log_action(user["user_id"], "Вхід в систему",
                      f"Роль: {user['role']}")
        self.current_user = user
        self.destroy()


# ════════════════════════════════════════════════════════════════════════════
#  Головне вікно програми
# ════════════════════════════════════════════════════════════════════════════

class App(ctk.CTk):
    def __init__(self, current_user: dict):
        super().__init__()
        self._user        = current_user
        self.wants_logout = False
        self.title(
            f"АРМ Оператора — АТ «Укрпошта»  |  {current_user['username']}"
        )
        self.geometry("1080x700")
        self.minsize(920, 600)
        self.configure(fg_color=C_BG)
        self._build()

    def _build(self):
        # ── Сайдбар ──────────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(self, fg_color=C_SIDEBAR,
                               corner_radius=0, width=236)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo = ctk.CTkFrame(sidebar, fg_color=C_YELLOW,
                            corner_radius=0, height=72)
        logo.pack(fill="x")
        logo.pack_propagate(False)
        ctk.CTkLabel(logo, text="📮  УКРПОШТА",
                     font=ctk.CTkFont("Helvetica", 16, "bold"),
                     text_color=C_DARK).place(relx=0.5, rely=0.5,
                                              anchor="center")

        ctk.CTkLabel(sidebar, text="АРМ ОПЕРАТОРА",
                     font=ctk.CTkFont("Helvetica", 10),
                     text_color="#8DA0BB").pack(pady=(12, 6))

        # Бейдж
        role       = self._user["role"]
        role_label = "👑 Адміністратор" if role == "admin" else "👷 Оператор"
        role_color = C_ADMIN if role == "admin" else C_OPER

        badge = ctk.CTkFrame(sidebar, fg_color=C_SIDEBAR2, corner_radius=10)
        badge.pack(padx=12, pady=(0, 14), fill="x")
        ctk.CTkLabel(badge,
                     text=self._user.get("display_name",
                                         self._user["username"]),
                     font=ctk.CTkFont("Helvetica", 12, "bold"),
                     text_color=C_WHITE).pack(pady=(10, 2))
        ctk.CTkLabel(badge, text=role_label,
                     font=ctk.CTkFont("Helvetica", 11),
                     text_color=role_color).pack(pady=(0, 10))

        # ── Навігація ─────────────────────────────────────────────────────
        self._panels:   dict[str, ctk.CTkFrame]  = {}
        self._nav_btns: dict[str, ctk.CTkButton] = {}

        nav_items = [
            ("tracking", "🔍  Трекінг",      TrackingPanel),
            ("register", "📦  Нова посилка",  RegisterPanel),
        ]
        if role == "admin":
            nav_items += [
                ("admin", "📊  Адмін / Звіти", AdminPanel),
                ("logs",  "📜  Журнал дій",    LogPanel),
            ]

        for key, label, PanelClass in nav_items:
            self._panels[key] = PanelClass(self, current_user=self._user)
            btn = ctk.CTkButton(
                sidebar, text=label,
                command=lambda k=key: self._show(k),
                width=212, height=44, corner_radius=10,
                fg_color="transparent", hover_color=C_SIDEBAR2,
                text_color=C_WHITE, anchor="w",
                font=ctk.CTkFont("Helvetica", 13),
            )
            btn.pack(pady=3, padx=12)
            self._nav_btns[key] = btn

        ctk.CTkButton(
            sidebar, text="🚪  Вийти з системи",
            command=self._logout,
            width=212, height=40, corner_radius=10,
            fg_color="transparent", hover_color="#3D1515",
            text_color="#FF6B6B", anchor="w",
            font=ctk.CTkFont("Helvetica", 13),
        ).pack(side="bottom", pady=12, padx=12)

        ctk.CTkLabel(sidebar, text="v1.1  •  2024",
                     font=ctk.CTkFont("Helvetica", 10),
                     text_color="#5A7094").pack(side="bottom", pady=(0, 2))

        self._show(next(iter(self._panels)))

    def _show(self, key: str):
        for panel in self._panels.values():
            panel.pack_forget()
        for k, btn in self._nav_btns.items():
            btn.configure(
                fg_color=C_YELLOW if k == key else "transparent",
                text_color=C_DARK  if k == key else C_WHITE,
            )
        self._panels[key].pack(side="left", fill="both", expand=True)

    def _logout(self):
        db.log_action(self._user["user_id"], "Вихід з системи", "")
        self.wants_logout = True
        self.destroy()


# ════════════════════════════════════════════════════════════════════════════
#  Точка входу
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    db.init_db()

    while True:
        login = LoginWindow()
        login.mainloop()

        if not login.current_user:
            break

        app = App(login.current_user)
        app.mainloop()

        if not getattr(app, "wants_logout", False):
            break