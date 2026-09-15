

import db
import doctors
import receptionists
import staff
import patients
import appointments
import medical_records
import billing
import reports
import ui


def run(user):
    while True:
        ui.print_header(f"ADMIN MENU - logged in as {user['username']}")
        print(" 1. Manage Doctors")
        print(" 2. Manage Receptionists")
        print(" 3. View / Search Patients")
        print(" 4. Manage Appointments")
        print(" 5. Medical Records")
        print(" 6. Billing")
        print(" 7. Reports")
        print(" 8. View All User Accounts")
        print(" 0. Logout")
        choice = ui.prompt("Choose an option")

        if choice == "1":
            _manage_doctors()
        elif choice == "2":
            _manage_receptionists()
        elif choice == "3":
            _view_patients()
        elif choice == "4":
            _manage_appointments()
        elif choice == "5":
            _medical_records()
        elif choice == "6":
            _billing()
        elif choice == "7":
            _reports()
        elif choice == "8":
            _view_accounts()
        elif choice == "0":
            print("Logging out...")
            return
        else:
            ui.print_error("Invalid option.")


def _manage_doctors():
    while True:
        ui.print_header("MANAGE DOCTORS")
        print(" 1. Add doctor (creates profile + issues a Pass)")
        print(" 2. View all doctors")
        print(" 3. Search doctor")
        print(" 4. Update doctor")
        print(" 5. Remove doctor (revokes their Pass)")
        print(" 6. Reissue a doctor's Pass")
        print(" 0. Back")
        choice = ui.prompt("Choose an option")

        try:
            if choice == "1":
                name = ui.prompt("Full name")
                print("Specializations:", ", ".join(doctors.SPECIALIZATIONS))
                spec = ui.prompt("Specialization")
                email = ui.prompt("Email")
                phone = ui.prompt("Phone")
                fee = ui.prompt_float("Consultation fee", default=50.0)
                doctor_id, access_code = staff.add_doctor(name, spec, email, phone, consultation_fee=fee)
                ui.print_success(f"Doctor added with ID {doctor_id} (Fee: {fee:.2f})")
                ui.print_success(f"Their login Pass is: {access_code}  (give this to Dr. {name})")
            elif choice == "2":
                ui.print_table(doctors.list_all_doctors(),
                                ["doctor_id", "full_name", "specialization", "consultation_fee", "email", "phone", "availability_status"])
            elif choice == "3":
                kw = ui.prompt("Search keyword (id/name/specialization/email)")
                ui.print_table(doctors.search_doctors(kw),
                                ["doctor_id", "full_name", "specialization", "consultation_fee", "email", "phone", "availability_status"])
            elif choice == "4":
                did = ui.prompt("Doctor ID to update")
                print("Leave a field blank to keep it unchanged.")
                fields = {
                    "full_name": ui.prompt("New full name"),
                    "specialization": ui.prompt("New specialization"),
                    "email": ui.prompt("New email"),
                    "phone": ui.prompt("New phone"),
                    "consultation_fee": ui.prompt("New consultation fee"),
                    "availability_status": ui.prompt("New availability (Available/Unavailable)"),
                }
                doctors.update_doctor(did, **fields)
                ui.print_success(f"Doctor {did} updated.")
            elif choice == "5":
                did = ui.prompt("Doctor ID to remove")
                if ui.confirm(f"Really remove doctor {did}? This also revokes their Pass"):
                    staff.remove_doctor(did)
                    ui.print_success(f"Doctor {did} removed and their Pass revoked.")
            elif choice == "6":
                did = ui.prompt("Doctor ID")
                new_code = staff.reissue_doctor_pass(did)
                ui.print_success(f"New Pass for {did}: {new_code}  (the old one no longer works)")
            elif choice == "0":
                return
            else:
                ui.print_error("Invalid option.")
        except ValueError as e:
            ui.print_error(str(e))
        ui.pause()


def _manage_receptionists():
    while True:
        ui.print_header("MANAGE RECEPTIONISTS")
        print(" 1. Add receptionist (creates profile + issues a Pass)")
        print(" 2. View all receptionists")
        print(" 3. Remove receptionist (revokes their Pass)")
        print(" 4. Reissue a receptionist's Pass")
        print(" 0. Back")
        choice = ui.prompt("Choose an option")

        try:
            if choice == "1":
                name = ui.prompt("Full name")
                email = ui.prompt("Email")
                phone = ui.prompt("Phone")
                receptionist_id, access_code = staff.add_receptionist(name, email, phone)
                ui.print_success(f"Receptionist added with ID {receptionist_id}")
                ui.print_success(f"Their login Pass is: {access_code}  (give this to {name})")
            elif choice == "2":
                ui.print_table(receptionists.list_all_receptionists(),
                                ["receptionist_id", "full_name", "email", "phone"])
            elif choice == "3":
                rid = ui.prompt("Receptionist ID to remove")
                if ui.confirm(f"Really remove receptionist {rid}? This also revokes their Pass"):
                    staff.remove_receptionist(rid)
                    ui.print_success(f"Receptionist {rid} removed and their Pass revoked.")
            elif choice == "4":
                rid = ui.prompt("Receptionist ID")
                new_code = staff.reissue_receptionist_pass(rid)
                ui.print_success(f"New Pass for {rid}: {new_code}  (the old one no longer works)")
            elif choice == "0":
                return
            else:
                ui.print_error("Invalid option.")
        except ValueError as e:
            ui.print_error(str(e))
        ui.pause()


def _view_patients():
    ui.print_header("PATIENTS")
    print(" 1. View all")
    print(" 2. Search")
    choice = ui.prompt("Choose an option")
    cols = ["patient_id", "full_name", "email", "phone", "dob", "gender", "blood_group"]
    if choice == "1":
        ui.print_table(patients.list_all_patients(), cols)
    elif choice == "2":
        kw = ui.prompt("Search keyword")
        ui.print_table(patients.search_patients(kw), cols)
    ui.pause()


def _manage_appointments():
    while True:
        ui.print_header("MANAGE APPOINTMENTS")
        print(" 1. View all appointments")
        print(" 2. Search appointments")
        print(" 3. View appointments by date")
        print(" 4. Cancel an appointment")
        print(" 5. Reschedule an appointment")
        print(" 0. Back")
        choice = ui.prompt("Choose an option")
        cols = ["appointment_id", "patient_id", "doctor_id", "appointment_date", "appointment_time", "status"]
        try:
            if choice == "1":
                ui.print_table(appointments.list_all_appointments(), cols)
            elif choice == "2":
                kw = ui.prompt("Search keyword")
                ui.print_table(appointments.search_appointments(kw), cols)
            elif choice == "3":
                d = ui.prompt("Date (YYYY-MM-DD)")
                ui.print_table(appointments.list_appointments_by_date(d), cols)
            elif choice == "4":
                aid = ui.prompt("Appointment ID to cancel")
                appointments.cancel_appointment(aid)
                ui.print_success(f"Appointment {aid} cancelled.")
            elif choice == "5":
                aid = ui.prompt("Appointment ID to reschedule")
                nd = ui.prompt("New date (YYYY-MM-DD)")
                nt = ui.prompt("New time (HH:MM)")
                appointments.reschedule_appointment(aid, nd, nt)
                ui.print_success(f"Appointment {aid} rescheduled.")
            elif choice == "0":
                return
            else:
                ui.print_error("Invalid option.")
        except ValueError as e:
            ui.print_error(str(e))
        ui.pause()


def _medical_records():
    ui.print_header("MEDICAL RECORDS")
    pid = ui.prompt("Patient ID to view history")
    try:
        records = medical_records.get_patient_history(pid)
        ui.print_table(records, ["record_id", "doctor_id", "diagnosis", "cause", "medical_fee", "avoid", "date_of_visit"])
    except Exception as e:
        ui.print_error(str(e))
    ui.pause()


def _billing():
    while True:
        ui.print_header("BILLING")
        print(" 1. View all bills")
        print(" 2. Record a payment")
        print(" 0. Back")
        choice = ui.prompt("Choose an option")
        try:
            if choice == "1":
                ui.print_table(billing.list_all_bills(),
                                ["bill_id", "patient_id", "consultation_fee", "medical_fee", "total_amount", "amount_paid", "balance", "date_created"])
            elif choice == "2":
                bid = ui.prompt("Bill ID")
                amt = ui.prompt_float("Payment amount")
                paid, balance = billing.record_payment(bid, amt)
                ui.print_success(f"Payment recorded. Paid so far: {paid:.2f}, balance: {balance:.2f}")
            elif choice == "0":
                return
            else:
                ui.print_error("Invalid option.")
        except ValueError as e:
            ui.print_error(str(e))
        ui.pause()


def _reports():
    from menus import reports_menu
    reports_menu.run(admin=True)


def _view_accounts():
    ui.print_header("ALL USER ACCOUNTS")
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT user_id, username, role, linked_id, full_name, access_code, created_at "
        "FROM users ORDER BY user_id"
    ).fetchall()
    conn.close()
    ui.print_table(rows, ["user_id", "username", "role", "linked_id", "full_name", "access_code", "created_at"])
    ui.pause()
