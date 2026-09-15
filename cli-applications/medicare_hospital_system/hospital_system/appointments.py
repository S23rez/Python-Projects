"""
appointments.py
----------------
Booking, viewing, searching, cancelling and rescheduling appointments.
Uses datetime to compare dates/times and prevent double-booking a doctor.
"""

from datetime import datetime

import db
import validators
import patients
import doctors
import billing

ACTIVE_STATUSES = ("Scheduled",)  # statuses that block a time slot


def _check_conflict(cur, doctor_id, appointment_date, appointment_time, exclude_id=None):
    query = """SELECT appointment_id FROM appointments
               WHERE doctor_id = ? AND appointment_date = ? AND appointment_time = ?
                 AND status = 'Scheduled'"""
    params = [doctor_id, appointment_date, appointment_time]
    if exclude_id:
        query += " AND appointment_id != ?"
        params.append(exclude_id)
    return cur.execute(query, params).fetchone()


def book_appointment(patient_id, doctor_id, appointment_date, appointment_time, reason, consultation_fee=None):
    patient_id = patient_id.strip()
    doctor_id = doctor_id.strip()
    appointment_date = appointment_date.strip()
    appointment_time = appointment_time.strip()

    if not patients.patient_exists(patient_id):
        raise ValueError(f"Patient {patient_id} does not exist.")
    doc = doctors.get_doctor(doctor_id)
    if not doc:
        raise ValueError(f"Doctor {doctor_id} does not exist.")
    if not validators.is_valid_date(appointment_date):
        raise ValueError("Appointment date must be in YYYY-MM-DD format.")
    if not validators.is_today_or_future(appointment_date):
        raise ValueError("Appointment date cannot be in the past.")
    if not validators.is_valid_time(appointment_time):
        raise ValueError("Appointment time must be in HH:MM (24-hour) format.")

    if consultation_fee is None:
        consultation_fee = doc["consultation_fee"] if "consultation_fee" in doc.keys() else 50.0
    else:
        try:
            consultation_fee = float(consultation_fee)
        except (ValueError, TypeError):
            raise ValueError("Consultation fee must be a valid number.")

    if consultation_fee < 0:
        raise ValueError("Consultation fee cannot be negative.")

    conn = db.get_connection()
    cur = conn.cursor()

    if _check_conflict(cur, doctor_id, appointment_date, appointment_time):
        conn.close()
        raise ValueError(
            f"Doctor {doctor_id} already has an appointment on {appointment_date} at {appointment_time}."
        )

    appointment_id = db.next_id(cur, "appointments", "appointment_id", "A")
    cur.execute(
        """INSERT INTO appointments
           (appointment_id, patient_id, doctor_id, appointment_date, appointment_time, reason, status)
           VALUES (?, ?, ?, ?, ?, ?, 'Scheduled')""",
        (appointment_id, patient_id, doctor_id, appointment_date, appointment_time, reason.strip()),
    )
    conn.commit()
    conn.close()

    # The consultation fee is captured at booking time and immediately
    # turned into a bill tied to this appointment, so it shows up right
    # away under the patient's bills (ready to be paid).
    bill_id, subtotal, discount_amount, total_amount = billing.generate_bill(
        patient_id, consultation_fee=consultation_fee, appointment_id=appointment_id
    )

    return appointment_id, bill_id, total_amount


def get_appointment(appointment_id: str):
    conn = db.get_connection()
    row = conn.execute(
        "SELECT * FROM appointments WHERE appointment_id = ?", (appointment_id,)
    ).fetchone()
    conn.close()
    return row


def list_all_appointments():
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT * FROM appointments ORDER BY appointment_date, appointment_time"
    ).fetchall()
    conn.close()
    return rows


def list_appointments_for_patient(patient_id: str):
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT * FROM appointments WHERE patient_id = ? ORDER BY appointment_date, appointment_time",
        (patient_id,),
    ).fetchall()
    conn.close()
    return rows


def list_appointments_for_doctor(doctor_id: str):
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT * FROM appointments WHERE doctor_id = ? ORDER BY appointment_date, appointment_time",
        (doctor_id,),
    ).fetchall()
    conn.close()
    return rows


def list_appointments_by_date(appointment_date: str):
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT * FROM appointments WHERE appointment_date = ? ORDER BY appointment_time",
        (appointment_date,),
    ).fetchall()
    conn.close()
    return rows


def search_appointments(keyword: str):
    keyword = f"%{keyword.strip().lower()}%"
    conn = db.get_connection()
    rows = conn.execute(
        """SELECT * FROM appointments
           WHERE lower(appointment_id) LIKE ?
              OR lower(patient_id) LIKE ?
              OR lower(doctor_id) LIKE ?
              OR lower(status) LIKE ?
           ORDER BY appointment_date, appointment_time""",
        (keyword, keyword, keyword, keyword),
    ).fetchall()
    conn.close()
    return rows


def cancel_appointment(appointment_id: str):
    appt = get_appointment(appointment_id)
    if appt is None:
        raise ValueError(f"Appointment {appointment_id} not found.")
    if appt["status"] == "Cancelled":
        raise ValueError(f"Appointment {appointment_id} is already cancelled.")
    conn = db.get_connection()
    conn.execute("UPDATE appointments SET status = 'Cancelled' WHERE appointment_id = ?", (appointment_id,))
    conn.commit()
    conn.close()


def reschedule_appointment(appointment_id: str, new_date: str, new_time: str):
    appt = get_appointment(appointment_id)
    if appt is None:
        raise ValueError(f"Appointment {appointment_id} not found.")
    if appt["status"] != "Scheduled":
        raise ValueError(f"Only 'Scheduled' appointments can be rescheduled (this one is '{appt['status']}').")

    new_date = new_date.strip()
    new_time = new_time.strip()
    if not validators.is_valid_date(new_date):
        raise ValueError("New date must be in YYYY-MM-DD format.")
    if not validators.is_today_or_future(new_date):
        raise ValueError("New date cannot be in the past.")
    if not validators.is_valid_time(new_time):
        raise ValueError("New time must be in HH:MM (24-hour) format.")

    conn = db.get_connection()
    cur = conn.cursor()
    if _check_conflict(cur, appt["doctor_id"], new_date, new_time, exclude_id=appointment_id):
        conn.close()
        raise ValueError(f"Doctor {appt['doctor_id']} already has an appointment on {new_date} at {new_time}.")

    cur.execute(
        "UPDATE appointments SET appointment_date = ?, appointment_time = ?, status = 'Rescheduled' "
        "WHERE appointment_id = ?",
        (new_date, new_time, appointment_id),
    )
    # Rescheduled appointments remain "active" for conflict purposes,
    # so restore status to Scheduled after the move.
    cur.execute("UPDATE appointments SET status = 'Scheduled' WHERE appointment_id = ?", (appointment_id,))
    conn.commit()
    conn.close()
