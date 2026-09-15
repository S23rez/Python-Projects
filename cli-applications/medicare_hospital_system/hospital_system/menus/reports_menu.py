
import reports
import ui


def run(admin: bool):
    while True:
        ui.print_header("REPORTS")
        print(" 1. Total number of patients")
        print(" 2. Total number of doctors")
        print(" 3. Appointments for a specific date")
        print(" 4. Number of appointments per doctor")
        if admin:
            print(" 5. Total revenue")
        print(" 6. Most common medical conditions")
        print(" 7. Patient medical history")
        print(" 0. Back")
        choice = ui.prompt("Choose an option")

        try:
            if choice == "1":
                content, path = reports.report_total_patients()
                _show(content, path)
            elif choice == "2":
                content, path = reports.report_total_doctors()
                _show(content, path)
            elif choice == "3":
                d = ui.prompt("Date (YYYY-MM-DD)")
                content, path = reports.report_appointments_by_date(d)
                _show(content, path)
            elif choice == "4":
                content, path = reports.report_appointments_per_doctor()
                _show(content, path)
            elif choice == "5" and admin:
                content, path = reports.report_total_revenue()
                _show(content, path)
            elif choice == "6":
                content, path = reports.report_common_conditions()
                _show(content, path)
            elif choice == "7":
                pid = ui.prompt("Patient ID")
                content, path = reports.report_patient_history(pid)
                _show(content, path)
            elif choice == "0":
                return
            else:
                ui.print_error("Invalid option.")
        except ValueError as e:
            ui.print_error(str(e))
        ui.pause()


def _show(content, path):
    ui.print_line()
    print(content)
    ui.print_line()
    print(f"Saved to: {path}")
