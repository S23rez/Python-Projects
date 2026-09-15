"""
test_system.py
--------------
Automated unit tests for Medicare Hospital System rebuild.
Validates doctor consultation fees, appointment auto-billing,
medical record fee integration, patient payment, and receptionist payment.
"""

import os
import sqlite3
import unittest
from datetime import datetime, timedelta

# Ensure we use a clean test database
import db

# Override DB path for isolated testing
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_hospital.db")
db.DB_PATH = TEST_DB_PATH

import auth
import doctors
import patients
import staff
import appointments
import medical_records
import billing


class TestMedicareHospitalSystem(unittest.TestCase):

    def setUp(self):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        db.init_db()

    def tearDown(self):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_doctor_consultation_fees(self):
        # Add doctor with custom consultation fee
        doc_id = doctors.add_doctor(
            full_name="Dr. Sarah Connor",
            specialization="Cardiology",
            email="sarah.connor@test.com",
            phone="08012345678",
            consultation_fee=250.0,
        )
        doc = doctors.get_doctor(doc_id)
        self.assertEqual(doc["consultation_fee"], 250.0)

        # Update consultation fee
        doctors.update_doctor(doc_id, consultation_fee=300.0)
        updated_doc = doctors.get_doctor(doc_id)
        self.assertEqual(updated_doc["consultation_fee"], 300.0)

        # Rejects negative fee
        with self.assertRaises(ValueError):
            doctors.add_doctor(
                full_name="Dr. Bad Fee",
                specialization="Pediatrics",
                email="bad.fee@test.com",
                phone="08012345679",
                consultation_fee=-50.0,
            )

    def test_appointment_booking_and_billing_flow(self):
        # Register a doctor with fee 120.0
        doc_id = doctors.add_doctor(
            full_name="Dr. John Smith",
            specialization="General Medicine",
            email="john.smith@test.com",
            phone="08011112222",
            consultation_fee=120.0,
        )

        # Register a patient
        pat_id = patients.register_patient(
            full_name="Alice Johnson",
            email="alice@test.com",
            phone="08033334444",
            dob="1995-05-15",
            gender="Female",
            address="123 Main St",
            blood_group="O+",
        )

        # Book appointment without specifying consultation fee (should auto-use doctor's 120.0 fee)
        future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        appt_id, bill_id, total_amount = appointments.book_appointment(
            patient_id=pat_id,
            doctor_id=doc_id,
            appointment_date=future_date,
            appointment_time="10:00",
            reason="Routine Checkup",
        )

        self.assertIsNotNone(appt_id)
        self.assertIsNotNone(bill_id)
        self.assertEqual(total_amount, 120.0)

        # Check bill details
        bill = billing.get_bill(bill_id)
        self.assertEqual(bill["patient_id"], pat_id)
        self.assertEqual(bill["consultation_fee"], 120.0)
        self.assertEqual(bill["medical_fee"], 0.0)
        self.assertEqual(bill["total_amount"], 120.0)
        self.assertEqual(bill["balance"], 120.0)

        # Doctor creates a medical record with medical_fee = 80.0
        rec_id, updated_bill_id, rec_total, rec_balance = medical_records.create_record(
            patient_id=pat_id,
            doctor_id=doc_id,
            diagnosis="Mild Hypertension",
            symptoms="Headache",
            prescription="Antihypertensive meds",
            notes="Follow up in 2 weeks",
            cause="Stress",
            avoid="Excess salt",
            medical_fee=80.0,
            appointment_id=appt_id,
        )

        self.assertEqual(bill_id, updated_bill_id)
        self.assertEqual(rec_total, 200.0)  # 120.0 consultation + 80.0 medical fee
        self.assertEqual(rec_balance, 200.0)

        # Patient makes payment of 100.0
        paid_1, bal_1 = billing.record_payment(bill_id, 100.0)
        self.assertEqual(paid_1, 100.0)
        self.assertEqual(bal_1, 100.0)

        # Receptionist pays remaining balance of 100.0
        paid_2, bal_2 = billing.record_payment(bill_id, 100.0)
        self.assertEqual(paid_2, 200.0)
        self.assertEqual(bal_2, 0.0)

    def test_direct_medical_record_creation(self):
        # Register doctor with fee 90.0
        doc_id = doctors.add_doctor(
            full_name="Dr. Gregory House",
            specialization="Dermatology",
            email="house@test.com",
            phone="08055556666",
            consultation_fee=90.0,
        )

        # Register patient
        pat_id = patients.register_patient(
            full_name="Bob Miller",
            email="bob@test.com",
            phone="08077778888",
            dob="1988-11-20",
            gender="Male",
            address="456 Elm St",
            blood_group="A+",
        )

        # Doctor creates record directly without prior booked appointment
        rec_id, bill_id, total_amount, balance = medical_records.create_record(
            patient_id=pat_id,
            doctor_id=doc_id,
            diagnosis="Eczema",
            symptoms="Rash",
            prescription="Topical cream",
            notes="Apply twice daily",
            medical_fee=45.0,
        )

        # Bill should combine doctor consultation fee (90.0) and medical fee (45.0) -> 135.0 total
        bill = billing.get_bill(bill_id)
        self.assertEqual(bill["consultation_fee"], 90.0)
        self.assertEqual(bill["medical_fee"], 45.0)
        self.assertEqual(bill["total_amount"], 135.0)
        self.assertEqual(bill["balance"], 135.0)


if __name__ == "__main__":
    unittest.main()
