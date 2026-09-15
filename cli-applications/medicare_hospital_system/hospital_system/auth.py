"""
auth.py
-------
Handles user accounts shared by all four roles: admin, receptionist,
doctor and patient. Passwords are never stored in plain text -- they
are salted and hashed with PBKDF2-HMAC-SHA256 (Python's hashlib).
"""

import hashlib
import os
from datetime import datetime

import db

ROLES = ("admin", "receptionist", "doctor", "patient")


def hash_password(password: str, salt: str = None):
    """Return (hash_hex, salt_hex). Generates a new random salt if none given."""
    if salt is None:
        salt = os.urandom(16).hex()
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000
    ).hex()
    return pwd_hash, salt


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == stored_hash


def username_exists(username: str) -> bool:
    conn = db.get_connection()
    row = conn.execute(
        "SELECT 1 FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return row is not None


def create_user(username: str, password: str, role: str, linked_id: str = None, full_name: str = None):
    """Insert a new row into the users table for a username/password account
    (used for Admin and self-registering Patients). Raises ValueError on bad input."""
    if role not in ROLES:
        raise ValueError(f"Invalid role: {role}")
    if username_exists(username):
        raise ValueError(f"Username '{username}' is already taken.")
    if len(password) < 4:
        raise ValueError("Password must be at least 4 characters long.")

    pwd_hash, salt = hash_password(password)
    conn = db.get_connection()
    conn.execute(
        """INSERT INTO users (username, password_hash, salt, role, linked_id, full_name, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (username, pwd_hash, salt, role, linked_id, full_name, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def access_code_exists(access_code: str) -> bool:
    conn = db.get_connection()
    row = conn.execute("SELECT 1 FROM users WHERE access_code = ?", (access_code,)).fetchone()
    conn.close()
    return row is not None


def next_access_code(prefix: str, width: int = 3) -> str:
    """Generate the next sequential pass code for a prefix, e.g. Doc001, Doc002...
    (Rec001, Rec002... for receptionists). Purely additive -- never reuses a
    code, even if an earlier one was later removed."""
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT access_code FROM users WHERE access_code LIKE ? ORDER BY access_code DESC",
        (f"{prefix}%",),
    ).fetchall()
    conn.close()
    max_num = 0
    for row in rows:
        digits = row["access_code"][len(prefix):]
        if digits.isdigit():
            max_num = max(max_num, int(digits))
    return f"{prefix}{max_num + 1:0{width}d}"


def create_staff_account(role: str, linked_id: str, full_name: str, access_code: str = None):
    """Create a Doctor or Receptionist account that logs in with a Pass
    code instead of a username/password pair. If access_code isn't
    supplied, the next sequential one for the role is generated
    (Doc001, Doc002... / Rec001, Rec002...). Returns the access code."""
    if role not in ("doctor", "receptionist"):
        raise ValueError("create_staff_account is only for doctor/receptionist roles.")

    prefix = "Doc" if role == "doctor" else "Rec"
    if access_code is None:
        access_code = next_access_code(prefix)
    elif access_code_exists(access_code):
        raise ValueError(f"Pass code '{access_code}' is already in use.")

    # The access code doubles as the username and (hashed) password so the
    # row satisfies the same schema as every other account, but staff never
    # need to know or type anything except the Pass code itself.
    pwd_hash, salt = hash_password(access_code)
    conn = db.get_connection()
    conn.execute(
        """INSERT INTO users (username, password_hash, salt, role, linked_id, full_name, access_code, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (access_code, pwd_hash, salt, role, linked_id, full_name, access_code,
         datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()
    return access_code


def reissue_pass(role: str, linked_id: str) -> str:
    """Revoke a staff member's current Pass and issue a brand-new one
    (e.g. if the old one was lost or compromised)."""
    conn = db.get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE role = ? AND linked_id = ?", (role, linked_id)
    ).fetchone()
    if row is None:
        conn.close()
        raise ValueError(f"No {role} account found for ID {linked_id}.")

    prefix = "Doc" if role == "doctor" else "Rec"
    new_code = next_access_code(prefix)
    pwd_hash, salt = hash_password(new_code)
    conn.execute(
        "UPDATE users SET username = ?, access_code = ?, password_hash = ?, salt = ? WHERE user_id = ?",
        (new_code, new_code, pwd_hash, salt, row["user_id"]),
    )
    conn.commit()
    conn.close()
    return new_code


def remove_staff_account(role: str, linked_id: str):
    """Delete the login account tied to a doctor/receptionist that is
    being removed, so their old Pass can no longer be used to log in."""
    conn = db.get_connection()
    conn.execute("DELETE FROM users WHERE role = ? AND linked_id = ?", (role, linked_id))
    conn.commit()
    conn.close()


def login(username: str, password: str):
    """Username/password login -- used for Admin and Patient accounts.
    Returns the user row (sqlite3.Row) on success, or None on failure."""
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if row is None:
        return None
    if verify_password(password, row["salt"], row["password_hash"]):
        return row
    return None


def login_by_pass(access_code: str):
    """Pass-code login -- used for Doctor and Receptionist accounts.
    Single-factor: possessing the exact code is the credential.
    Returns the user row on success, or None if the code doesn't match."""
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM users WHERE access_code = ?", (access_code,)).fetchone()
    conn.close()
    return row


def any_admin_exists() -> bool:
    conn = db.get_connection()
    row = conn.execute("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1").fetchone()
    conn.close()
    return row is not None
