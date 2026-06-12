"""
main.py — Головний файл програми «АРМ Оператора Укрпошти».
Запуск: python main.py
"""

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk

import database as db

# ─── Глобальні налаштування теми ────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Кольорова палітра Укрпошти
C_YELLOW   = "#FFD700"
C_YELLOW_H = "#FFC200"       # hover
C_DARK     = "#1A1A2E"       # майже чорний — заголовки
C_SIDEBAR  = "#1C2B4A"       # темно-синій сайдбар
C_SIDEBAR2 = "#253857"       # hover кнопок сайдбару
C_WHITE    = "#FFFFFF"
C_BG       = "#F4F6FA"       # фон контенту
C_TEXT     = "#1A1A2E"
C_MUTED    = "#6B7A99"
C_SUCCESS  = "#27AE60"
C_ERROR    = "#E74C3C"
C_BORDER   = "#DDE3EE"


# ════════════════════════════════════════════════════════════════════════════
#  Допоміжні віджети
# ════════════════════════════════════════════════════════════════════════════

class SectionLabel(ctk.CTkLabel):
    def __init__(self, master, text, **kw):
        super().__init__(
            master, text=text,
            font=ctk.CTkFont("Helvetica", 11, "bold"),
            text_color=C_MUTED, **kw
        )


class FieldEntry(ctk.CTkEntry):
    def __init__(self, master, placeholder="", width=280, **kw):
        super().__init__(
            master,
            placeholder_text=placeholder,
            width=width,
            height=38,
            corner_radius=8,
            border_color=C_BORDER,
            fg_color=C_WHITE,
            text_color=C_TEXT,
            font=ctk.CTkFont("Helvetica", 13),
            **kw,
        )


class PrimaryButton(ctk.CTkButton):
    def __init__(self, master, text, command=None, width=160, **kw):
        super().__init__(
            master,
            text=text,
            command=command,
            width=width,
            height=42,
            corner_radius=10,
            fg_color=C_YELLOW,
            hover_color=C_YELLOW_H,
            text_color=C_DARK,
            font=ctk.CTkFont("Helvetica", 13, "bold"),
            **kw,
        )


class StatusCard(ctk.CTkFrame):
    """Картка з результатом — зелена або червона рамка."""
    def __init__(self, master, success=True, **kw):
        color = C_SUCCESS if success else C_ERROR
        super().__init__(
            master,
            fg_color=C_WHITE,
            border_color=color,
            border_width=2,
            corner_radius=12,
            **kw,
        )
        self._color = color

    def set_text(self, lines: list[tuple[str, str]]):
        """lines = [(label, value), ...]"""
        for w in self.winfo_children():
            w.destroy()
        for label, value in lines:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(
                row, text=label, width=160, anchor="w",
                font=ctk.CTkFont("Helvetica", 12), text_color=C_MUTED
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=value, anchor="w",
                font=ctk.CTkFont("Helvetica", 13, "bold"), text_color=C_TEXT
            ).pack(side="left", padx=(4, 0))


# ════════════════════════════════════════════════════════════════════════════
#  Панелі (сторінки)
# ════════════════════════════════════════════════════════════════════════════

class TrackingPanel(ctk.CTkFrame):
    """Блок 1 — Пошук посилки за трек-номером."""

    def __init__(self, master, **kw):
        super().__init__(master, fg_color=C_BG, **kw)
        self._build()

    def _build(self):
        # Заголовок
        ctk.CTkLabel(
            self, text="🔍  Трекінг посилки",
            font=ctk.CTkFont("Helvetica", 22, "bold"), text_color=C_DARK
        ).pack(anchor="w", padx=32, pady=(28, 4))
        ctk.CTkLabel(
            self, text="Введіть трек-номер щоб дізнатись статус відправлення",
            font=ctk.CTkFont("Helvetica", 13), text_color=C_MUTED
        ).pack(anchor="w", padx=32, pady=(0, 20))

        # Поле вводу + кнопка
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(anchor="w", padx=32, pady=(0, 20))

        self.entry = FieldEntry(row, placeholder="0500041234567", width=320)
        self.entry.pack(side="left", padx=(0, 12))
        self.entry.bind("<Return>", lambda e: self._search())

        PrimaryButton(row, "Знайти", command=self._search, width=120).pack(side="left")

        # Зона результату
        self.result_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.result_frame.pack(fill="x", padx=32, pady=(0, 12))

    def _search(self):
        track = self.entry.get().strip()
        if len(track) != 13 or not track.isdigit():
            self._show_error("Трек-номер має містити рівно 13 цифр")
            return

        parcel = db.find_parcel(track)

        # очищаємо попередній результат
        for w in self.result_frame.winfo_children():
            w.destroy()

        if parcel is None:
            card = StatusCard(self.result_frame, success=False)
            card.pack(fill="x", pady=4)
            card.set_text([("", f"❌  Посилку «{track}» не знайдено в базі")])
            return

        card = StatusCard(self.result_frame, success=True)
        card.pack(fill="x", pady=4)
        delivery_icon = {"Укрпошта Експрес": "⚡", "Укрпошта Стандарт": "📦"}.get(
            parcel["delivery_type"], "📮"
        )
        card.set_text([
            ("✅  Посилка знайдена!", ""),
            ("Трек-номер:",    parcel["track_number"]),
            ("Тип доставки:",  f"{delivery_icon}  {parcel['delivery_type']}"),
            ("Вага:",          f"{parcel['weight']} кг"),
            ("Вартість:",      f"{parcel['price']} грн"),
            ("Відправник:",    parcel["sender_name"]),
            ("Тел. відпр.:",   parcel["sender_phone"]),
            ("Отримувач:",     parcel["receiver_name"]),
            ("Тел. отрим.:",   parcel["receiver_phone"]),
            ("Оформив:",       parcel["employee_name"]),
        ])

    def _show_error(self, msg: str):
        for w in self.result_frame.winfo_children():
            w.destroy()
        card = StatusCard(self.result_frame, success=False)
        card.pack(fill="x", pady=4)
        card.set_text([("", f"⚠️  {msg}")])


# ─────────────────────────────────────────────────────────────────────────────

class RegisterPanel(ctk.CTkFrame):
    """Блок 2 — Реєстрація нового відправлення."""

    DELIVERY_TYPES = ["Укрпошта Стандарт", "Укрпошта Експрес", "Укрпошта Першокласна"]

    def __init__(self, master, **kw):
        super().__init__(master, fg_color=C_BG, **kw)
        self._employees = db.get_employees()
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self, text="📦  Реєстрація відправлення",
            font=ctk.CTkFont("Helvetica", 22, "bold"), text_color=C_DARK
        ).pack(anchor="w", padx=32, pady=(28, 4))
        ctk.CTkLabel(
            self, text="Заповніть дані клієнтів та параметри посилки",
            font=ctk.CTkFont("Helvetica", 13), text_color=C_MUTED
        ).pack(anchor="w", padx=32, pady=(0, 20))

        # Контейнер із двома колонками
        cols = ctk.CTkFrame(self, fg_color="transparent")
        cols.pack(anchor="w", padx=32, fill="x")

        left  = ctk.CTkFrame(cols, fg_color="transparent")
        left.pack(side="left", anchor="n", padx=(0, 32))
        right = ctk.CTkFrame(cols, fg_color="transparent")
        right.pack(side="left", anchor="n")

        # ── Ліворуч: відправник ──
        ctk.CTkLabel(left, text="ВІДПРАВНИК", font=ctk.CTkFont("Helvetica", 11, "bold"),
                     text_color=C_MUTED).pack(anchor="w", pady=(0, 6))
        self.e_sender_name  = self._field(left, "ПІБ відправника")
        self.e_sender_phone = self._field(left, "+380XXXXXXXXX")

        ctk.CTkLabel(left, text="ОТРИМУВАЧ", font=ctk.CTkFont("Helvetica", 11, "bold"),
                     text_color=C_MUTED).pack(anchor="w", pady=(16, 6))
        self.e_recv_name  = self._field(left, "ПІБ отримувача")
        self.e_recv_phone = self._field(left, "+380XXXXXXXXX")

        # ── Праворуч: параметри ──
        ctk.CTkLabel(right, text="ПАРАМЕТРИ ПОСИЛКИ", font=ctk.CTkFont("Helvetica", 11, "bold"),
                     text_color=C_MUTED).pack(anchor="w", pady=(0, 6))
        self.e_weight = self._field(right, "Вага (кг), напр. 2.5")
        self.e_price  = self._field(right, "Вартість (грн), напр. 65.00")

        ctk.CTkLabel(right, text="Тип доставки", font=ctk.CTkFont("Helvetica", 12),
                     text_color=C_MUTED).pack(anchor="w", pady=(10, 4))
        self.delivery_var = ctk.StringVar(value=self.DELIVERY_TYPES[0])
        ctk.CTkOptionMenu(
            right, values=self.DELIVERY_TYPES,
            variable=self.delivery_var,
            width=280, height=38, corner_radius=8,
            fg_color=C_WHITE, button_color=C_YELLOW, button_hover_color=C_YELLOW_H,
            text_color=C_TEXT, font=ctk.CTkFont("Helvetica", 13),
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(right, text="Оператор", font=ctk.CTkFont("Helvetica", 12),
                     text_color=C_MUTED).pack(anchor="w", pady=(2, 4))
        emp_names = [f"{e['fullname']} ({e['position']})" for e in self._employees]
        self.employee_var = ctk.StringVar(value=emp_names[0] if emp_names else "")
        ctk.CTkOptionMenu(
            right, values=emp_names,
            variable=self.employee_var,
            width=280, height=38, corner_radius=8,
            fg_color=C_WHITE, button_color=C_YELLOW, button_hover_color=C_YELLOW_H,
            text_color=C_TEXT, font=ctk.CTkFont("Helvetica", 13),
        ).pack(anchor="w")

        # Кнопка + результат
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(anchor="w", padx=32, pady=20)
        PrimaryButton(btn_row, "✅  Оформити посилку", command=self._submit, width=220).pack(side="left")

        self.result_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.result_frame.pack(fill="x", padx=32)

    @staticmethod
    def _field(parent, placeholder) -> FieldEntry:
        e = FieldEntry(parent, placeholder=placeholder, width=280)
        e.pack(anchor="w", pady=4)
        return e

    def _submit(self):
        # Збір значень
        s_name  = self.e_sender_name.get().strip()
        s_phone = self.e_sender_phone.get().strip()
        r_name  = self.e_recv_name.get().strip()
        r_phone = self.e_recv_phone.get().strip()
        weight_s = self.e_weight.get().strip()
        price_s  = self.e_price.get().strip()
        d_type   = self.delivery_var.get()

        # Валідація
        errors = []
        if not s_name:  errors.append("ПІБ відправника")
        if not s_phone: errors.append("Телефон відправника")
        if not r_name:  errors.append("ПІБ отримувача")
        if not r_phone: errors.append("Телефон отримувача")
        try:
            weight = float(weight_s)
            if weight <= 0: raise ValueError
        except ValueError:
            errors.append("Вага (число > 0)")
        try:
            price = float(price_s)
            if price <= 0: raise ValueError
        except ValueError:
            errors.append("Вартість (число > 0)")

        if errors:
            self._show_result(False, f"Заповніть поля: {', '.join(errors)}")
            return

        # Визначаємо employee_id
        sel_idx = [f"{e['fullname']} ({e['position']})" for e in self._employees].index(
            self.employee_var.get()
        )
        emp_id = self._employees[sel_idx]["employee_id"]

        try:
            track = db.register_parcel(
                s_name, s_phone, r_name, r_phone,
                weight, price, d_type, emp_id
            )
            self._show_result(
                True,
                f"Посилку успішно оформлено!\nТрек-номер: {track}",
            )
            self._clear_fields()
        except Exception as exc:
            self._show_result(False, f"Помилка бази даних: {exc}")

    def _show_result(self, success: bool, msg: str):
        for w in self.result_frame.winfo_children():
            w.destroy()
        icon = "✅" if success else "❌"
        card = StatusCard(self.result_frame, success=success)
        card.pack(fill="x", pady=4)
        for line in f"{icon}  {msg}".split("\n"):
            ctk.CTkLabel(
                card, text=line, font=ctk.CTkFont("Helvetica", 13, "bold" if success else "normal"),
                text_color=C_SUCCESS if success else C_ERROR, anchor="w"
            ).pack(anchor="w", padx=16, pady=3)

    def _clear_fields(self):
        for entry in [self.e_sender_name, self.e_sender_phone,
                      self.e_recv_name, self.e_recv_phone,
                      self.e_weight, self.e_price]:
            entry.delete(0, "end")


# ─────────────────────────────────────────────────────────────────────────────

class AdminPanel(ctk.CTkFrame):
    """Блок 3 — Адмін-панель зі звітами."""

    def __init__(self, master, **kw):
        super().__init__(master, fg_color=C_BG, **kw)
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self, text="📊  Адмін-панель  / Звіти",
            font=ctk.CTkFont("Helvetica", 22, "bold"), text_color=C_DARK
        ).pack(anchor="w", padx=32, pady=(28, 4))
        ctk.CTkLabel(
            self, text="Оперативна статистика по відділенню",
            font=ctk.CTkFont("Helvetica", 13), text_color=C_MUTED
        ).pack(anchor="w", padx=32, pady=(0, 20))

        # Кнопки звітів
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(anchor="w", padx=32, pady=(0, 16))
        PrimaryButton(btn_row, "💰  Звіт по касі",       command=self._cashier_report, width=180).pack(side="left", padx=(0, 12))
        PrimaryButton(btn_row, "👷  Ефективність",        command=self._efficiency_report, width=180).pack(side="left", padx=(0, 12))
        PrimaryButton(btn_row, "📋  Всі посилки",         command=self._all_parcels, width=180).pack(side="left")

        # Зона таблиці
        self.table_frame = ctk.CTkScrollableFrame(
            self, fg_color=C_WHITE,
            corner_radius=12, border_width=1, border_color=C_BORDER
        )
        self.table_frame.pack(fill="both", expand=True, padx=32, pady=(0, 20))

    def _clear_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()

    def _render_table(self, title: str, headers: list[str], rows: list[list]):
        self._clear_table()

        ctk.CTkLabel(
            self.table_frame, text=title,
            font=ctk.CTkFont("Helvetica", 15, "bold"), text_color=C_DARK
        ).pack(anchor="w", padx=12, pady=(12, 8))

        if not rows:
            ctk.CTkLabel(
                self.table_frame, text="Даних немає",
                font=ctk.CTkFont("Helvetica", 13), text_color=C_MUTED
            ).pack(padx=12, pady=12)
            return

        # Заголовки
        h_row = ctk.CTkFrame(self.table_frame, fg_color=C_SIDEBAR, corner_radius=8)
        h_row.pack(fill="x", padx=8, pady=(0, 4))
        for h in headers:
            ctk.CTkLabel(
                h_row, text=h, anchor="w",
                font=ctk.CTkFont("Helvetica", 11, "bold"),
                text_color=C_WHITE, width=max(80, int(600 / len(headers)))
            ).pack(side="left", padx=10, pady=7)

        # Рядки
        for i, data_row in enumerate(rows):
            bg = C_WHITE if i % 2 == 0 else "#F0F3F9"
            d_row = ctk.CTkFrame(self.table_frame, fg_color=bg, corner_radius=6)
            d_row.pack(fill="x", padx=8, pady=1)
            for cell in data_row:
                ctk.CTkLabel(
                    d_row, text=str(cell) if cell is not None else "—",
                    anchor="w", font=ctk.CTkFont("Helvetica", 12), text_color=C_TEXT,
                    width=max(80, int(600 / len(headers)))
                ).pack(side="left", padx=10, pady=6)

    def _cashier_report(self):
        data = db.report_cashier()
        headers = ["Співробітник", "Посада", "Посилок", "Сума (грн)"]
        rows = [[d["employee_name"], d["position"], d["parcel_count"], d["total_sum"]] for d in data]
        self._render_table("💰  Звіт по касі", headers, rows)

    def _efficiency_report(self):
        data = db.report_efficiency()
        headers = ["Співробітник", "Посада", "Посилок", "Сер. вага (кг)", "Сума (грн)", "Сер. ціна"]
        rows = [
            [d["employee_name"], d["position"], d["parcel_count"],
             d["avg_weight"], d["total_sum"], d["avg_price"]]
            for d in data
        ]
        self._render_table("👷  Ефективність працівників", headers, rows)

    def _all_parcels(self):
        data = db.report_all_parcels()
        headers = ["ID", "Трек-номер", "Відправник", "Отримувач", "Вага", "Ціна", "Тип", "Оператор"]
        rows = [
            [d["parcel_id"], d["track_number"], d["sender"], d["receiver"],
             f"{d['weight']} кг", f"{d['price']} грн", d["delivery_type"], d["employee"]]
            for d in data
        ]
        self._render_table("📋  Всі посилки", headers, rows)


# ════════════════════════════════════════════════════════════════════════════
#  Головне вікно
# ════════════════════════════════════════════════════════════════════════════

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("АРМ Оператора — АТ «Укрпошта»")
        self.geometry("1040x680")
        self.minsize(900, 600)
        self.configure(fg_color=C_BG)
        self._build()

    def _build(self):
        # ── Сайдбар ──
        sidebar = ctk.CTkFrame(self, fg_color=C_SIDEBAR, corner_radius=0, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Логотип / назва
        logo_frame = ctk.CTkFrame(sidebar, fg_color=C_YELLOW, corner_radius=0, height=72)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)
        ctk.CTkLabel(
            logo_frame, text="📮  УКРПОШТА",
            font=ctk.CTkFont("Helvetica", 16, "bold"), text_color=C_DARK
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            sidebar, text="АРМ ОПЕРАТОРА",
            font=ctk.CTkFont("Helvetica", 10), text_color="#8DA0BB"
        ).pack(pady=(14, 20))

        # Навігаційні кнопки
        self._panels: dict[str, ctk.CTkFrame] = {}
        self._nav_btns: dict[str, ctk.CTkButton] = {}

        nav_items = [
            ("tracking",  "🔍  Трекінг",        TrackingPanel),
            ("register",  "📦  Нова посилка",    RegisterPanel),
            ("admin",     "📊  Адмін / Звіти",   AdminPanel),
        ]

        for key, label, PanelClass in nav_items:
            panel = PanelClass(self)
            self._panels[key] = panel

            btn = ctk.CTkButton(
                sidebar, text=label,
                command=lambda k=key: self._show(k),
                width=200, height=44, corner_radius=10,
                fg_color="transparent", hover_color=C_SIDEBAR2,
                text_color=C_WHITE, anchor="w",
                font=ctk.CTkFont("Helvetica", 13),
            )
            btn.pack(pady=3, padx=10)
            self._nav_btns[key] = btn

        # Версія внизу сайдбару
        ctk.CTkLabel(
            sidebar, text="v1.0  •  2024",
            font=ctk.CTkFont("Helvetica", 10), text_color="#5A7094"
        ).pack(side="bottom", pady=14)

        # Показати першу панель
        self._show("tracking")

    def _show(self, key: str):
        for k, panel in self._panels.items():
            panel.pack_forget()
        for k, btn in self._nav_btns.items():
            btn.configure(
                fg_color=C_YELLOW if k == key else "transparent",
                text_color=C_DARK if k == key else C_WHITE,
            )
        self._panels[key].pack(side="left", fill="both", expand=True)


# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = App()
    app.mainloop()