"""
patients.py
-----------
Patient registration, lookup and search.
"""

from datetime import datetime

import db
import validators


def register_patient(full_name, email, phone, dob, gender, address, blood_group):
    """Validate and store a new patient. Returns the new patient_id.
    Raises ValueError with a human-readable message if validation fails."""

    full_name = full_name.strip()
    email = email.strip()
    phone = phone.strip()
    dob = dob.strip()
    gender = gender.strip()
    blood_group = blood_group.strip().upper()

    if not full_name:
        raise ValueError("Full name is required.")
    if not validators.is_valid_email(email):
        raise ValueError(f"'{email}' is not a valid email address.")
    if not validators.is_valid_phone(phone):
        raise ValueError(f"'{phone}' is not a valid phone number (must be exactly 11 digits).")
    if not validators.is_valid_date(dob):
        raise ValueError("Date of birth must be in YYYY-MM-DD format.")
    if not validators.is_past_or_today(dob):
        raise ValueError("Date of birth cannot be in the future.")
    if gender.lower() not in ("male", "female", "other"):
        raise ValueError("Gender must be Male, Female or Other.")

    conn = db.get_connection()
    cur = conn.cursor()

    # Guard against duplicate patients being registered twice by email.
    existing = cur.execute(
        "SELECT patient_id FROM patients WHERE lower(email) = lower(?)", (email,)
    ).fetchone()
    if existing:
        conn.close()
        raise ValueError(f"A patient with email '{email}' is already registered (ID {existing['patient_id']}).")

    patient_id = db.next_id(cur, "patients", "patient_id", "P")

    # Duplicate-ID safety net (patient_id is the primary key, so SQLite
    # itself would reject a real duplicate -- this check just gives a
    # friendlier error message instead of a raw database exception).
    cur.execute("SELECT 1 FROM patients WHERE patient_id = ?", (patient_id,))
    if cur.fetchone():
        conn.close()
        raise ValueError(f"Patient ID {patient_id} already exists. Please try again.")

    date_registered = datetime.now().strftime("%Y-%m-%d %H:%M")

    cur.execute(
        """INSERT INTO patients
           (patient_id, full_name, email, phone, dob, gender, address, blood_group, date_registered)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (patient_id, full_name, email, phone, dob, gender, address, blood_group, date_registered),
    )
    conn.commit()
    conn.close()
    return patient_id


def get_patient(patient_id: str):
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
    conn.close()
    return row


def patient_exists(patient_id: str) -> bool:
    return get_patient(patient_id) is not None


def list_all_patients():
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM patients ORDER BY patient_id").fetchall()
    conn.close()
    return rows


def search_patients(keyword: str):
    """Search by ID, name, email or phone (case-insensitive, partial match)."""
    keyword = f"%{keyword.strip().lower()}%"
    conn = db.get_connection()
    rows = conn.execute(
        """SELECT * FROM patients
           WHERE lower(patient_id) LIKE ?
              OR lower(full_name) LIKE ?
              OR lower(email) LIKE ?
              OR phone LIKE ?
           ORDER BY patient_id""",
        (keyword, keyword, keyword, keyword),
    ).fetchall()
    conn.close()
    return rows


def patient_age(patient_row) -> int:
    return validators.calculate_age(patient_row["dob"])
