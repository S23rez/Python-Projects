"""
reports.py
----------
Generates hospital-wide reports and saves them as text files.
Uses the os module to check for / create the reports folder and to
avoid silently overwriting an existing report file.
"""

import os
from collections import Counter
from datetime import datetime

import db
import patients
import doctors
import appointments
import medical_records
import billing

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")


def _ensure_reports_folder():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)


def _save_report(filename: str, content: str) -> str:
    """Write content to reports/<filename>. If the file already exists,
    a numeric suffix is added so previous reports are never overwritten."""
    _ensure_reports_folder()
    path = os.path.join(REPORTS_DIR, filename)

    if os.path.exists(path):
        name, ext = os.path.splitext(filename)
        counter = 2
        while os.path.exists(os.path.join(REPORTS_DIR, f"{name}_{counter}{ext}")):
            counter += 1
        path = os.path.join(REPORTS_DIR, f"{name}_{counter}{ext}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def report_total_patients():
    all_patients = patients.list_all_patients()
    lines = [
        "MEDICARE COMMUNITY HOSPITAL - PATIENT COUNT REPORT",
        f"Generated: {_timestamp()}",
        "-" * 55,
        f"Total registered patients: {len(all_patients)}",
        "",
    ]
    for p in all_patients:
        lines.append(f"  {p['patient_id']}  {p['full_name']}  (registered {p['date_registered']})")
    content = "\n".join(lines)
    path = _save_report("total_patients.txt", content)
    return content, path


def report_total_doctors():
    all_doctors = doctors.list_all_doctors()
    lines = [
        "MEDICARE COMMUNITY HOSPITAL - DOCTOR COUNT REPORT",
        f"Generated: {_timestamp()}",
        "-" * 55,
        f"Total doctors on staff: {len(all_doctors)}",
        "",
    ]
    for d in all_doctors:
        lines.append(f"  {d['doctor_id']}  {d['full_name']}  ({d['specialization']}) - {d['availability_status']}")
    content = "\n".join(lines)
    path = _save_report("total_doctors.txt", content)
    return content, path


def report_appointments_by_date(date_str: str):
    appts = appointments.list_appointments_by_date(date_str)
    lines = [
        "MEDICARE COMMUNITY HOSPITAL - APPOINTMENTS FOR " + date_str,
        f"Generated: {_timestamp()}",
        "-" * 55,
        f"Total appointments on {date_str}: {len(appts)}",
        "",
    ]
    for a in appts:
        lines.append(
            f"  {a['appointment_id']}  {a['appointment_time']}  "
            f"Patient {a['patient_id']} with Doctor {a['doctor_id']}  [{a['status']}]"
        )
    content = "\n".join(lines)
    path = _save_report(f"appointments_{date_str}.txt", content)
    return content, path


def report_appointments_per_doctor():
    all_doctors = doctors.list_all_doctors()
    lines = [
        "MEDICARE COMMUNITY HOSPITAL - APPOINTMENTS PER DOCTOR",
        f"Generated: {_timestamp()}",
        "-" * 55,
    ]
    for d in all_doctors:
        count = len(appointments.list_appointments_for_doctor(d["doctor_id"]))
        lines.append(f"  {d['doctor_id']}  {d['full_name']} ({d['specialization']}): {count} appointment(s)")
    content = "\n".join(lines)
    path = _save_report("appointments_per_doctor.txt", content)
    return content, path


def report_total_revenue():
    all_bills = billing.list_all_bills()
    total = billing.total_revenue()
    lines = [
        "MEDICARE COMMUNITY HOSPITAL - REVENUE REPORT",
        f"Generated: {_timestamp()}",
        "-" * 55,
        f"Total bills issued: {len(all_bills)}",
        f"Total revenue collected: {total:.2f}",
        "",
    ]
    for b in all_bills:
        lines.append(
            f"  {b['bill_id']}  Patient {b['patient_id']}  "
            f"Total: {b['total_amount']:.2f}  Paid: {b['amount_paid']:.2f}  Balance: {b['balance']:.2f}"
        )
    content = "\n".join(lines)
    path = _save_report("total_revenue.txt", content)
    return content, path


def report_common_conditions(top_n: int = 10):
    records = medical_records.all_records()
    counts = Counter(r["diagnosis"].strip().title() for r in records if r["diagnosis"] and r["diagnosis"].strip())
    lines = [
        "MEDICARE COMMUNITY HOSPITAL - MOST COMMON MEDICAL CONDITIONS",
        f"Generated: {_timestamp()}",
        "-" * 55,
    ]
    if not counts:
        lines.append("No medical records on file yet.")
    else:
        for condition, count in counts.most_common(top_n):
            lines.append(f"  {condition}: {count} case(s)")
    content = "\n".join(lines)
    path = _save_report("common_conditions.txt", content)
    return content, path


def report_patient_history(patient_id: str):
    patient = patients.get_patient(patient_id)
    if patient is None:
        raise ValueError(f"Patient {patient_id} not found.")
    history = medical_records.get_patient_history(patient_id)
    lines = [
        f"MEDICARE COMMUNITY HOSPITAL - MEDICAL HISTORY FOR {patient['full_name']} ({patient_id})",
        f"Generated: {_timestamp()}",
        "-" * 55,
    ]
    if not history:
        lines.append("No medical records on file for this patient.")
    for r in history:
        lines.extend([
            f"  Visit date: {r['date_of_visit']}   Record: {r['record_id']}   Doctor: {r['doctor_id']}",
            f"    Diagnosis:    {r['diagnosis']}",
            f"    Cause:        {r['cause']}",
            f"    Symptoms:     {r['symptoms']}",
            f"    Prescription: {r['prescription']}",
            f"    Avoid:        {r['avoid']}",
            f"    Notes:        {r['notes']}",
            "",
        ])
    content = "\n".join(lines)
    path = _save_report(f"history_{patient_id}.txt", content)
    return content, path
