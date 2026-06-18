"""
database.py — Шар роботи з базою даних Укрпошти.
Весь SQL зосереджено тут. GUI жодного разу не торкається sqlite3 напряму.
"""

import sqlite3
import random
import string
import hashlib
from pathlib import Path

DB_PATH = Path(__file__).parent / "ukrposhta_db.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ─── Ініціалізація ───────────────────────────────────────────────────────────

def init_db() -> None:
    """Створює таблиці Users та ActionLog (якщо ще немає) і сіє тестових юзерів."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS Users (
                user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                username    VARCHAR(50)  NOT NULL UNIQUE,
                password    VARCHAR(100) NOT NULL,
                role        VARCHAR(20)  NOT NULL DEFAULT 'operator',
                employee_id INTEGER REFERENCES Employees(employee_id)
            );

            CREATE TABLE IF NOT EXISTS ActionLog (
                log_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER REFERENCES Users(user_id),
                action    VARCHAR(100) NOT NULL,
                details   TEXT DEFAULT '',
                timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
            );
        """)

        seed = [
            ("admin",     "admin123", "admin",    None),
            ("operator1", "1234",     "operator", 1),
            ("operator2", "1234",     "operator", 2),
        ]
        for username, pwd, role, emp_id in seed:
            exists = conn.execute(
                "SELECT 1 FROM Users WHERE username = ?", (username,)
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO Users (username, password, role, employee_id) "
                    "VALUES (?, ?, ?, ?)",
                    (username, _hash(pwd), role, emp_id),
                )
        conn.commit()


# ─── Авторизація ─────────────────────────────────────────────────────────────

def authenticate(username: str, password: str) -> dict | None:
    sql = """
        SELECT u.user_id, u.username, u.role, u.employee_id,
               COALESCE(e.fullname, u.username) AS display_name
        FROM Users u
        LEFT JOIN Employees e ON u.employee_id = e.employee_id
        WHERE u.username = ? AND u.password = ?
    """
    with _connect() as conn:
        row = conn.execute(sql, (username.strip(), _hash(password))).fetchone()
    return dict(row) if row else None


# ─── Журнал дій ──────────────────────────────────────────────────────────────

def log_action(user_id: int, action: str, details: str = "") -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO ActionLog (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, action, details),
        )
        conn.commit()


def get_logs(limit: int = 300) -> list[dict]:
    sql = """
        SELECT l.log_id, l.timestamp, u.username, u.role, l.action, l.details
        FROM ActionLog l
        LEFT JOIN Users u ON l.user_id = u.user_id
        ORDER BY l.log_id DESC
        LIMIT ?
    """
    with _connect() as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]


# ─── Трекінг / пошук ────────────────────────────────────────────────────────

def find_parcel(track_number: str) -> dict | None:
    sql = """
        SELECT
            p.track_number, p.weight, p.price, p.delivery_type,
            s.fullname AS sender_name,   s.phone AS sender_phone,
            r.fullname AS receiver_name, r.phone AS receiver_phone,
            e.fullname AS employee_name
        FROM Parcels p
        JOIN Clients   s ON p.sender_id   = s.client_id
        JOIN Clients   r ON p.receiver_id = r.client_id
        JOIN Employees e ON p.employee_id = e.employee_id
        WHERE p.track_number = ?
    """
    with _connect() as conn:
        row = conn.execute(sql, (track_number.strip(),)).fetchone()
    return dict(row) if row else None


# ─── Реєстрація посилки ──────────────────────────────────────────────────────

def _generate_track() -> str:
    with _connect() as conn:
        while True:
            track = "05000" + "".join(random.choices(string.digits, k=8))
            if not conn.execute(
                "SELECT 1 FROM Parcels WHERE track_number = ?", (track,)
            ).fetchone():
                return track


def _get_or_create_client(conn: sqlite3.Connection,
                           fullname: str, phone: str) -> int:
    row = conn.execute(
        "SELECT client_id FROM Clients WHERE phone = ?", (phone.strip(),)
    ).fetchone()
    if row:
        return row["client_id"]
    return conn.execute(
        "INSERT INTO Clients (fullname, phone) VALUES (?, ?)",
        (fullname.strip(), phone.strip()),
    ).lastrowid


def register_parcel(
    sender_name: str, sender_phone: str,
    receiver_name: str, receiver_phone: str,
    weight: float, price: float,
    delivery_type: str, employee_id: int,
) -> str:
    track = _generate_track()
    with _connect() as conn:
        sid = _get_or_create_client(conn, sender_name,   sender_phone)
        rid = _get_or_create_client(conn, receiver_name, receiver_phone)
        conn.execute(
            "INSERT INTO Parcels "
            "(track_number,sender_id,receiver_id,weight,price,delivery_type,employee_id)"
            " VALUES (?,?,?,?,?,?,?)",
            (track, sid, rid, weight, price, delivery_type, employee_id),
        )
        conn.commit()
    return track


# ─── Довідники ───────────────────────────────────────────────────────────────

def get_employees() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT employee_id, fullname, position FROM Employees ORDER BY fullname"
        ).fetchall()
    return [dict(r) for r in rows]


# ─── Звіти ───────────────────────────────────────────────────────────────────

def report_cashier() -> list[dict]:
    sql = """
        SELECT e.fullname AS employee_name, e.position,
               COUNT(p.parcel_id)    AS parcel_count,
               ROUND(SUM(p.price),2) AS total_sum
        FROM Employees e
        LEFT JOIN Parcels p ON e.employee_id = p.employee_id
        GROUP BY e.employee_id
        ORDER BY total_sum DESC
    """
    with _connect() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


def report_efficiency() -> list[dict]:
    sql = """
        SELECT e.fullname AS employee_name, e.position,
               COUNT(p.parcel_id)     AS parcel_count,
               ROUND(AVG(p.weight),2) AS avg_weight,
               ROUND(SUM(p.price),2)  AS total_sum,
               ROUND(AVG(p.price),2)  AS avg_price
        FROM Employees e
        LEFT JOIN Parcels p ON e.employee_id = p.employee_id
        GROUP BY e.employee_id
        ORDER BY parcel_count DESC
    """
    with _connect() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


def report_all_parcels() -> list[dict]:
    sql = """
        SELECT p.parcel_id, p.track_number,
               s.fullname AS sender,   r.fullname AS receiver,
               p.weight, p.price, p.delivery_type,
               e.fullname AS employee
        FROM Parcels p
        JOIN Clients   s ON p.sender_id   = s.client_id
        JOIN Clients   r ON p.receiver_id = r.client_id
        JOIN Employees e ON p.employee_id = e.employee_id
        ORDER BY p.parcel_id DESC
    """
    with _connect() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]