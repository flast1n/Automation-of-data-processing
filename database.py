"""
database.py — Шар роботи з базою даних Укрпошти.
Весь SQL зосереджено тут. GUI жодного разу не торкається sqlite3 напряму.
"""

import sqlite3
import random
import string
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).parent / "ukrposhta_db.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # доступ до колонок за іменем
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ─── Трекінг / пошук ────────────────────────────────────────────────────────

def find_parcel(track_number: str) -> dict | None:
    """Повертає повну інформацію про посилку за трек-номером або None."""
    sql = """
        SELECT
            p.track_number,
            p.weight,
            p.price,
            p.delivery_type,
            s.fullname  AS sender_name,
            s.phone     AS sender_phone,
            r.fullname  AS receiver_name,
            r.phone     AS receiver_phone,
            e.fullname  AS employee_name
        FROM Parcels p
        JOIN Clients  s ON p.sender_id   = s.client_id
        JOIN Clients  r ON p.receiver_id = r.client_id
        JOIN Employees e ON p.employee_id = e.employee_id
        WHERE p.track_number = ?
    """
    with _connect() as conn:
        row = conn.execute(sql, (track_number.strip(),)).fetchone()
    return dict(row) if row else None


# ─── Реєстрація посилки ──────────────────────────────────────────────────────

def _generate_track() -> str:
    """Генерує унікальний 13-значний трек-номер (формат Укрпошти: 05000XXXXXXX)."""
    with _connect() as conn:
        while True:
            digits = "".join(random.choices(string.digits, k=8))
            track = f"05000{digits}"
            exists = conn.execute(
                "SELECT 1 FROM Parcels WHERE track_number = ?", (track,)
            ).fetchone()
            if not exists:
                return track


def _get_or_create_client(conn: sqlite3.Connection, fullname: str, phone: str) -> int:
    """Повертає client_id існуючого клієнта або створює нового."""
    row = conn.execute(
        "SELECT client_id FROM Clients WHERE phone = ?", (phone.strip(),)
    ).fetchone()
    if row:
        return row["client_id"]
    cur = conn.execute(
        "INSERT INTO Clients (fullname, phone) VALUES (?, ?)",
        (fullname.strip(), phone.strip()),
    )
    return cur.lastrowid


def register_parcel(
    sender_name: str,
    sender_phone: str,
    receiver_name: str,
    receiver_phone: str,
    weight: float,
    price: float,
    delivery_type: str,
    employee_id: int,
) -> str:
    """Реєструє нову посилку. Повертає згенерований трек-номер."""
    track = _generate_track()
    with _connect() as conn:
        sender_id   = _get_or_create_client(conn, sender_name,   sender_phone)
        receiver_id = _get_or_create_client(conn, receiver_name, receiver_phone)
        conn.execute(
            """INSERT INTO Parcels
               (track_number, sender_id, receiver_id, weight, price, delivery_type, employee_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (track, sender_id, receiver_id, weight, price, delivery_type, employee_id),
        )
        conn.commit()
    return track


# ─── Довідники ───────────────────────────────────────────────────────────────

def get_employees() -> list[dict]:
    """Повертає список всіх співробітників для вибору оператора."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT employee_id, fullname, position FROM Employees ORDER BY fullname"
        ).fetchall()
    return [dict(r) for r in rows]


# ─── Звіти ───────────────────────────────────────────────────────────────────

def report_cashier(target_date: str | None = None) -> list[dict]:
    """
    Звіт по касі: кількість та сума посилок по кожному співробітнику.
    target_date — рядок 'YYYY-MM-DD'; якщо None — всі записи (немає поля дати).
    """
    # У базі немає поля дати, тому повертаємо загальну статистику
    sql = """
        SELECT
            e.fullname                   AS employee_name,
            e.position,
            COUNT(p.parcel_id)           AS parcel_count,
            ROUND(SUM(p.price), 2)       AS total_sum
        FROM Employees e
        LEFT JOIN Parcels p ON e.employee_id = p.employee_id
        GROUP BY e.employee_id
        ORDER BY total_sum DESC
    """
    with _connect() as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


def report_efficiency() -> list[dict]:
    """
    Ефективність працівників: кількість посилок і середня вага по кожному.
    """
    sql = """
        SELECT
            e.fullname                        AS employee_name,
            e.position,
            COUNT(p.parcel_id)                AS parcel_count,
            ROUND(AVG(p.weight), 2)           AS avg_weight,
            ROUND(SUM(p.price), 2)            AS total_sum,
            ROUND(AVG(p.price), 2)            AS avg_price
        FROM Employees e
        LEFT JOIN Parcels p ON e.employee_id = p.employee_id
        GROUP BY e.employee_id
        ORDER BY parcel_count DESC
    """
    with _connect() as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


def report_all_parcels() -> list[dict]:
    """Повний список посилок для перегляду адміністратором."""
    sql = """
        SELECT
            p.parcel_id,
            p.track_number,
            s.fullname   AS sender,
            r.fullname   AS receiver,
            p.weight,
            p.price,
            p.delivery_type,
            e.fullname   AS employee
        FROM Parcels p
        JOIN Clients  s ON p.sender_id   = s.client_id
        JOIN Clients  r ON p.receiver_id = r.client_id
        JOIN Employees e ON p.employee_id = e.employee_id
        ORDER BY p.parcel_id DESC
    """
    with _connect() as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]