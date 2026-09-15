# Medicare Community Hospital Management System

A command-line Hospital Management System built in pure Python (standard
library only — `sqlite3`, `re`, `datetime`, `math`, `os`, `hashlib`).

## Requirements
- Python 3.8+
- No external packages to install.

## How to run
```
cd hospital_system
python3 main.py
```

The first time you run it, `hospital.db` (a SQLite file) is created
automatically in the same folder — this is what makes the system keep
working after you close and reopen the program. All data (patients,
doctors, appointments, records, bills, accounts) lives in that file.

## Getting started

**Only Patients can self-register.** Admin, Doctor and Receptionist accounts
cannot be created from the sign-up screen — this stops anyone from just
signing up as staff. Instead:

- The **Admin** account is built in automatically the first time you run
  the program:
  - Username: `s23rez`
  - Password: `M3dicar3`
- **5 Doctors** and **2 Receptionists** are also seeded automatically on
  first run, each with a **Pass code** instead of a username/password:

  | Pass | Name | Specialization |
  |---|---|---|
  | `Doc001` | Dr. Diego Suarez | Cardiology |
  | `Doc002` | Dr. Amara Chen | Pediatrics |
  | `Doc003` | Dr. Michael Okafor | General Medicine |
  | `Doc004` | Dr. Elena Petrova | Dermatology |
  | `Doc005` | Dr. Samuel Whitfield | Dentistry |

  | Pass | Name |
  |---|---|
  | `Rec001` | Grace Adeyemi |
  | `Rec002` | Tunde Bakare |

- The **Admin can add more doctors and receptionists** at any time from
  the Admin menu (Manage Doctors / Manage Receptionists → Add). Each new
  hire gets the next sequential Pass automatically (`Doc006`, `Doc007`,
  ... / `Rec003`, `Rec004`, ...), shown on screen once so the admin can
  hand it over. The Admin can also reissue a lost Pass, or remove a
  doctor/receptionist (which revokes their Pass immediately).

### Logging in
There's a single **Login** screen for everyone:
- **Admin / Patient** — enter your username, then your password.
- **Doctor / Receptionist** — just enter your **Pass** code (e.g.
  `Doc001` or `Rec002`); no separate username or password needed. The
  Pass *is* the credential.

The system detects the role from what you entered and greets you by
name, e.g. Pass `Doc001` logs in with *"Good morning, Doctor Suarez!"*

## Roles & permissions
| Role | Can do |
|---|---|
| **Admin** | Add/update/remove doctors and receptionists and issue their Pass codes, view/search all patients, manage all appointments, view any patient's medical history, view all bills & record payments, all reports (including revenue), view every user account. |
| **Receptionist** | Register patients, view doctors (read-only), book/view/search/cancel/reschedule appointments, generate bills & record payments, operational reports (no revenue figures, no doctor/receptionist management). |
| **Doctor** | View their own appointment schedule, look up a patient's medical history, create new medical records, update their own availability. Nothing outside their own patients/appointments. |
| **Patient** | Self-register, view their own profile, book/view/cancel/reschedule their own appointments, view their own medical history and bills. Nothing belonging to other patients. |

## Project structure
```
hospital_system/
├── main.py                 # entry point: welcome screen, signup/login, role routing
├── db.py                   # SQLite connection + schema (creates hospital.db)
├── auth.py                 # salted/hashed passwords, account creation, login
├── validators.py           # regex email/phone validation, date/age helpers (datetime)
├── patients.py              # patient registration, search, lookup
├── doctors.py               # doctor profile CRUD
├── availability.py           # NEW: computes a doctor's open slots for booking
├── receptionists.py         # receptionist profile CRUD
├── staff.py                 # ties a doctor/receptionist profile to a login Pass
├── seed.py                  # auto-creates Admin + 5 Doctors + 2 Receptionists on first run
├── appointments.py          # booking, conflict detection, cancel/reschedule
├── medical_records.py       # visit records, patient history
├── billing.py                # bill generation & payments (math module for rounding)
├── reports.py                 # report generation, saved as .txt files (os module)
├── ui.py                     # shared CLI input/output helpers
├── menus/
│   ├── admin_menu.py
│   ├── receptionist_menu.py
│   ├── doctor_menu.py
│   ├── patient_menu.py
│   └── reports_menu.py       # shared by admin & receptionist
└── reports/                   # created automatically the first time a report runs
```

## Key business rules implemented
- **No duplicate patient IDs** — IDs are auto-generated (`P0001`, `P0002`, ...)
  from the database itself, so collisions are structurally impossible; a
  duplicate-email check also stops the same person registering twice.
- **Email/phone validation** via `re` regular expressions.
- **Age calculation** via `datetime`, comparing today's date to date of birth.
- **No booking for a non-existent patient or doctor** — checked before insert.
- **No double-booking a doctor** — `appointments.py` checks for an existing
  `Scheduled` appointment for that doctor at the same date **and** time
  before allowing a new booking or a reschedule.
- **Billing math** uses the `math` module to round every currency figure to
  2 decimal places consistently (subtotal → discount → total → balance).
- **Reports** are written to the `reports/` folder; `os.path.exists` /
  `os.makedirs` are used to create the folder on first use, and existing
  report files are never silently overwritten (a numeric suffix is added).

## Doctor availability shown to patients
Patients (and receptionists booking on their behalf) now see a real
7-day schedule of open slots for a doctor before picking a date/time —
no more guessing and hitting a "doctor already booked" error. This
lives in **`availability.py`** (new file):

- Working hours are plain constants at the top of `availability.py`:
  Monday–Saturday, 09:00–17:00, 30-minute slots (`WORKING_DAYS`,
  `DAY_START`, `DAY_END`, `SLOT_MINUTES`) — edit these if the hospital's
  actual hours differ.
- `get_upcoming_schedule(doctor_id, num_days=7)` returns the next 7 days
  with each day's open slots (already-booked times removed, and for
  today, past times removed too).
- `get_available_slots(doctor_id, date_str)` returns just one day's open
  slots.
- Wired into `menus/patient_menu.py` and `menus/receptionist_menu.py`
  (`_book_appointment`): after picking a doctor, the 7-day schedule is
  printed, then the specific day's open times, before asking for a
  date/time to book.

- **Patients can now make payments** on their own bills (Patient menu →
  "Make a Payment"), which deducts from the balance immediately. A patient
  can only pay a bill that belongs to them.
- **Consultation fee is captured at booking time.** When a patient or
  receptionist books an appointment, they now enter the consultation fee
  right there, and a bill is created automatically and linked to that
  appointment — ready to be paid.
- **Medical records now capture "Cause of ailment" and "What the patient
  should avoid"** alongside diagnosis/symptoms/prescription/notes.
- **Doctors can edit a medical record** they created (Doctor menu → "Edit
  a Medical Record"). A doctor cannot edit another doctor's record.
- **Doctor availability is shown to patients** when choosing a doctor to
  book with (the doctor list now always includes availability status).
- Existing `hospital.db` files migrate automatically — no data is lost;
  the new columns are just added to it the next time you run the program.

## Notes
- Passwords/Pass codes are entered in plain sight (via `input()`) rather
  than hidden, to keep the program reliably runnable in any terminal.
  Under the hood every credential — including Pass codes — is stored as
  a salted PBKDF2-SHA256 hash, never as plain text.
- Dates use `YYYY-MM-DD` and times use 24-hour `HH:MM`.
- `seed.py` is idempotent: it's safe that it runs on every launch,
  it only fills in accounts that don't exist yet, so it won't duplicate
  the Admin/Doctors/Receptionists on subsequent runs.
