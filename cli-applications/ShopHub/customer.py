import sqlite3
from datetime import datetime
from database import get_connection
from validators import (
    prompt_non_empty,
    prompt_email,
    prompt_phone,
    prompt_password,
    prompt_positive_int
)


def register_customer():
    print("\n--- CUSTOMER REGISTRATION ---")
    # 1. Personal details first
    full_name = prompt_non_empty("Full Name: ")
    email = prompt_email("Email: ")
    phone = prompt_phone("Phone Number (11 digits): ")
    address = prompt_non_empty("Shipping Address: ")

    # 2. Credentials last
    username = prompt_non_empty("Choose a Username: ")
    password = prompt_password("Choose a Password (more than 8 and less than 12 characters): ")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
                    INSERT INTO customers (username, password, full_name, email, phone_number, shipping_address, registration_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (username, password, full_name, email, phone, address, now))
        conn.commit()
        print(f"[+] Registration successful! Your Customer ID is #{cur.lastrowid}. You may now log in.")
    except sqlite3.IntegrityError:
        print("[-] Registration error: That Username or Email is already registered.")
    finally:
        conn.close()


def login_customer():
    print("\n--- CUSTOMER LOGIN ---")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
                SELECT customer_id, full_name, email, phone_number, shipping_address, username, password
                FROM customers
                WHERE username = ?
                  AND password = ?
                """, (username, password))
    cust = cur.fetchone()
    conn.close()

    if cust:
        print(f"\n[+] Welcome back, {cust[1]}!")
        return {
            "id": cust[0],
            "name": cust[1],
            "email": cust[2],
            "phone": cust[3],
            "address": cust[4],
            "username": cust[5]
        }
    print("[-] Invalid username or password.")
    return None


def display_catalog():
    # date_added is omitted for customers
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
                SELECT product_id, product_name, category, price, stock_quantity
                FROM products
                WHERE stock_quantity > 0
                  AND status != 'OUT_OF_STOCK'
                ORDER BY category, product_name
                """)
    rows = cur.fetchall()
    conn.close()

    print("\n========================= AVAILABLE STORE PRODUCTS =========================")
    if not rows:
        print("Sorry, all products are currently sold out.")
        print("=" * 76)
        return False

    print(f"{'ID':<6} | {'Item Name':<28} | {'Category':<15} | {'Price':<10} | {'In Stock'}")
    print("-" * 76)
    for r in rows:
        print(f"#{r[0]:<5} | {r[1]:<28} | {r[2]:<15} | ${r[3]:<9.2f} | {r[4]} units")
    print("=" * 76)
    return True


def add_to_cart(customer_id: int):
    has_items = display_catalog()
    if not has_items:
        return

    p_id = prompt_positive_int("\nEnter Product ID to add: ")
    qty = prompt_positive_int("Enter Desired Quantity: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT product_name, stock_quantity FROM products WHERE product_id = ?", (p_id,))
    prod = cur.fetchone()

    if not prod:
        print("[-] Error: Product ID not found.")
        conn.close()
        return

    product_name, available_stock = prod[0], prod[1]

    if available_stock <= 0:
        print(f"[-] '{product_name}' is currently out of stock.")
        conn.close()
        return

    cur.execute("SELECT quantity FROM cart_items WHERE customer_id = ? AND product_id = ?", (customer_id, p_id))
    existing = cur.fetchone()
    current_cart_qty = existing[0] if existing else 0

    if current_cart_qty + qty > available_stock:
        print(f"[-] Cannot add {qty}. Available: {available_stock} (You already have {current_cart_qty} in cart).")
        conn.close()
        return

    if existing:
        cur.execute("UPDATE cart_items SET quantity = quantity + ? WHERE customer_id = ? AND product_id = ?", (qty, customer_id, p_id))
    else:
        cur.execute("INSERT INTO cart_items (customer_id, product_id, quantity) VALUES (?, ?, ?)", (customer_id, p_id, qty))

    conn.commit()
    conn.close()
    print(f"[+] Added {qty}x '{product_name}' to your cart.")


def view_cart(customer_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
                SELECT c.product_id, p.product_name, p.price, c.quantity, (p.price * c.quantity) as line_total
                FROM cart_items c
                         JOIN products p ON c.product_id = p.product_id
                WHERE c.customer_id = ?
                """, (customer_id,))
    items = cur.fetchall()
    conn.close()

    print("\n---------------------- YOUR SHOPPING CART ----------------------")
    if not items:
        print("Your cart is empty.")
        print("-" * 64)
        return []

    print(f"{'ID':<6} | {'Item':<25} | {'Unit Price':<11} | {'Qty':<5} | {'Subtotal'}")
    print("-" * 64)
    total = 0.0
    for row in items:
        print(f"#{row[0]:<5} | {row[1]:<25} | ${row[2]:<10.2f} | {row[3]:<5} | ${row[4]:.2f}")
        total += row[4]
    print("-" * 64)
    print(f"Total Cart Value: ${total:.2f}")
    return items


def checkout(customer: dict):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
                    SELECT c.product_id, c.quantity, p.product_name, p.price, p.stock_quantity
                    FROM cart_items c
                             JOIN products p ON c.product_id = p.product_id
                    WHERE c.customer_id = ?
                    """, (customer["id"],))
        cart_items = cur.fetchall()

        if not cart_items:
            print("[-] Cannot checkout: Your cart is empty.")
            conn.close()
            return

        subtotal = 0.0
        line_items = []
        for it in cart_items:
            p_id, req_qty, name, price, stock = it[0], it[1], it[2], it[3], it[4]
            if stock < req_qty:
                raise ValueError(f"Checkout conflict: '{name}' has only {stock} items left, but you requested {req_qty}.")

            line_cost = price * req_qty
            subtotal += line_cost
            line_items.append((p_id, name, price, req_qty, line_cost))

        discount = 0.0
        final_amount = subtotal - discount
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute("""
                    INSERT INTO orders (customer_id, subtotal, discount_amount, final_amount, order_status, created_at)
                    VALUES (?, ?, ?, ?, 'COMPLETED', ?)
                    """, (customer["id"], subtotal, discount, final_amount, now))
        order_id = cur.lastrowid

        for p_id, _, price, req_qty, _ in line_items:
            cur.execute("""
                        INSERT INTO order_items (order_id, product_id, unit_price, quantity)
                        VALUES (?, ?, ?, ?)
                        """, (order_id, p_id, price, req_qty))

            cur.execute("""
                        UPDATE products
                        SET stock_quantity = stock_quantity - ?,
                            status         = CASE WHEN stock_quantity - ? = 0 THEN 'OUT_OF_STOCK' ELSE status END
                        WHERE product_id = ?
                        """, (req_qty, req_qty, p_id))

        cur.execute("DELETE FROM cart_items WHERE customer_id = ?", (customer["id"],))
        conn.commit()

        print("\n" + "=" * 50)
        print("             SHOPHUB PAYMENT RECEIPT              ")
        print("=" * 50)
        print(f"Receipt ID:   #{order_id}")
        print(f"Timestamp:    {now}")
        print(f"Customer:     {customer['name']}")
        print(f"Email:        {customer['email']}")
        print(f"Deliver To:   {customer['address']}")
        print("-" * 50)
        for _, name, price, qty, cost in line_items:
            print(f"{name:<24} {qty:>2}x @ ${price:>6.2f} = ${cost:>8.2f}")
        print("-" * 50)
        print(f"Subtotal:       ${subtotal:.2f}")
        print(f"Discounts:      ${discount:.2f}")
        print(f"FINAL CHARGE:   ${final_amount:.2f}")
        print("=" * 50)
        print("Your order has been placed successfully!\n")

    except ValueError as err:
        conn.rollback()
        print(f"\n[-] Order cancelled: {err}")
    except Exception as exc:
        conn.rollback()
        print(f"\n[-] Internal processing error: {exc}")
    finally:
        conn.close()


# ==============================================================================
# PROFILE MANAGEMENT & TRANSACTION HISTORY
# ==============================================================================

def view_order_history(customer_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
                SELECT order_id, subtotal, discount_amount, final_amount, order_status, created_at
                FROM orders
                WHERE customer_id = ?
                ORDER BY created_at DESC
                """, (customer_id,))
    orders = cur.fetchall()

    if not orders:
        print("\n[-] You have not placed any orders yet.")
        conn.close()
        return

    print("\n========================= YOUR TRANSACTION HISTORY =========================")
    for ord in orders:
        order_id, subtotal, discount, final_amount, status, created_at = ord
        print(f"\nOrder #{order_id} | Placed: {created_at} | Status: {status}")
        print(f"Subtotal: ${subtotal:.2f} | Discount: ${discount:.2f} | Total Paid: ${final_amount:.2f}")
        print("Items Purchased:")

        cur.execute("""
                    SELECT p.product_name, oi.unit_price, oi.quantity, (oi.unit_price * oi.quantity) as line_cost
                    FROM order_items oi
                             JOIN products p ON oi.product_id = p.product_id
                    WHERE oi.order_id = ?
                    """, (order_id,))
        items = cur.fetchall()

        for item_name, unit_price, qty, line_cost in items:
            print(f"   • {item_name:<30} x{qty:<2} @ ${unit_price:.2f} = ${line_cost:.2f}")
        print("-" * 65)

    conn.close()


def edit_profile(customer: dict):
    conn = get_connection()
    cur = conn.cursor()

    while True:
        # Fetch fresh data from DB
        cur.execute("""
                    SELECT full_name, email, phone_number, shipping_address
                    FROM customers
                    WHERE customer_id = ?
                    """, (customer["id"],))
        record = cur.fetchone()
        if not record:
            print("[-] Error loading profile data.")
            break

        print("\n================== YOUR ACCOUNT PROFILE ==================")
        print(f"1. Full Name:        {record[0]}")
        print(f"2. Email:            {record[1]}")
        print(f"3. Phone Number:     {record[2]}")
        print(f"4. Shipping Address: {record[3]}")
        print(f"5. Change Password")
        print("6. Back to Dashboard")
        print("=" * 58)

        choice = input("Select a field to update (1-6): ").strip()

        if choice == "1":
            new_name = prompt_non_empty("Enter new Full Name: ")
            cur.execute("UPDATE customers SET full_name = ? WHERE customer_id = ?", (new_name, customer["id"]))
            conn.commit()
            customer["name"] = new_name
            print("[+] Full Name updated successfully.")

        elif choice == "2":
            new_email = prompt_email("Enter new Email: ")
            try:
                cur.execute("UPDATE customers SET email = ? WHERE customer_id = ?", (new_email, customer["id"]))
                conn.commit()
                customer["email"] = new_email
                print("[+] Email updated successfully.")
            except sqlite3.IntegrityError:
                print("[-] Error: That email is already registered by another account.")

        elif choice == "3":
            new_phone = prompt_phone("Enter new Phone Number (Must be exactly 11 digits): ")
            cur.execute("UPDATE customers SET phone_number = ? WHERE customer_id = ?", (new_phone, customer["id"]))
            conn.commit()
            customer["phone"] = new_phone
            print("[+] Phone number updated successfully.")

        elif choice == "4":
            new_address = prompt_non_empty("Enter new Shipping Address: ")
            cur.execute("UPDATE customers SET shipping_address = ? WHERE customer_id = ?", (new_address, customer["id"]))
            conn.commit()
            customer["address"] = new_address
            print("[+] Shipping Address updated successfully.")

        elif choice == "5":
            new_password = prompt_password("Enter new Password (9 to 11 characters): ")
            cur.execute("UPDATE customers SET password = ? WHERE customer_id = ?", (new_password, customer["id"]))
            conn.commit()
            print("[+] Password updated successfully.")

        elif choice == "6":
            break
        else:
            print("[-] Invalid option. Please enter 1-6.")

    conn.close()


def customer_menu(customer: dict):
    while True:
        print(f"\n=== STORE DASHBOARD ({customer['name']}) ===")
        print("1. Browse Store Products")
        print("2. Add Item to Cart")
        print("3. View Shopping Cart")
        print("4. Checkout")
        print("5. View Order History")
        print("6. Edit Profile")
        print("7. Logout")

        choice = input("Select an option (1-7): ").strip()
        if choice == "1":
            display_catalog()
        elif choice == "2":
            add_to_cart(customer["id"])
        elif choice == "3":
            view_cart(customer["id"])
        elif choice == "4":
            checkout(customer)
        elif choice == "5":
            view_order_history(customer["id"])
        elif choice == "6":
            edit_profile(customer)
        elif choice == "7":
            print("[+] Logged out of customer account.")
            break
        else:
            print("[-] Invalid choice. Enter 1-7.")