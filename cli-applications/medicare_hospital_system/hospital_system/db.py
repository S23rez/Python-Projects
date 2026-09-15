"""
db.py
-----
Handles the SQLite connection and creates all tables used by the
Medicare Community Hospital Management System.

The database file (hospital.db) is created automatically the first
time the program runs, and all data persists between runs -- so the
system keeps working after the program is closed and reopened.
"""

import os
import sqlite3

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "hospital.db")


def get_connection():
    """Return a new SQLite connection with foreign keys enabled and
    rows accessible by column name (like a dictionary)."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create every table if it does not already exist. Safe to call
    every time the program starts."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username       TEXT UNIQUE NOT NULL,
            password_hash  TEXT NOT NULL,
            salt           TEXT NOT NULL,
            role           TEXT NOT NULL CHECK(role IN ('admin','receptionist','doctor','patient')),
            linked_id      TEXT,
            full_name      TEXT,
            access_code    TEXT UNIQUE,
            created_at     TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS receptionists (
            receptionist_id   TEXT PRIMARY KEY,
            full_name         TEXT NOT NULL,
            email             TEXT NOT NULL,
            phone             TEXT NOT NULL,
            date_added        TEXT NOT NULL
        )
    """)

    # --- lightweight migration for databases created by an earlier
    # version of this program, which didn't have full_name/access_code ---
    existing_cols = {row["name"] for row in cur.execute("PRAGMA table_info(users)")}
    if "full_name" not in existing_cols:
        cur.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
    if "access_code" not in existing_cols:
        cur.execute("ALTER TABLE users ADD COLUMN access_code TEXT")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id       TEXT PRIMARY KEY,
            full_name        TEXT NOT NULL,
            email            TEXT NOT NULL,
            phone            TEXT NOT NULL,
            dob              TEXT NOT NULL,
            gender           TEXT NOT NULL,
            address          TEXT,
            blood_group      TEXT,
            date_registered  TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id             TEXT PRIMARY KEY,
            full_name             TEXT NOT NULL,
            specialization        TEXT NOT NULL,
            email                 TEXT NOT NULL,
            phone                 TEXT NOT NULL,
            availability_status   TEXT NOT NULL DEFAULT 'Available',
            consultation_fee      REAL NOT NULL DEFAULT 50.00
        )
    """)

    doc_cols = {row["name"] for row in cur.execute("PRAGMA table_info(doctors)")}
    if "consultation_fee" not in doc_cols:
        cur.execute("ALTER TABLE doctors ADD COLUMN consultation_fee REAL NOT NULL DEFAULT 50.00")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id     TEXT PRIMARY KEY,
            patient_id         TEXT NOT NULL,
            doctor_id          TEXT NOT NULL,
            appointment_date   TEXT NOT NULL,
            appointment_time   TEXT NOT NULL,
            reason             TEXT,
            status             TEXT NOT NULL DEFAULT 'Scheduled',
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY (doctor_id)  REFERENCES doctors(doctor_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS medical_records (
            record_id       TEXT PRIMARY KEY,
            patient_id      TEXT NOT NULL,
            doctor_id       TEXT NOT NULL,
            diagnosis       TEXT,
            cause           TEXT,
            symptoms        TEXT,
            prescription    TEXT,
            avoid           TEXT,
            notes           TEXT,
            medical_fee     REAL NOT NULL DEFAULT 0.00,
            date_of_visit   TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY (doctor_id)  REFERENCES doctors(doctor_id)
        )
    """)

    # --- migration for medical_records created by an earlier version ---
    mr_cols = {row["name"] for row in cur.execute("PRAGMA table_info(medical_records)")}
    if "cause" not in mr_cols:
        cur.execute("ALTER TABLE medical_records ADD COLUMN cause TEXT")
    if "avoid" not in mr_cols:
        cur.execute("ALTER TABLE medical_records ADD COLUMN avoid TEXT")
    if "medical_fee" not in mr_cols:
        cur.execute("ALTER TABLE medical_records ADD COLUMN medical_fee REAL NOT NULL DEFAULT 0.00")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            bill_id            TEXT PRIMARY KEY,
            patient_id         TEXT NOT NULL,
            appointment_id     TEXT,
            record_id          TEXT,
            consultation_fee   REAL NOT NULL DEFAULT 0,
            medical_fee        REAL NOT NULL DEFAULT 0,
            lab_fee            REAL NOT NULL DEFAULT 0,
            medication_cost    REAL NOT NULL DEFAULT 0,
            other_charges      REAL NOT NULL DEFAULT 0,
            discount_percent   REAL NOT NULL DEFAULT 0,
            subtotal           REAL NOT NULL,
            total_amount       REAL NOT NULL,
            amount_paid        REAL NOT NULL DEFAULT 0,
            balance            REAL NOT NULL,
            date_created       TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )
    """)

    bill_cols = {row["name"] for row in cur.execute("PRAGMA table_info(bills)")}
    if "record_id" not in bill_cols:
        cur.execute("ALTER TABLE bills ADD COLUMN record_id TEXT")
    if "medical_fee" not in bill_cols:
        cur.execute("ALTER TABLE bills ADD COLUMN medical_fee REAL NOT NULL DEFAULT 0.00")

    conn.commit()
    conn.close()


def next_id(cursor, table, id_column, prefix, width=4):
    """Generate the next sequential ID for a table, e.g. P0001, P0002...
    Guarantees uniqueness since it is derived from the highest existing ID.
    """
    cursor.execute(f"SELECT {id_column} FROM {table} ORDER BY {id_column} DESC LIMIT 1")
    row = cursor.fetchone()
    if row is None:
        num = 1
    else:
        last_id = row[0]
        digits = "".join(ch for ch in last_id if ch.isdigit())
        num = int(digits) + 1 if digits else 1
    return f"{prefix}{num:0{width}d}"
