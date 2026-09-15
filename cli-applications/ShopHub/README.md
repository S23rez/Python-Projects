
# ShopHub E-Commerce Management System

ShopHub is a complete, transactional e-commerce management system built with Python and a relational SQLite engine. Originally born as a small electronics shop managing 20 items by hand, the platform has grown into a multi-category storefront handling hundreds of registered shoppers and an extensive inventory catalog mimicking retail platforms like Jumia.

The system enforces relational data integrity, role-based access control (RBAC), strict regular expression input validation, ACID transaction workflows to prevent overselling, and automated administrative business intelligence reporting.

---

## System Capabilities & Core Modules

### 1. Product & Inventory Management
* **Catalog Operations:** Add, view, search, edit, and delete products across diverse categories.
* **Granular Stock Control:** Increment and decrement inventory balances on demand.
* **Automated Stock Status:** Items automatically switch to `OUT_OF_STOCK` when quantity hits 0. Zero-stock items cannot be ordered.
* **Separation of Concerns:** Operational metadata (`date_added`) is strictly visible to administrators and omitted from the customer catalog interface.
* **Pre-seeded Storefront:** Comes pre-loaded with **52 products** across Phones & Tablets, Computing, Electronics, Appliances, Fashion, Beauty, and Groceries.

### 2. Customer Management & Authentication
* **Input-Validated Registration:** Requires Full Name, RFC-compliant Email, numeric Phone Number, Shipping Address, Username, and Password.
* **Profile Management:** Customers can update their personal information, shipping address, or credentials at any time.
* **Order History & Receipts:** Shoppers can review their historical purchase log with itemized breakdowns (quantities, purchase-time prices, line totals, and timestamps).

### 3. Order Processing & Transaction Pipeline
* **Atomic Checkout:** Wrapped inside a database transaction (`BEGIN` / `COMMIT` / `ROLLBACK`) ensuring:
  1. Customer existence is verified.
  2. All products and requested quantities are validated against live stock.
  3. Product stocks decrement the instant checkout succeeds.
  4. Subtotal, discounts, and final charges are calculated accurately.
  5. Active shopping carts are purged upon successful payment.
  6. An itemized receipt is generated and displayed.
  7. Partial stock or inventory conflicts trigger an immediate rollback to avoid partial purchases or overselling.

### 4. Admin Reporting & Business Intelligence (BI)
* **Total Sales & Gross Revenue:** Cumulative order volume and net earnings.
* **Low Stock Alerts:** Real-time filter highlighting products running low (stock < 10).
* **Top 5 Best-Sellers:** Ranked by aggregate units sold and revenue contribution.
* **High-Value Customers:** Ranked by lifetime order counts and total spend.
* **Date Range Querying:** Audit sales and checkouts within specified `YYYY-MM-DD` periods.
* **User & Credential Audit Table:** View all registered customers and account credentials.

---

## Validation & Business Rules

| Field | Rule / Regular Expression | Behavior on Failure |
| :--- | :--- | :--- |
| **Email** | `^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$` | Rejects non-RFC format; prevents duplicates via DB unique index |
| **Phone Number** | `^\d{11}$` | Strictly requires exactly 11 numeric digits |
| **Password** | `8 < len(password) < 12` | Must be strictly between 9 and 11 characters long |
| **Numeric Values** | Positive Floats & Integers | Disallows negative numbers and zero for prices/quantities |
| **Timestamps** | Automated via `datetime.now()` | Generated automatically (`YYYY-MM-DD HH:MM:SS`) on DB write |

---

## Project Structure

```text
shophub/
├── database.py       # SQLite connection manager, foreign keys, and DDL schema
├── validators.py     # Regex engines and input parsing rules
├── customer.py       # Customer portal: storefront, cart, checkout, profile, history
├── admin.py          # Admin portal: product CRUD, stock adjustment, user audit, BI
├── seed_data.py      # Database seeder (52 Jumia-style retail goods)
├── main.py           # Unified entry router (Admin & Customer gateway)
├── .gitignore        # Excludes SQLite database files and runtime caches
└── README.md         # System documentation and setup guide

```

---

## Relational Schema Design

```sql
-- Customers & Credentials
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone_number TEXT NOT NULL,
    shipping_address TEXT NOT NULL,
    registration_date TEXT NOT NULL
);

-- Products & Inventory
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL CHECK (price >= 0),
    stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0),
    status TEXT NOT NULL,
    date_added TEXT NOT NULL
);

-- Shopping Carts
CREATE TABLE cart_items (
    cart_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    UNIQUE(customer_id, product_id)
);

-- Orders Ledger
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    subtotal REAL NOT NULL,
    discount_amount REAL NOT NULL DEFAULT 0.0,
    final_amount REAL NOT NULL,
    order_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Historical Purchase Line Items
CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

```

---

## Getting Started

### Prerequisites

* Python 3.9 or higher (standard library only; no external package dependencies required).

### Installation & Execution

1. **Clone the repository:**
```bash
git clone https://github.com/S23rez/ShopHub-E-Commerce.git
cd shophub-ecommerce

```


2. **Seed the database (52 items across 7 departments):**
```bash
python3 seed_data.py

```


3. **Launch the CLI storefront:**
```bash
python3 main.py

```



---

## User Flows & Navigation

### 1. Main Welcome Pane

```text
=======================================================
              WELCOME TO SHOPHUB              
   Signup as new customer / Login as Existing User    
=======================================================
1. Sign Up
2. Login
3. Exit
-------------------------------------------------------

```

### 2. Login Portal (Unified Gateway)

* **Administrator Access:**
* **Username:** `s23rez`
* **Password:** `ShopH3b`
* Automatically grants access to the **Central Administrator Dashboard**.


* **Customer Access:**
* Providing any registered customer username and password opens the **Customer Dashboard**.



### 3. Administrative Control Features

* `Insert New Product`
* `View All Products (with Date Added)`
* `Search Products`
* `Update Product Info`
* `Delete Product`
* `Increase / Decrease Stock`
* `View Registered Users & Passwords`
* `Financial & Stock Reports` (Sales, low stock alerts, best sellers, customer lifetime value, and date ranges)

### 4. Customer Storefront Features

* `Browse Store Products` (Displays names, categories, pricing, and live units; omits internal dates)
* `Add Item to Cart` (Previews catalog first, prompts for Product ID & Quantity, guards against over-ordering)
* `View Shopping Cart` (Calculates live subtotals)
* `Checkout` (Atomic stock reduction, order finalization, and receipt printing)
* `View Order History` (Itemized archive of past transactions)
* `Edit Profile` (Modify Name, Email, 11-digit Phone, Shipping Address, or 9–11 character Password)

---

## License

This project is open-source and available under the [MIT License](https://www.google.com/search?q=LICENSE).

```

```