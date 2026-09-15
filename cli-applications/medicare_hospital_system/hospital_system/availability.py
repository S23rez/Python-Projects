"""
availability.py
----------------
Computes which appointment slots a doctor still has open, so a patient
(or receptionist) can see real available dates/times before booking --
instead of guessing a date/time and only finding out it's taken after
trying to book.

The clinic's working days/hours and slot length are plain constants
below -- change these if the hospital's actual schedule differs.
"""

from datetime import datetime, timedelta

import doctors
import appointments

# Monday=0 ... Sunday=6. This clinic is open Monday-Saturday, closed Sunday.
WORKING_DAYS = (0, 1, 2, 3, 4, 5)
DAY_START = "09:00"
DAY_END = "17:00"
SLOT_MINUTES = 30

DATE_FMT = "%Y-%m-%d"
TIME_FMT = "%H:%M"


def _generate_day_slots():
    """Every possible HH:MM slot in a single working day, e.g.
    ['09:00', '09:30', '10:00', ..., '16:30']."""
    start = datetime.strptime(DAY_START, TIME_FMT)
    end = datetime.strptime(DAY_END, TIME_FMT)
    slots = []
    current = start
    while current < end:
        slots.append(current.strftime(TIME_FMT))
        current += timedelta(minutes=SLOT_MINUTES)
    return slots


ALL_DAY_SLOTS = _generate_day_slots()


def is_working_day(date_str: str) -> bool:
    d = datetime.strptime(date_str.strip(), DATE_FMT)
    return d.weekday() in WORKING_DAYS


def get_available_slots(doctor_id: str, date_str: str):
    """Return the list of HH:MM slots still open for this doctor on this
    date. Already-booked ('Scheduled') times are excluded; if the date
    is today, times already in the past are excluded too. Returns an
    empty list for a closed day (e.g. Sunday) or a fully-booked day."""
    doctor_id = doctor_id.strip()
    date_str = date_str.strip()

    if not doctors.doctor_exists(doctor_id):
        raise ValueError(f"Doctor {doctor_id} does not exist.")
    if not is_working_day(date_str):
        return []

    booked_times = {
        a["appointment_time"]
        for a in appointments.list_appointments_for_doctor(doctor_id)
        if a["appointment_date"] == date_str and a["status"] == "Scheduled"
    }

    slots = [s for s in ALL_DAY_SLOTS if s not in booked_times]

    today = datetime.today().strftime(DATE_FMT)
    if date_str == today:
        now = datetime.now().strftime(TIME_FMT)
        slots = [s for s in slots if s > now]

    return slots


def get_upcoming_schedule(doctor_id: str, num_days: int = 7, start_date: str = None):
    """Return an ordered list of (date_str, [available_slots]) covering
    the next `num_days` days (including closed/fully-booked days, shown
    with an empty list), starting today or from start_date."""
    doctor_id = doctor_id.strip()
    if not doctors.doctor_exists(doctor_id):
        raise ValueError(f"Doctor {doctor_id} does not exist.")

    start = datetime.strptime(start_date.strip(), DATE_FMT) if start_date else datetime.today()
    schedule = []
    for i in range(num_days):
        date_str = (start + timedelta(days=i)).strftime(DATE_FMT)
        schedule.append((date_str, get_available_slots(doctor_id, date_str)))
    return schedule
