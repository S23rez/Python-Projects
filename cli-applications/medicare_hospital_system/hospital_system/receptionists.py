"""
receptionists.py
------------------
Receptionist profile records. Login accounts (with Pass codes) are
handled separately in auth.py / staff.py -- this module just stores
the who's-who: name, email, phone.
"""

from datetime import datetime

import db
import validators


def add_receptionist(full_name, email, phone):
    full_name = full_name.strip()
    email = email.strip()
    phone = phone.strip()

    if not full_name:
        raise ValueError("Full name is required.")
    if not validators.is_valid_email(email):
        raise ValueError(f"'{email}' is not a valid email address.")
    if not validators.is_valid_phone(phone):
        raise ValueError(f"'{phone}' is not a valid phone number.")

    conn = db.get_connection()
    cur = conn.cursor()

    existing = cur.execute(
        "SELECT receptionist_id FROM receptionists WHERE lower(email) = lower(?)", (email,)
    ).fetchone()
    if existing:
        conn.close()
        raise ValueError(f"A receptionist with email '{email}' already exists (ID {existing['receptionist_id']}).")

    receptionist_id = db.next_id(cur, "receptionists", "receptionist_id", "R")
    cur.execute(
        """INSERT INTO receptionists (receptionist_id, full_name, email, phone, date_added)
           VALUES (?, ?, ?, ?, ?)""",
        (receptionist_id, full_name, email, phone, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()
    return receptionist_id


def get_receptionist(receptionist_id: str):
    conn = db.get_connection()
    row = conn.execute(
        "SELECT * FROM receptionists WHERE receptionist_id = ?", (receptionist_id,)
    ).fetchone()
    conn.close()
    return row


def receptionist_exists(receptionist_id: str) -> bool:
    return get_receptionist(receptionist_id) is not None


def list_all_receptionists():
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM receptionists ORDER BY receptionist_id").fetchall()
    conn.close()
    return rows


def remove_receptionist(receptionist_id: str):
    if not receptionist_exists(receptionist_id):
        raise ValueError(f"Receptionist {receptionist_id} not found.")
    conn = db.get_connection()
    conn.execute("DELETE FROM receptionists WHERE receptionist_id = ?", (receptionist_id,))
    conn.commit()
    conn.close()
