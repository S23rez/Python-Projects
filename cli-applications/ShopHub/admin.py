from datetime import datetime
from database import get_connection
from validators import (
    prompt_non_empty,
    prompt_positive_float,
    prompt_positive_int,
    prompt_date
)

ADMIN_USER = "s23rez"
ADMIN_PASS = "ShopH3b"

def admin_authenticate() -> bool:
    print("\n--- RESTRICTED: ADMIN ACCESS ---")
    u = input("Username: ").strip()
    p = input("Password: ").strip()
    if u == ADMIN_USER and p == ADMIN_PASS:
        print("[+] Access granted.")
        return True
    print("[-] Access denied. Invalid credentials.")
    return False

def add_product():
    print("\n--- INVENTORY: INSERT PRODUCT ---")
    name = prompt_non_empty("Product Name: ")
    category = prompt_non_empty("Category: ")
    price = prompt_positive_float("Unit Price ($): ")
    stock = prompt_positive_int("Starting Stock Quantity: ")
    status = "ACTIVE" if stock > 0 else "OUT_OF_STOCK"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO products (product_name, category, price, stock_quantity, status, date_added)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, category, price, stock, status, now))
    conn.commit()
    print(f"[+] Product inserted with ID #{cur.lastrowid} on {now}")
    conn.close()

def view_all_products():
    print("\n--- COMPLETE PRODUCT REPOSITORY (ADMIN VIEW) ---")
    conn = get_connection()
    cur = conn.cursor()
    # date_added is explicitly displayed for admin
    cur.execute("SELECT product_id, product_name, category, price, stock_quantity, status, date_added FROM products")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No products currently in the database.")
        return

    print(f"{'ID':<5} | {'Product Name':<28} | {'Category':<15} | {'Price':<8} | {'Stock':<6} | {'Status':<12} | {'Date Added'}")
    print("-" * 105)
    for r in rows:
        print(f"#{r[0]:<4} | {r[1]:<28} | {r[2]:<15} | ${r[3]:<7.2f} | {r[4]:<6} | {r[5]:<12} | {r[6]}")

def search_products():
    term = prompt_non_empty("\nEnter name or category keyword to search: ")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT product_id, product_name, category, price, stock_quantity, status, date_added 
        FROM products 
        WHERE product_name LIKE ? OR category LIKE ?
    """, (f"%{term}%", f"%{term}%"))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("[-] No records match that search query.")
        return

    print(f"\nResults for '{term}':")
    for r in rows:
        print(f"#{r[0]} - {r[1]} [{r[2]}] | ${r[3]:.2f} | In Stock: {r[4]} | Status: {r[5]} | Added: {r[6]}")

def update_product():
    p_id = prompt_positive_int("\nEnter Product ID to update: ")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT product_name, category, price FROM products WHERE product_id = ?", (p_id,))
    prod = cur.fetchone()
    if not prod:
        print(f"[-] Product #{p_id} not found.")
        conn.close()
        return

    print(f"Editing #{p_id}: {prod[0]} | Cat: {prod[1]} | Price: ${prod[2]:.2f}")
    new_name = prompt_non_empty("New Product Name: ")
    new_cat = prompt_non_empty("New Category: ")
    new_price = prompt_positive_float("New Price ($): ")

    cur.execute("UPDATE products SET product_name = ?, category = ?, price = ? WHERE product_id = ?",
                (new_name, new_cat, new_price, p_id))
    conn.commit()
    conn.close()
    print("[+] Product details updated.")

def delete_product():
    p_id = prompt_positive_int("\nEnter Product ID to remove: ")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE product_id = ?", (p_id,))
    if cur.rowcount > 0:
        conn.commit()
        print(f"[+] Product #{p_id} and its associations have been deleted.")
    else:
        print(f"[-] Product #{p_id} not found.")
    conn.close()

def adjust_stock():
    p_id = prompt_positive_int("\nEnter Product ID: ")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT product_name, stock_quantity FROM products WHERE product_id = ?", (p_id,))
    prod = cur.fetchone()

    if not prod:
        print("[-] Product not found.")
        conn.close()
        return

    print(f"Item: '{prod[0]}' | Current Stock: {prod[1]}")
    action = input("Enter 'INC' to increase or 'DEC' to decrease: ").strip().upper()
    if action not in ["INC", "DEC"]:
        print("[-] Invalid selection.")
        conn.close()
        return

    change = prompt_positive_int("Quantity units: ")
    current_qty = prod[1]

    if action == "DEC":
        if change > current_qty:
            print("[-] Stock cannot be negative.")
            conn.close()
            return
        new_qty = current_qty - change
    else:
        new_qty = current_qty + change

    new_status = "OUT_OF_STOCK" if new_qty == 0 else "ACTIVE"
    cur.execute("UPDATE products SET stock_quantity = ?, status = ? WHERE product_id = ?", (new_qty, new_status, p_id))
    conn.commit()
    conn.close()
    print(f"[+] Stock updated to {new_qty} units.")

def view_all_users():
    print("\n--- REGISTERED USERS & CREDENTIALS ---")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT customer_id, username, password, full_name, email, phone_number, registration_date 
        FROM customers
        ORDER BY customer_id ASC
    """)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No registered customers found in database.")
        return

    print(f"{'ID':<4} | {'Username':<14} | {'Password':<14} | {'Full Name':<20} | {'Email':<24} | {'Phone':<12} | {'Registered'}")
    print("-" * 110)
    for r in rows:
        print(f"#{r[0]:<3} | {r[1]:<14} | {r[2]:<14} | {r[3]:<20} | {r[4]:<24} | {r[5]:<12} | {r[6]}")

def run_reports():
    while True:
        print("\n--- ADMIN ANALYTICS & REPORTS ---")
        print("1. Total Sales & Revenue")
        print("2. Low Stock Alerts (Stock < 10)")
        print("3. Best-Selling Products")
        print("4. High-Value Customers (By Spend)")
        print("5. Orders in Date Range")
        print("6. Return to Admin Menu")

        opt = input("Select (1-6): ").strip()
        conn = get_connection()
        cur = conn.cursor()

        if opt == "1":
            cur.execute("SELECT COUNT(order_id), COALESCE(SUM(final_amount), 0.0) FROM orders WHERE order_status = 'COMPLETED'")
            res = cur.fetchone()
            print(f"\nOrders Completed: {res[0]} | Gross Revenue: ${res[1]:.2f}")

        elif opt == "2":
            cur.execute("SELECT product_id, product_name, stock_quantity FROM products WHERE stock_quantity < 10 ORDER BY stock_quantity ASC")
            rows = cur.fetchall()
            print("\n--- LOW STOCK WARNING (< 10) ---")
            for r in rows:
                print(f"#{r[0]} {r[1]} - Only {r[2]} remaining")

        elif opt == "3":
            cur.execute("""
                SELECT p.product_id, p.product_name, SUM(oi.quantity) as units_sold, SUM(oi.unit_price * oi.quantity) as gross
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                GROUP BY p.product_id, p.product_name
                ORDER BY units_sold DESC LIMIT 5
            """)
            rows = cur.fetchall()
            print("\n--- TOP 5 BEST-SELLING PRODUCTS ---")
            for r in rows:
                print(f"#{r[0]} {r[1]} | Units Sold: {r[2]} | Total Generated: ${r[3]:.2f}")

        elif opt == "4":
            cur.execute("""
                SELECT c.customer_id, c.full_name, c.email, COUNT(o.order_id), SUM(o.final_amount) as spent
                FROM customers c
                JOIN orders o ON c.customer_id = o.customer_id
                WHERE o.order_status = 'COMPLETED'
                GROUP BY c.customer_id, c.full_name, c.email
                ORDER BY spent DESC LIMIT 5
            """)
            rows = cur.fetchall()
            print("\n--- TOP 5 CUSTOMERS BY LIFETIME SPEND ---")
            for r in rows:
                print(f"#{r[0]} {r[1]} ({r[2]}) | Orders: {r[3]} | Total Spent: ${r[4]:.2f}")

        elif opt == "5":
            print("\nEnter Date Range (YYYY-MM-DD):")
            start = prompt_date("Start Date: ") + " 00:00:00"
            end = prompt_date("End Date: ") + " 23:59:59"
            cur.execute("""
                SELECT order_id, customer_id, final_amount, created_at 
                FROM orders 
                WHERE created_at BETWEEN ? AND ? ORDER BY created_at DESC
            """, (start, end))
            rows = cur.fetchall()
            print(f"\n--- ORDERS PROCESSED BETWEEN {start} AND {end} ---")
            for r in rows:
                print(f"Order #{r[0]} | Cust ID: #{r[1]} | Total: ${r[2]:.2f} | Processed: {r[3]}")

        elif opt == "6":
            conn.close()
            break
        else:
            print("[-] Invalid report option.")
        conn.close()

def admin_menu():
    while True:
        print("\n=== SHOPHUB CENTRAL ADMINISTRATOR ===")
        print("1. Insert New Product")
        print("2. View All Products (with Date Added)")
        print("3. Search Products")
        print("4. Update Product Info")
        print("5. Delete Product")
        print("6. Increase / Decrease Stock")
        print("7. View Registered Users & Passwords")
        print("8. Financial & Stock Reports")
        print("9. Logout")

        choice = input("Select an option (1-9): ").strip()
        if choice == "1":
            add_product()
        elif choice == "2":
            view_all_products()
        elif choice == "3":
            search_products()
        elif choice == "4":
            update_product()
        elif choice == "5":
            delete_product()
        elif choice == "6":
            adjust_stock()
        elif choice == "7":
            view_all_users()
        elif choice == "8":
            run_reports()
        elif choice == "9":
            print("[+] Logged out of administrator panel.")
            break
        else:
            print("[-] Invalid choice. Enter 1-9.")