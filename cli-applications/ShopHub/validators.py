import re
from datetime import datetime

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
# Strictly requires exactly 11 numeric digits
PHONE_REGEX = re.compile(r"^\d{11}$")
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def prompt_non_empty(prompt_text: str) -> str:
    while True:
        val = input(prompt_text).strip()
        if val:
            return val
        print("[-] Input cannot be blank. Please try again.")

def prompt_email(prompt_text: str = "Email: ") -> str:
    while True:
        email = input(prompt_text).strip()
        if EMAIL_REGEX.match(email):
            return email
        print("[-] Invalid email address format (e.g., user@domain.com).")

def prompt_phone(prompt_text: str = "Phone Number (Must be exactly 11 digits): ") -> str:
    while True:
        phone = input(prompt_text).strip()
        if PHONE_REGEX.match(phone):
            return phone
        print("[-] Invalid phone number. Phone number must be exactly 11 numeric digits.")

def prompt_password(prompt_text: str = "Choose a Password (more than 8 and less than 12 characters): ") -> str:
    while True:
        pwd = input(prompt_text).strip()
        if 8 < len(pwd) < 12:
            return pwd
        print(f"[-] Invalid password length ({len(pwd)} characters). Password must be strictly between 9 and 11 characters long.")

def prompt_positive_float(prompt_text: str) -> float:
    while True:
        val = input(prompt_text).strip()
        try:
            num = float(val)
            if num > 0:
                return round(num, 2)
            print("[-] Amount must be greater than zero.")
        except ValueError:
            print("[-] Invalid number. Please enter a valid decimal.")

def prompt_positive_int(prompt_text: str) -> int:
    while True:
        val = input(prompt_text).strip()
        try:
            num = int(val)
            if num > 0:
                return num
            print("[-] Quantity must be greater than zero.")
        except ValueError:
            print("[-] Invalid integer. Please enter whole digits.")

def prompt_date(prompt_text: str) -> str:
    while True:
        val = input(prompt_text).strip()
        if DATE_REGEX.match(val):
            try:
                datetime.strptime(val, "%Y-%m-%d")
                return val
            except ValueError:
                pass
        print("[-] Invalid date. Format must strictly follow YYYY-MM-DD.")