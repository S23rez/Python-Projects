
from datetime import datetime

import doctors
import appointments
import medical_records
import patients
import ui


def run(user):
    doctor_id = user["linked_id"]
    doctor = doctors.get_doctor(doctor_id)
    if doctor is None:
        ui.print_error("Your doctor profile could not be found. Contact an administrator.")
        return

    while True:
        ui.print_header(f"DOCTOR MENU - Dr. {doctor['full_name']} ({doctor_id})")
        print(" 1. View My Appointments")
        print(" 2. View a Patient's Medical History")
        print(" 3. Create a Medical Record")
        print(" 4. Edit a Medical Record")
        print(" 5. Update My Availability")
        print(" 0. Logout")
        choice = ui.prompt("Choose an option")

        try:
            if choice == "1":
                ui.print_table(
                    appointments.list_appointments_for_doctor(doctor_id),
                    ["appointment_id", "patient_id", "appointment_date", "appointment_time", "reason", "status"],
                )
                ui.pause()
            elif choice == "2":
                pid = ui.prompt("Patient ID")
                if not patients.patient_exists(pid):
                    ui.print_error(f"Patient {pid} not found.")
                else:
                    ui.print_table(
                        medical_records.get_patient_history(pid),
                        ["record_id", "date_of_visit", "diagnosis", "cause", "symptoms", "prescription", "avoid"],
                    )
                ui.pause()
            elif choice == "3":
                _create_record(doctor_id)
            elif choice == "4":
                _edit_record(doctor_id)
            elif choice == "5":
                new_status = ui.prompt("New availability status (Available/Unavailable)")
                doctors.update_doctor(doctor_id, availability_status=new_status)
                ui.print_success("Availability updated.")
                ui.pause()
            elif choice == "0":
                print("Logging out...")
                return
            else:
                ui.print_error("Invalid option.")
        except ValueError as e:
            ui.print_error(str(e))
            ui.pause()


def _create_record(doctor_id):
    ui.print_header("NEW MEDICAL RECORD")
    pid = ui.prompt("Patient ID")
    appt_id = ui.prompt("Appointment ID (optional, press Enter to skip)").strip() or None
    diagnosis = ui.prompt("Diagnosis")
    cause = ui.prompt("Cause of ailment")
    symptoms = ui.prompt("Symptoms")
    prescription = ui.prompt("Prescription")
    avoid = ui.prompt("What the patient should avoid")
    notes = ui.prompt("Notes")
    med_fee = ui.prompt_float("Medical/Treatment fee for this visit", default=0.0)
    date_of_visit = ui.prompt("Date of visit (YYYY-MM-DD, blank = today)")
    if not date_of_visit:
        date_of_visit = datetime.now().strftime("%Y-%m-%d")
    try:
        record_id, bill_id, total_amount, balance = medical_records.create_record(
            pid, doctor_id, diagnosis, symptoms, prescription, notes, date_of_visit,
            cause=cause, avoid=avoid, medical_fee=med_fee, appointment_id=appt_id
        )
        ui.print_success(f"Medical record created with ID {record_id}")
        ui.print_success(f"Patient bill {bill_id} generated/updated -- Total: {total_amount:.2f}, Balance Due: {balance:.2f}")
    except ValueError as e:
        ui.print_error(str(e))
    ui.pause()


def _edit_record(doctor_id):
    ui.print_header("EDIT MEDICAL RECORD")
    record_id = ui.prompt("Record ID to edit")
    record = medical_records.get_record(record_id)
    if record is None:
        ui.print_error(f"Medical record {record_id} not found.")
        ui.pause()
        return

    curr_med_fee = record["medical_fee"] if "medical_fee" in record.keys() else 0.0
    print("\nCurrent values (leave a field blank to keep it unchanged):")
    print(f"  Diagnosis:    {record['diagnosis']}")
    print(f"  Cause:        {record['cause']}")
    print(f"  Symptoms:     {record['symptoms']}")
    print(f"  Prescription: {record['prescription']}")
    print(f"  Avoid:        {record['avoid']}")
    print(f"  Notes:        {record['notes']}")
    print(f"  Medical Fee:  {curr_med_fee:.2f}\n")

    fields = {
        "diagnosis": ui.prompt("New diagnosis"),
        "cause": ui.prompt("New cause of ailment"),
        "symptoms": ui.prompt("New symptoms"),
        "prescription": ui.prompt("New prescription"),
        "avoid": ui.prompt("New 'what to avoid'"),
        "notes": ui.prompt("New notes"),
        "medical_fee": ui.prompt("New medical fee (or Enter to keep)"),
    }
    try:
        medical_records.update_record(record_id, doctor_id, **fields)
        ui.print_success(f"Medical record {record_id} updated.")
    except ValueError as e:
        ui.print_error(str(e))
    ui.pause()
