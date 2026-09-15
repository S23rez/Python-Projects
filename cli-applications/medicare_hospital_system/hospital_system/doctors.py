"""
doctors.py
----------
Add, view, search, update and remove doctors.
"""

import db
import validators

SPECIALIZATIONS = (
    "General Medicine",
    "Pediatrics",
    "Cardiology",
    "Dermatology",
    "Dentistry",
)


def add_doctor(full_name, specialization, email, phone, consultation_fee=50.0, availability_status="Available"):
    full_name = full_name.strip()
    specialization = specialization.strip()
    email = email.strip()
    phone = phone.strip()
    try:
        consultation_fee = float(consultation_fee)
    except (ValueError, TypeError):
        raise ValueError("Consultation fee must be a valid number.")

    if not full_name:
        raise ValueError("Full name is required.")
    if specialization not in SPECIALIZATIONS:
        raise ValueError(f"Specialization must be one of: {', '.join(SPECIALIZATIONS)}.")
    if not validators.is_valid_email(email):
        raise ValueError(f"'{email}' is not a valid email address.")
    if not validators.is_valid_phone(phone):
        raise ValueError(f"'{phone}' is not a valid phone number (must be exactly 11 digits).")
    if availability_status not in ("Available", "Unavailable"):
        raise ValueError("Availability status must be 'Available' or 'Unavailable'.")
    if consultation_fee < 0:
        raise ValueError("Consultation fee cannot be negative.")

    conn = db.get_connection()
    cur = conn.cursor()

    existing = cur.execute(
        "SELECT doctor_id FROM doctors WHERE lower(email) = lower(?)", (email,)
    ).fetchone()
    if existing:
        conn.close()
        raise ValueError(f"A doctor with email '{email}' already exists (ID {existing['doctor_id']}).")

    doctor_id = db.next_id(cur, "doctors", "doctor_id", "D")
    cur.execute(
        """INSERT INTO doctors (doctor_id, full_name, specialization, email, phone, availability_status, consultation_fee)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (doctor_id, full_name, specialization, email, phone, availability_status, consultation_fee),
    )
    conn.commit()
    conn.close()
    return doctor_id


def get_doctor(doctor_id: str):
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM doctors WHERE doctor_id = ?", (doctor_id,)).fetchone()
    conn.close()
    return row


def doctor_exists(doctor_id: str) -> bool:
    return get_doctor(doctor_id) is not None


def list_all_doctors():
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM doctors ORDER BY doctor_id").fetchall()
    conn.close()
    return rows


def search_doctors(keyword: str):
    keyword = f"%{keyword.strip().lower()}%"
    conn = db.get_connection()
    rows = conn.execute(
        """SELECT * FROM doctors
           WHERE lower(doctor_id) LIKE ?
              OR lower(full_name) LIKE ?
              OR lower(specialization) LIKE ?
              OR lower(email) LIKE ?
           ORDER BY doctor_id""",
        (keyword, keyword, keyword, keyword),
    ).fetchall()
    conn.close()
    return rows


def update_doctor(doctor_id: str, **fields):
    """Update any subset of: full_name, specialization, email, phone, availability_status, consultation_fee."""
    if not doctor_exists(doctor_id):
        raise ValueError(f"Doctor {doctor_id} not found.")

    allowed = {"full_name", "specialization", "email", "phone", "availability_status", "consultation_fee"}
    updates = {}
    for k, v in fields.items():
        if k in allowed and v not in (None, ""):
            if k == "consultation_fee":
                try:
                    fee_val = float(v)
                    if fee_val < 0:
                        raise ValueError("Consultation fee cannot be negative.")
                    updates[k] = fee_val
                except (ValueError, TypeError) as e:
                    if "negative" in str(e):
                        raise
                    raise ValueError("Consultation fee must be a valid number.")
            else:
                updates[k] = v.strip() if isinstance(v, str) else v

    if not updates:
        raise ValueError("No valid fields supplied to update.")

    if "specialization" in updates and updates["specialization"] not in SPECIALIZATIONS:
        raise ValueError(f"Specialization must be one of: {', '.join(SPECIALIZATIONS)}.")
    if "email" in updates and not validators.is_valid_email(updates["email"]):
        raise ValueError(f"'{updates['email']}' is not a valid email address.")
    if "phone" in updates and not validators.is_valid_phone(updates["phone"]):
        raise ValueError(f"'{updates['phone']}' is not a valid phone number (must be exactly 11 digits).")
    if "availability_status" in updates and updates["availability_status"] not in ("Available", "Unavailable"):
        raise ValueError("Availability status must be 'Available' or 'Unavailable'.")

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values()) + [doctor_id]

    conn = db.get_connection()
    conn.execute(f"UPDATE doctors SET {set_clause} WHERE doctor_id = ?", values)
    conn.commit()
    conn.close()


def remove_doctor(doctor_id: str):
    if not doctor_exists(doctor_id):
        raise ValueError(f"Doctor {doctor_id} not found.")
    conn = db.get_connection()
    cur = conn.cursor()
    active = cur.execute(
        "SELECT COUNT(*) AS c FROM appointments WHERE doctor_id = ? AND status = 'Scheduled'",
        (doctor_id,),
    ).fetchone()["c"]
    if active:
        conn.close()
        raise ValueError(
            f"Cannot remove doctor {doctor_id}: {active} scheduled appointment(s) still reference them. "
            "Cancel or reassign those appointments first."
        )
    cur.execute("DELETE FROM doctors WHERE doctor_id = ?", (doctor_id,))
    conn.commit()
    conn.close()