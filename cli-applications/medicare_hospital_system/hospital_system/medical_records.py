"""
medical_records.py
-------------------
Doctors create medical records after a visit and can review a
patient's previous medical history.
"""

from datetime import datetime

import db
import patients
import doctors
import billing


def create_record(patient_id, doctor_id, diagnosis, symptoms, prescription, notes,
                   date_of_visit=None, cause="", avoid="", medical_fee=0.0, appointment_id=None):
    patient_id = patient_id.strip()
    doctor_id = doctor_id.strip()

    if not patients.patient_exists(patient_id):
        raise ValueError(f"Patient {patient_id} does not exist.")
    if not doctors.doctor_exists(doctor_id):
        raise ValueError(f"Doctor {doctor_id} does not exist.")
    if not diagnosis.strip():
        raise ValueError("Diagnosis is required.")

    try:
        medical_fee = float(medical_fee)
    except (ValueError, TypeError):
        raise ValueError("Medical fee must be a valid number.")

    if medical_fee < 0:
        raise ValueError("Medical fee cannot be negative.")

    date_of_visit = (date_of_visit or datetime.now().strftime("%Y-%m-%d")).strip()

    conn = db.get_connection()
    cur = conn.cursor()
    record_id = db.next_id(cur, "medical_records", "record_id", "MR")
    cur.execute(
        """INSERT INTO medical_records
           (record_id, patient_id, doctor_id, diagnosis, cause, symptoms, prescription, avoid, notes, medical_fee, date_of_visit)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (record_id, patient_id, doctor_id, diagnosis.strip(), cause.strip(), symptoms.strip(),
         prescription.strip(), avoid.strip(), notes.strip(), medical_fee, date_of_visit),
    )
    conn.commit()
    conn.close()

    # Create or update billing for this medical record
    bill_id, total_amount, balance = billing.create_or_update_medical_bill(
        patient_id=patient_id,
        doctor_id=doctor_id,
        record_id=record_id,
        medical_fee=medical_fee,
        appointment_id=appointment_id,
    )

    return record_id, bill_id, total_amount, balance


def get_record(record_id: str):
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM medical_records WHERE record_id = ?", (record_id,)).fetchone()
    conn.close()
    return row


def update_record(record_id: str, doctor_id: str, **fields):
    """Let a doctor edit a medical record -- restricted to records they
    personally created, so one doctor can't rewrite another's notes."""
    record = get_record(record_id)
    if record is None:
        raise ValueError(f"Medical record {record_id} not found.")
    if record["doctor_id"] != doctor_id:
        raise ValueError("You can only edit medical records you created yourself.")

    allowed = {"diagnosis", "cause", "symptoms", "prescription", "avoid", "notes", "medical_fee"}
    updates = {}
    for k, v in fields.items():
        if k in allowed and v not in (None, ""):
            if k == "medical_fee":
                try:
                    fee_val = float(v)
                    if fee_val < 0:
                        raise ValueError("Medical fee cannot be negative.")
                    updates[k] = fee_val
                except (ValueError, TypeError) as e:
                    if "negative" in str(e):
                        raise
                    raise ValueError("Medical fee must be a valid number.")
            else:
                updates[k] = v.strip() if isinstance(v, str) else v

    if not updates:
        raise ValueError("No fields supplied to update.")

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values()) + [record_id]

    conn = db.get_connection()
    conn.execute(f"UPDATE medical_records SET {set_clause} WHERE record_id = ?", values)
    conn.commit()
    conn.close()

    if "medical_fee" in updates:
        billing.create_or_update_medical_bill(
            patient_id=record["patient_id"],
            doctor_id=doctor_id,
            record_id=record_id,
            medical_fee=updates["medical_fee"]
        )


def get_patient_history(patient_id: str):
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT * FROM medical_records WHERE patient_id = ? ORDER BY date_of_visit DESC",
        (patient_id,),
    ).fetchall()
    conn.close()
    return rows


def get_records_by_doctor(doctor_id: str):
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT * FROM medical_records WHERE doctor_id = ? ORDER BY date_of_visit DESC",
        (doctor_id,),
    ).fetchall()
    conn.close()
    return rows


def all_records():
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM medical_records ORDER BY date_of_visit DESC").fetchall()
    conn.close()
    return rows
