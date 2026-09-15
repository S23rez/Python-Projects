"""
seed.py
-------
Runs once at program startup and creates the built-in accounts if
they don't already exist:

  - 1 Admin       (username 's23rez', password given at handover)
  - 5 Doctors     (Pass codes Doc001 - Doc005, one per specialization)
  - 2 Receptionists (Pass codes Rec001 - Rec002)

Each block is independently idempotent, so re-running this on every
launch is safe -- it only ever fills in what's missing.
"""

import auth
import staff

ADMIN_USERNAME = "s23rez"
ADMIN_PASSWORD = "M3dicar3"

DEFAULT_DOCTORS = [
    # (full_name, specialization, email, phone, consultation_fee) -> becomes Doc001, Doc002, ...
    ("Diego Suarez", "Cardiology", "diego.suarez@medicarehospital.com", "08011122233", 150.0),
    ("Amara Chen", "Pediatrics", "amara.chen@medicarehospital.com", "08011122234", 80.0),
    ("Michael Okafor", "General Medicine", "michael.okafor@medicarehospital.com", "08011122235", 50.0),
    ("Elena Petrova", "Dermatology", "elena.petrova@medicarehospital.com", "08011122236", 100.0),
    ("Samuel Whitfield", "Dentistry", "samuel.whitfield@medicarehospital.com", "08011122237", 120.0),
]

DEFAULT_RECEPTIONISTS = [
    # (full_name, email, phone) -> becomes Rec001, Rec002
    ("Grace Adeyemi", "grace.adeyemi@medicarehospital.com", "08099911122"),
    ("Tunde Bakare", "tunde.bakare@medicarehospital.com", "08099911123"),
]


def bootstrap_defaults():
    _seed_admin()
    _seed_doctors()
    _seed_receptionists()


def _seed_admin():
    if not auth.username_exists(ADMIN_USERNAME):
        auth.create_user(ADMIN_USERNAME, ADMIN_PASSWORD, "admin", full_name="System Administrator")


def _seed_doctors():
    if auth.access_code_exists("Doc001"):
        return  # already seeded
    for name, specialization, email, phone, fee in DEFAULT_DOCTORS:
        staff.add_doctor(name, specialization, email, phone, consultation_fee=fee)


def _seed_receptionists():
    if auth.access_code_exists("Rec001"):
        return  # already seeded
    for name, email, phone in DEFAULT_RECEPTIONISTS:
        staff.add_receptionist(name, email, phone)
