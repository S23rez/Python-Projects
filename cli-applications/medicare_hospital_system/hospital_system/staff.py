"""
staff.py
--------
Bridges the doctor/receptionist profile tables with their login
accounts, so adding a staff member always does both steps at once:
create the profile, then issue them a Pass. Only the Admin (and the
one-time seed script) can call these -- there is no self-signup path
for doctors or receptionists.
"""

import auth
import doctors
import receptionists


def add_doctor(full_name, specialization, email, phone, consultation_fee=50.0, availability_status="Available"):
    """Create a doctor profile and issue their login Pass in one step.
    Returns (doctor_id, access_code)."""
    doctor_id = doctors.add_doctor(full_name, specialization, email, phone, consultation_fee=consultation_fee, availability_status=availability_status)
    access_code = auth.create_staff_account("doctor", doctor_id, full_name)
    return doctor_id, access_code


def add_receptionist(full_name, email, phone):
    """Create a receptionist profile and issue their login Pass in one step.
    Returns (receptionist_id, access_code)."""
    receptionist_id = receptionists.add_receptionist(full_name, email, phone)
    access_code = auth.create_staff_account("receptionist", receptionist_id, full_name)
    return receptionist_id, access_code


def remove_doctor(doctor_id: str):
    """Remove a doctor's profile and revoke their Pass together."""
    doctors.remove_doctor(doctor_id)
    auth.remove_staff_account("doctor", doctor_id)


def remove_receptionist(receptionist_id: str):
    """Remove a receptionist's profile and revoke their Pass together."""
    receptionists.remove_receptionist(receptionist_id)
    auth.remove_staff_account("receptionist", receptionist_id)


def reissue_doctor_pass(doctor_id: str) -> str:
    if not doctors.doctor_exists(doctor_id):
        raise ValueError(f"Doctor {doctor_id} not found.")
    return auth.reissue_pass("doctor", doctor_id)


def reissue_receptionist_pass(receptionist_id: str) -> str:
    if not receptionists.receptionist_exists(receptionist_id):
        raise ValueError(f"Receptionist {receptionist_id} not found.")
    return auth.reissue_pass("receptionist", receptionist_id)
