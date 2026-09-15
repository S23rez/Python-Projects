

import db
import auth
import patients
import doctors
import seed
import ui
import validators

from menus import admin_menu, receptionist_menu, doctor_menu, patient_menu

ROLE_MENUS = {
    "admin": admin_menu.run,
    "receptionist": receptionist_menu.run,
    "doctor": doctor_menu.run,
    "patient": patient_menu.run,
}

VALID_BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")
def sign_up():
    """Patients only -- Admin, Doctor and Receptionist accounts are
    issued by the Admin, never self-registered."""
    ui.print_header("PATIENT SIGN UP")
    if not ui.confirm("Continue with sign up"):
        return

        # Username validation
    while True:
        username = ui.prompt("Choose a username").strip()
        if not username:
            ui.print_error("Username cannot be empty.")
            continue
        if auth.username_exists(username):
            ui.print_error(f"Username '{username}' is already taken.")
            continue
        break

    # Password validation
    while True:
        password = ui.prompt("Choose a password (min 4 characters)")
        if len(password) >= 4:
            break
        ui.print_error("Password must be at least 4 characters long.")

    print("\nPlease provide your patient registration details:")

    # Full name validation
    while True:
        name = ui.prompt("Full name").strip()
        if name:
            break
        ui.print_error("Full name cannot be empty.")

    #Email Validation
    while True:
        email = ui.prompt("Email").strip()
        if not validators.is_valid_email(email):
            ui.print_error(f"'{email}' is not a valid email address.")
        else:
            conn = db.get_connection()
            existing = conn.execute(
                "SELECT 1 FROM patients WHERE lower(email) = lower(?)", (email,)
            ).fetchone()
            conn.close()
            if existing:
                ui.print_error(f"A patient with email '{email}' is already registered.")
            else:
                break

    #Phone Validation
    while True:
        phone = ui.prompt("Phone")
        if validators.is_valid_phone(phone):
            break
        ui.print_error(f"'{phone}' is not a valid phone number (must be exactly 11 digits).")

        # Date of birth validation
    while True:
            dob = ui.prompt("Date of birth (YYYY-MM-DD)").strip()
            if not validators.is_valid_date(dob):
                ui.print_error("Date of birth must be in valid YYYY-MM-DD format.")
            elif not validators.is_past_or_today(dob):
                ui.print_error("Date of birth cannot be in the future.")
            else:
                break

    # Gender validation
    while True:
        gender = ui.prompt("Gender (Male/Female/Other)").strip()
        if gender.lower() in ("male", "female", "other"):
            gender = gender.capitalize()
            break
        ui.print_error("Gender must be Male, Female, or Other.")

    address = ui.prompt("Address").strip()

    # Blood group validation
    while True:
            blood_group = ui.prompt("Blood group (e.g. A+, O-, B+)").strip().upper()
            if blood_group in VALID_BLOOD_GROUPS:
                break
            ui.print_error(f"'{blood_group}' is invalid. Allowed: {', '.join(VALID_BLOOD_GROUPS)}")

    try:
        patient_id = patients.register_patient(name, email, phone, dob, gender, address, blood_group)
        auth.create_user(username, password, "patient", patient_id, full_name=name)
        ui.print_success(f"Account created! You can now log in as '{username}'.")
        ui.print_success(f"Your patient ID is {patient_id} -- keep it for reference.")
    except ValueError as e:
        ui.print_error(str(e))

    ui.pause()


def _greet(user) -> str:
    """Build the personalised welcome line shown right after login."""
    greeting = ui.time_greeting()
    role = user["role"]

    if role == "doctor":
        last_name = (user["full_name"] or "").split()[-1] if user["full_name"] else user["username"]
        return f"{greeting}, Doctor {last_name}!"
    if role == "receptionist":
        first_name = (user["full_name"] or user["username"]).split()[0]
        return f"{greeting}, {first_name}!"
    if role == "admin":
        return f"{greeting}, Admin!"
    # patient
    first_name = (user["full_name"] or user["username"]).split()[0]
    return f"{greeting}, {first_name}!"


def log_in():
    ui.print_header("LOGIN")
    print("Enter your username and password/Passcode")
    entry = ui.prompt("Username or Pass code")

    # Try Pass-code login first (Doctor / Receptionist) -- single factor.
    user = auth.login_by_pass(entry)

    # Otherwise fall back to username + password (Admin / Patient).
    if user is None:
        password = ui.prompt("Password")
        user = auth.login(entry, password)

    if user is None:
        ui.print_error("Invalid credentials.")
        ui.pause()
        return

    ui.print_success(_greet(user))
    menu_fn = ROLE_MENUS.get(user["role"])
    if menu_fn:
        menu_fn(user)
    else:
        ui.print_error("Unknown role on this account. Contact an administrator.")
        ui.pause()


def main():
    db.init_db()
    seed.bootstrap_defaults()
    while True:
        ui.print_header("MEDICARE COMMUNITY HOSPITAL MANAGEMENT SYSTEM")
        print(" 1. Login")
        print(" 2. Sign Up ")
        print(" 0. Exit")
        choice = ui.prompt("Choose an option")

        if choice == "1":
            log_in()
        elif choice == "2":
            sign_up()
        elif choice == "0":
            print("\nGoodbye! Your data has been saved to hospital.db.\n")
            break
        else:
            ui.print_error("Invalid option.")


if __name__ == "__main__":
    main()
