"""
validators.py
-------------
Regex-based validation for emails and phone numbers, plus datetime
helpers for ages, dates and times.
"""

import re
from datetime import datetime

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+$")
PHONE_PATTERN = re.compile(r"^\d{11}$")

DATE_FMT = "%Y-%m-%d"
TIME_FMT = "%H:%M"


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email.strip()))


def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_PATTERN.match(phone.strip()))


def is_valid_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str.strip(), DATE_FMT)
        return True
    except ValueError:
        return False


def is_valid_time(time_str: str) -> bool:
    try:
        datetime.strptime(time_str.strip(), TIME_FMT)
        return True
    except ValueError:
        return False


def is_past_or_today(date_str: str) -> bool:
    """True if the date is today or earlier (used for date of birth)."""
    dob = datetime.strptime(date_str.strip(), DATE_FMT)
    return dob.date() <= datetime.today().date()


def is_today_or_future(date_str: str) -> bool:
    """True if the date is today or later (used for booking appointments)."""
    d = datetime.strptime(date_str.strip(), DATE_FMT)
    return d.date() >= datetime.today().date()


def calculate_age(dob_str: str) -> int:
    """Calculate age in whole years from a YYYY-MM-DD date of birth."""
    dob = datetime.strptime(dob_str.strip(), DATE_FMT)
    today = datetime.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age
