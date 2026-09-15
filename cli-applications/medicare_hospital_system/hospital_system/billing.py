"""
billing.py
----------
Generates bills and records payments. Uses the math module to keep
all money values rounded to exactly 2 decimal places without the
floating-point surprises of plain round().
"""

import math
from datetime import datetime

import db
import patients


def round_currency(amount: float) -> float:
    """Round half-up to 2 decimal places using math.floor (avoids
    banker's-rounding surprises from the built-in round())."""
    return math.floor(amount * 100 + 0.5) / 100


def generate_bill(patient_id, consultation_fee=0, lab_fee=0, medication_cost=0,
                   other_charges=0, discount_percent=0, appointment_id=None,
                   record_id=None, medical_fee=0):
    patient_id = patient_id.strip()
    if not patients.patient_exists(patient_id):
        raise ValueError(f"Patient {patient_id} does not exist.")

    fees = [consultation_fee, lab_fee, medication_cost, other_charges, medical_fee]
    for f in fees:
        if f < 0:
            raise ValueError("Fees cannot be negative.")
    if not (0 <= discount_percent <= 100):
        raise ValueError("Discount percent must be between 0 and 100.")

    subtotal = round_currency(sum(fees))
    discount_amount = round_currency(subtotal * (discount_percent / 100))
    total_amount = round_currency(subtotal - discount_amount)
    balance = total_amount  # nothing paid yet

    conn = db.get_connection()
    cur = conn.cursor()
    bill_id = db.next_id(cur, "bills", "bill_id", "B")
    cur.execute(
        """INSERT INTO bills
           (bill_id, patient_id, appointment_id, record_id, consultation_fee, medical_fee, lab_fee, medication_cost,
            other_charges, discount_percent, subtotal, total_amount, amount_paid, balance, date_created)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
        (bill_id, patient_id, appointment_id, record_id, consultation_fee, medical_fee, lab_fee, medication_cost,
         other_charges, discount_percent, subtotal, total_amount, balance,
         datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()
    return bill_id, subtotal, discount_amount, total_amount


def get_bill(bill_id: str):
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM bills WHERE bill_id = ?", (bill_id,)).fetchone()
    conn.close()
    return row


def get_bill_by_appointment(appointment_id: str):
    if not appointment_id:
        return None
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM bills WHERE appointment_id = ?", (appointment_id,)).fetchone()
    conn.close()
    return row


def create_or_update_medical_bill(patient_id, doctor_id, record_id, medical_fee=0.0, appointment_id=None):
    """Creates a bill or updates an existing appointment bill with medical_fee and consultation_fee."""
    import doctors

    medical_fee = round_currency(float(medical_fee))
    if medical_fee < 0:
        raise ValueError("Medical fee cannot be negative.")

    conn = db.get_connection()
    existing_bill = None

    if appointment_id:
        existing_bill = conn.execute("SELECT * FROM bills WHERE appointment_id = ?", (appointment_id,)).fetchone()
    if not existing_bill:
        # Check if there is an unlinked bill for this patient created today or recently
        existing_bill = conn.execute(
            "SELECT * FROM bills WHERE patient_id = ? AND record_id IS NULL ORDER BY date_created DESC LIMIT 1",
            (patient_id,)
        ).fetchone()

    if existing_bill:
        bill_id = existing_bill["bill_id"]
        c_fee = existing_bill["consultation_fee"]
        # If consultation fee was 0 on existing bill, fetch doctor's fee
        if c_fee == 0:
            doc = doctors.get_doctor(doctor_id)
            c_fee = doc["consultation_fee"] if doc and "consultation_fee" in doc.keys() else 50.0

        m_fee = medical_fee
        lab_fee = existing_bill["lab_fee"]
        med_cost = existing_bill["medication_cost"]
        other = existing_bill["other_charges"]
        disc_pct = existing_bill["discount_percent"]
        paid = existing_bill["amount_paid"]

        subtotal = round_currency(c_fee + m_fee + lab_fee + med_cost + other)
        disc_amt = round_currency(subtotal * (disc_pct / 100))
        total_amt = round_currency(subtotal - disc_amt)
        new_balance = round_currency(total_amt - paid)

        conn.execute(
            """UPDATE bills
               SET record_id = ?, consultation_fee = ?, medical_fee = ?,
                   subtotal = ?, total_amount = ?, balance = ?
               WHERE bill_id = ?""",
            (record_id, c_fee, m_fee, subtotal, total_amt, new_balance, bill_id),
        )
        conn.commit()
        conn.close()
        return bill_id, total_amt, new_balance
    else:
        conn.close()
        doc = doctors.get_doctor(doctor_id)
        c_fee = doc["consultation_fee"] if doc and "consultation_fee" in doc.keys() else 50.0
        bill_id, subtotal, disc_amt, total_amt = generate_bill(
            patient_id=patient_id,
            consultation_fee=c_fee,
            medical_fee=medical_fee,
            appointment_id=appointment_id,
            record_id=record_id,
        )
        return bill_id, total_amt, total_amt


def record_payment(bill_id: str, amount: float):
    bill = get_bill(bill_id)
    if bill is None:
        raise ValueError(f"Bill {bill_id} not found.")
    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")
    if amount > bill["balance"] + 1e-9:
        raise ValueError(f"Payment of {amount} exceeds remaining balance of {bill['balance']}.")

    new_paid = round_currency(bill["amount_paid"] + amount)
    new_balance = round_currency(bill["total_amount"] - new_paid)

    conn = db.get_connection()
    conn.execute(
        "UPDATE bills SET amount_paid = ?, balance = ? WHERE bill_id = ?",
        (new_paid, new_balance, bill_id),
    )
    conn.commit()
    conn.close()
    return new_paid, new_balance


def list_bills_for_patient(patient_id: str):
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT * FROM bills WHERE patient_id = ? ORDER BY date_created DESC", (patient_id,)
    ).fetchall()
    conn.close()
    return rows


def list_all_bills():
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM bills ORDER BY date_created DESC").fetchall()
    conn.close()
    return rows


def total_revenue() -> float:
    conn = db.get_connection()
    row = conn.execute("SELECT COALESCE(SUM(amount_paid), 0) AS total FROM bills").fetchone()
    conn.close()
    return round_currency(row["total"])
