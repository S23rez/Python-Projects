from datetime import datetime
from database import get_connection, init_db

# 52 items across standard Jumia storefront categories
JUMIA_PRODUCTS = [
    # Phones & Tablets
    ("Samsung Galaxy A15 (128GB)", "Phones & Tablets", 185.00, 25),
    ("Apple iPhone 15 (128GB)", "Phones & Tablets", 799.00, 14),
    ("Xiaomi Redmi Note 13 (256GB)", "Phones & Tablets", 210.00, 30),
    ("Tecno Spark 20 Pro (256GB)", "Phones & Tablets", 160.00, 40),
    ("Infinix Hot 40 Pro (128GB)", "Phones & Tablets", 145.00, 35),
    ("Samsung Galaxy Tab A9", "Phones & Tablets", 155.00, 12),
    ("Apple iPad 10th Gen (64GB)", "Phones & Tablets", 349.00, 8),
    ("Oraimo 20000mAh Power Bank", "Phones & Tablets", 22.50, 75),
    ("Anker 20W Fast USB-C Charger", "Phones & Tablets", 14.00, 90),

    # Computing & IT
    ("HP Pavilion 15 (Core i5, 16GB, 512GB)", "Computing", 580.00, 10),
    ("Dell Inspiron 3520 (Core i3, 8GB, 256GB)", "Computing", 420.00, 15),
    ("Lenovo IdeaPad Slim 3 (Ryzen 5, 512GB)", "Computing", 495.00, 18),
    ("Apple MacBook Air M2 (256GB)", "Computing", 999.00, 6),
    ("Logitech Wireless Mouse M185", "Computing", 12.00, 110),
    ("SanDisk 128GB Ultra USB 3.0 Flash Drive", "Computing", 13.50, 85),
    ("Seagate 1TB External Hard Drive", "Computing", 54.00, 22),
    ("Logitech MK270 Wireless Keyboard & Mouse Combo", "Computing", 28.00, 34),

    # Electronics & Audio
    ("Oraimo FreePods 4 TWS Earbuds", "Electronics", 29.50, 60),
    ("Apple AirPods Pro (2nd Gen)", "Electronics", 219.00, 9),
    ("JBL Flip 6 Portable Bluetooth Speaker", "Electronics", 99.00, 20),
    ("Sony WH-1000XM4 Noise-Canceling Headphones", "Electronics", 278.00, 7),
    ("Hisense 43-Inch 4K UHD Smart TV", "Electronics", 230.00, 16),
    ("LG 55-Inch 4K UHD Cinema TV", "Electronics", 450.00, 8),
    ("Sony 2.1ch Bluetooth Soundbar", "Electronics", 125.00, 11),
    ("Amazon Fire TV Stick 4K", "Electronics", 42.00, 45),

    # Home & Kitchen Appliances
    ("Silver Crest 2L Industrial Blender", "Appliances", 35.00, 40),
    ("Century 1.8L Electric Kettle", "Appliances", 15.50, 65),
    ("Binatone 16-Inch Standing Fan", "Appliances", 32.00, 28),
    ("Haier Thermocool 100L Chest Freezer", "Appliances", 260.00, 5),
    ("Panasonic Microwave Oven 20L", "Appliances", 92.00, 14),
    ("Philips Dry Iron 1000W", "Appliances", 18.00, 50),
    ("Maxi 4-Burner Gas Cooker", "Appliances", 175.00, 7),

    # Fashion & Apparel
    ("Men Slim Fit Casual Chino Trousers", "Fashion", 16.00, 45),
    ("Men Breathable Mesh Running Sneakers", "Fashion", 24.50, 30),
    ("Unisex Oversized Cotton Graphic T-Shirt", "Fashion", 9.50, 80),
    ("Women Flowy Floral Maxi Dress", "Fashion", 21.00, 25),
    ("Waterproof Laptop Backpack (15.6 Inch)", "Fashion", 19.50, 55),
    ("Men Stainless Steel Quartz Analog Watch", "Fashion", 26.00, 35),
    ("Polarized UV400 Sunglasses", "Fashion", 8.00, 70),

    # Beauty & Personal Care
    ("Nivea Perfect & Radiant Body Lotion (400ml)", "Beauty", 7.50, 95),
    ("CeraVe Hydrating Facial Cleanser (236ml)", "Beauty", 14.50, 40),
    ("The Ordinary Niacinamide 10% + Zinc 1%", "Beauty", 9.80, 50),
    ("Garnier SkinActive Micellar Water (400ml)", "Beauty", 8.20, 60),
    ("Dettol Antiseptic Disinfectant Liquid (500ml)", "Beauty", 5.50, 120),
    ("Oral-B Pro-Expert Toothbrush (Pack of 3)", "Beauty", 4.00, 100),
    ("Nova Rechargeable Hair Clipper", "Beauty", 11.00, 45),

    # Food & Groceries
    ("Golden Penny Long Grain Rice (5kg)", "Groceries", 9.50, 60),
    ("Kellogg's Corn Flakes (500g)", "Groceries", 4.50, 50),
    ("Milo Chocolate Malt Drink Refill (800g)", "Groceries", 6.80, 45),
    ("Dano Full Cream Milk Powder (800g)", "Groceries", 7.20, 40),
    ("Nescafe Classic Instant Coffee Jar (200g)", "Groceries", 6.00, 35),
    ("Devon King's Pure Vegetable Cooking Oil (5L)", "Groceries", 14.50, 30),
]

def seed_products():
    init_db()  # Ensures tables are created
    conn = get_connection()
    cur = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Clear existing cart and items to prevent orphaned foreign keys, then insert
    cur.execute("DELETE FROM cart_items;")
    cur.execute("DELETE FROM products;")

    # Reset SQLite AUTOINCREMENT counter for a clean catalog starting at ID #1
    cur.execute("DELETE FROM sqlite_sequence WHERE name='products';")

    inserted = 0
    for name, category, price, stock in JUMIA_PRODUCTS:
        status = "ACTIVE" if stock > 0 else "OUT_OF_STOCK"
        cur.execute("""
            INSERT INTO products (product_name, category, price, stock_quantity, status, date_added)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, category, price, stock, status, now))
        inserted += 1

    conn.commit()
    conn.close()

    print(f"[+] Successfully seeded {inserted} Jumia-style products into the database!")
    print(f"[+] All items are indexed starting at Product ID #1 with timestamp: {now}")

if __name__ == "__main__":
    seed_products()