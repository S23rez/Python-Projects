"""
ui.py
-----
Tiny helpers so every menu prints and reads input the same way.
"""

from datetime import datetime


def time_greeting() -> str:
    """'Good morning' / 'Good afternoon' / 'Good evening' based on the clock."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def prompt(label: str) -> str:
    return input(f"{label}: ").strip()


def prompt_float(label: str, default: float = 0.0) -> float:
    raw = input(f"{label} [{default}]: ").strip()
    if raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        print("  Not a number, using default.")
        return default


def confirm(label: str) -> bool:
    return input(f"{label} (y/n): ").strip().lower() == "y"


def print_header(title: str):
    print("\n" + "=" * 60)
    print(title.center(60))
    print("=" * 60)


def print_line():
    print("-" * 60)


def print_error(message: str):
    print(f"  [ERROR] {message}")


def print_success(message: str):
    print(f"  [OK] {message}")


def print_table(rows, columns):
    """rows: iterable of sqlite3.Row; columns: list of column names to show."""
    rows = list(rows)
    if not rows:
        print("  (no records found)")
        return
    widths = {c: max(len(c), *(len(str(r[c])) for r in rows)) for c in columns}
    header = " | ".join(c.ljust(widths[c]) for c in columns)
    print(" " + header)
    print(" " + "-" * len(header))
    for r in rows:
        print(" " + " | ".join(str(r[c]).ljust(widths[c]) for c in columns))


def print_schedule(schedule):
    """schedule: list of (date_str, [available HH:MM slots]) from
    availability.get_upcoming_schedule(). Prints one line per day."""
    for date_str, slots in schedule:
        if slots:
            print(f"  {date_str}: {', '.join(slots)}")
        else:
            print(f"  {date_str}: (closed or fully booked)")


def pause():
    input("\nPress Enter to continue...")
