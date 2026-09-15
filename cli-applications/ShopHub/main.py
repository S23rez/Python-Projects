import sys
from database import init_db
from admin import ADMIN_USER, ADMIN_PASS, admin_menu
from customer import register_customer, customer_menu
from database import get_connection

def unified_login():
    print("\n--- LOGIN TO SHOPHUB ---")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    # 1. Automatic Admin Login Check
    if username == ADMIN_USER and password == ADMIN_PASS:
        print("\n[+] Admin access granted. Welcome, Administrator.")
        admin_menu()
        return

    # 2. Registered Customer Login Check
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT customer_id, full_name, email, phone_number, shipping_address 
        FROM customers WHERE username = ? AND password = ?
    """, (username, password))
    cust = cur.fetchone()
    conn.close()

    if cust:
        customer_data = {
            "id": cust[0],
            "name": cust[1],
            "email": cust[2],
            "phone": cust[3],
            "address": cust[4]
        }
        print(f"\n[+] Login successful! Welcome back, {customer_data['name']}.")
        customer_menu(customer_data)
        return

    # 3. Neither Admin nor Registered Customer
    print("[-] Invalid credentials. Please check your username and password or sign up.")

def main():
    init_db()

    while True:
        print("\n" + "=" * 55)
        print("              WELCOME TO SHOPHUB              ")
        print("   Signup as new customer / Login as Existing User    ")
        print("=" * 55)
        print("1. Sign Up")
        print("2. Login")
        print("3. Exit")
        print("-" * 55)

        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            register_customer()
        elif choice == "2":
            unified_login()
        elif choice == "3":
            print("\nThank you for visiting ShopHub. Goodbye!")
            sys.exit(0)
        else:
            print("[-] Invalid selection. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()