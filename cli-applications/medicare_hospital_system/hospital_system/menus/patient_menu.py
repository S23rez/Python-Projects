
import patients
import doctors
import appointments
import availability
import medical_records
import billing
import validators
import ui


def run(user):
    patient_id = user["linked_id"]
    patient = patients.get_patient(patient_id)
    if patient is None:
        ui.print_error("Your patient profile could not be found. Contact the front desk.")
        return

    while True:
        ui.print_header(f"PATIENT MENU - {patient['full_name']} ({patient_id})")
        print(" 1. View My Profile")
        print(" 2. Book an Appointment")
        print(" 3. View My Appointments")
        print(" 4. Cancel an Appointment")
        print(" 5. Reschedule an Appointment")
        print(" 6. View My Medical History")
        print(" 7. View My Bills")
        print(" 8. Make a Payment")
        print(" 0. Logout")
        choice = ui.prompt("Choose an option")

        try:
            if choice == "1":
                _view_profile(patient)
            elif choice == "2":
                _book_appointment(patient_id)
            elif choice == "3":
                ui.print_table(
                    appointments.list_appointments_for_patient(patient_id),
                    ["appointment_id", "doctor_id", "appointment_date", "appointment_time", "reason", "status"],
                )
                ui.pause()
            elif choice == "4":
                aid = ui.prompt("Appointment ID to cancel")
                _cancel_own(patient_id, aid)
            elif choice == "5":
                aid = ui.prompt("Appointment ID to reschedule")
                _reschedule_own(patient_id, aid)
            elif choice == "6":
                ui.print_table(
                    medical_records.get_patient_history(patient_id),
                    ["record_id", "date_of_visit", "doctor_id", "diagnosis", "cause", "prescription", "avoid"],
                )
                ui.pause()
            elif choice == "7":
                ui.print_table(
                    billing.list_bills_for_patient(patient_id),
                    ["bill_id", "consultation_fee", "medical_fee", "total_amount", "amount_paid", "balance", "date_created"],
                )
                ui.pause()
            elif choice == "8":
                _make_payment(patient_id)
            elif choice == "0":
                print("Logging out...")
                return
            else:
                ui.print_error("Invalid option.")
        except ValueError as e:
            ui.print_error(str(e))
            ui.pause()


def _view_profile(patient):
    ui.print_header("MY PROFILE")
    age = validators.calculate_age(patient["dob"])
    for field in ("patient_id", "full_name", "email", "phone", "dob", "gender", "address", "blood_group"):
        print(f"  {field:16}: {patient[field]}")
    print(f"  {'age':16}: {age}")
    ui.pause()


def _book_appointment(patient_id):
    ui.print_header("BOOK APPOINTMENT")
    print("Doctors and their current availability:")
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
            patient_id, did, date, time, reason
        )
        ui.print_success(f"Appointment booked with ID {appointment_id}")
        ui.print_success(f"Bill {bill_id} created for this visit (Consultation Fee: {fee:.2f}) -- total due: {total_amount:.2f}")
    except ValueError as e:
        ui.print_error(str(e))
    ui.pause()


def _cancel_own(patient_id, appointment_id):
    appt = appointments.get_appointment(appointment_id)
    if appt is None or appt["patient_id"] != patient_id:
        ui.print_error("That appointment does not belong to you.")
    else:
        appointments.cancel_appointment(appointment_id)
        ui.print_success(f"Appointment {appointment_id} cancelled.")
    ui.pause()


def _reschedule_own(patient_id, appointment_id):
    appt = appointments.get_appointment(appointment_id)
    if appt is None or appt["patient_id"] != patient_id:
        ui.print_error("That appointment does not belong to you.")
        ui.pause()
        return
    nd = ui.prompt("New date (YYYY-MM-DD)")
    nt = ui.prompt("New time (HH:MM)")
    try:
        appointments.reschedule_appointment(appointment_id, nd, nt)
        ui.print_success(f"Appointment {appointment_id} rescheduled.")
    except ValueError as e:
        ui.print_error(str(e))
    ui.pause()


def _make_payment(patient_id):
    ui.print_header("MAKE A PAYMENT")
    my_bills = billing.list_bills_for_patient(patient_id)
    outstanding = [b for b in my_bills if b["balance"] > 0]
    if not outstanding:
        print("  You have no outstanding balance on any bill.")
        ui.pause()
        return

    ui.print_table(outstanding, ["bill_id", "consultation_fee", "medical_fee", "total_amount", "amount_paid", "balance", "date_created"])
    bill_id = ui.prompt("Bill ID to pay")

    bill = billing.get_bill(bill_id)
    if bill is None or bill["patient_id"] != patient_id:
        ui.print_error("That bill does not belong to you.")
        ui.pause()
        return

    amount = ui.prompt_float("Payment amount", default=bill["balance"])
    try:
        paid, balance = billing.record_payment(bill_id, amount)
        ui.print_success(f"Payment of {amount:.2f} recorded. Total paid: {paid:.2f}, remaining balance: {balance:.2f}")
    except ValueError as e:
        ui.print_error(str(e))
    ui.pause()
