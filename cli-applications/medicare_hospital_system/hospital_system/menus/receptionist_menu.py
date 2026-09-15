

import patients
import doctors
import appointments
import availability
import billing
import ui


def run(user):
    while True:
        ui.print_header(f"RECEPTIONIST MENU - logged in as {user['username']}")
        print(" 1. Register New Patient")
        print(" 2. View / Search Patients")
        print(" 3. View Doctors")
        print(" 4. Book Appointment")
        print(" 5. View / Search Appointments")
        print(" 6. Cancel Appointment")
        print(" 7. Reschedule Appointment")
        print(" 8. Billing")
        print(" 9. Reports")
        print(" 0. Logout")
        choice = ui.prompt("Choose an option")

        try:
            if choice == "1":
                _register_patient()
            elif choice == "2":
                _view_patients()
            elif choice == "3":
                ui.print_table(doctors.list_all_doctors(),
                                ["doctor_id", "full_name", "specialization", "consultation_fee", "availability_status"])
                ui.pause()
            elif choice == "4":
                _book_appointment()
            elif choice == "5":
                _view_appointments()
            elif choice == "6":
                aid = ui.prompt("Appointment ID to cancel")
                appointments.cancel_appointment(aid)
                ui.print_success(f"Appointment {aid} cancelled.")
                ui.pause()
            elif choice == "7":
                aid = ui.prompt("Appointment ID to reschedule")
                nd = ui.prompt("New date (YYYY-MM-DD)")
                nt = ui.prompt("New time (HH:MM)")
                appointments.reschedule_appointment(aid, nd, nt)
                ui.print_success(f"Appointment {aid} rescheduled.")
                ui.pause()
            elif choice == "8":
                _billing()
            elif choice == "9":
                from menus import reports_menu
                reports_menu.run(admin=False)
            elif choice == "0":
                print("Logging out...")
                return
            else:
                ui.print_error("Invalid option.")
        except ValueError as e:
            ui.print_error(str(e))
            ui.pause()


def _register_patient():
    ui.print_header("REGISTER NEW PATIENT")
    name = ui.prompt("Full name")
    email = ui.prompt("Email")
    phone = ui.prompt("Phone")
    dob = ui.prompt("Date of birth (YYYY-MM-DD)")
    gender = ui.prompt("Gender (Male/Female/Other)")
    address = ui.prompt("Address")
    blood_group = ui.prompt("Blood group")
    try:
        pid = patients.register_patient(name, email, phone, dob, gender, address, blood_group)
        ui.print_success(f"Patient registered with ID {pid}")
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


def _book_appointment():
    ui.print_header("BOOK APPOINTMENT")
    pid = ui.prompt("Patient ID")
    ui.print_table(doctors.list_all_doctors(), ["doctor_id", "full_name", "specialization", "consultation_fee", "availability_status"])
    did = ui.prompt("Doctor ID")

    doc = doctors.get_doctor(did)
    if not doc:
        ui.print_error(f"Doctor {did} not found.")
        ui.pause()
        return

    fee = doc["consultation_fee"] if "consultation_fee" in doc.keys() else 50.0
    print(f"\n[NOTICE] Dr. {doc['full_name']}'s Consultation Fee: {fee:.2f}")

    print(f"\nOpen slots for {did} over the next 7 days:")
    schedule = availability.get_upcoming_schedule(did, num_days=7)
    ui.print_schedule(schedule)

    date = ui.prompt("\nDate to book (YYYY-MM-DD)")
    try:
        open_slots = availability.get_available_slots(did, date)
    except ValueError as e:
        ui.print_error(str(e))
        ui.pause()
        return

    if not open_slots:
        ui.print_error(f"{did} has no open slots on {date} (closed day or fully booked).")
        ui.pause()
        return

    print(f"Open times on {date}: {', '.join(open_slots)}")
    time = ui.prompt("Time (HH:MM, pick one of the open times above)")
    reason = ui.prompt("Reason for appointment")
    try:
        appointment_id, bill_id, total_amount = appointments.book_appointment(
            pid, did, date, time, reason
        )
        ui.print_success(f"Appointment booked with ID {appointment_id}")
        ui.print_success(f"Bill {bill_id} created for this visit (Consultation Fee: {fee:.2f}) -- total due: {total_amount:.2f}")
    except ValueError as e:
        ui.print_error(str(e))
    ui.pause()


def _view_appointments():
    ui.print_header("APPOINTMENTS")
    print(" 1. View all")
    print(" 2. Search")
    print(" 3. By date")
    choice = ui.prompt("Choose an option")
    cols = ["appointment_id", "patient_id", "doctor_id", "appointment_date", "appointment_time", "status"]
    if choice == "1":
        ui.print_table(appointments.list_all_appointments(), cols)
    elif choice == "2":
        kw = ui.prompt("Search keyword")
        ui.print_table(appointments.search_appointments(kw), cols)
    elif choice == "3":
        d = ui.prompt("Date (YYYY-MM-DD)")
        ui.print_table(appointments.list_appointments_by_date(d), cols)
    ui.pause()


def _billing():
    while True:
        ui.print_header("BILLING")
        print(" 1. Generate a new bill (e.g. for lab work / medication, outside a booking)")
        print(" 2. View / Pay bills for a patient")
        print(" 3. Record a payment")
        print(" 0. Back")
        choice = ui.prompt("Choose an option")
        try:
            if choice == "1":
                pid = ui.prompt("Patient ID")
                consultation = ui.prompt_float("Consultation fee", default=0.0)
                med_fee = ui.prompt_float("Medical/Treatment fee", default=0.0)
                lab = ui.prompt_float("Laboratory fee", default=0.0)
                medication = ui.prompt_float("Medication cost", default=0.0)
                other = ui.prompt_float("Other charges", default=0.0)
                discount = ui.prompt_float("Discount percent", default=0.0)
                bill_id, subtotal, discount_amt, total = billing.generate_bill(
                    pid, consultation_fee=consultation, lab_fee=lab, medication_cost=medication,
                    other_charges=other, discount_percent=discount, medical_fee=med_fee
                )
                print(f"\n  Bill ID: {bill_id}")
                print(f"  Subtotal:  {subtotal:.2f}")
                print(f"  Discount:  -{discount_amt:.2f}")
                print(f"  Total due: {total:.2f}")
            elif choice == "2":
                pid = ui.prompt("Patient ID")
                ui.print_table(billing.list_bills_for_patient(pid),
                                ["bill_id", "consultation_fee", "medical_fee", "lab_fee", "medication_cost", "total_amount", "amount_paid", "balance", "date_created"])
            elif choice == "3":
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
