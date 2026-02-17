import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector
import matplotlib.pyplot as plt
from datetime import datetime

# ================= DATABASE CONFIGURATION =================
# WARNING: Change 'password' to match your local MySQL settings
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "ulushahad10",  # <--- CHECK THIS
    "database": "shoe_store"
}

# ================= DATABASE SETUP =================
def setup_db():
    """Creates the database and tables automatically if they don't exist."""
    try:
        # 1. Connect to Server to create DB
        conn = mysql.connector.connect(host=db_config["host"], user=db_config["user"], password=db_config["password"])
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
        conn.close()

        # 2. Connect to the specific Database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Table: Brands
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brands (
                brand_id INT AUTO_INCREMENT PRIMARY KEY,
                brand_name VARCHAR(255) UNIQUE NOT NULL
            )
        """)

        # Table: Shoes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shoes (
                shoe_id INT AUTO_INCREMENT PRIMARY KEY,
                brand_id INT,
                size INT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                stock INT NOT NULL,
                FOREIGN KEY (brand_id) REFERENCES brands(brand_id) ON DELETE CASCADE
            )
        """)

        # Table: Sales
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INT AUTO_INCREMENT PRIMARY KEY,
                shoe_id INT,
                quantity INT,
                total_price DECIMAL(10,2),
                sale_date DATETIME,
                customer_name VARCHAR(255) DEFAULT NULL,
                customer_phone VARCHAR(20) DEFAULT NULL,
                FOREIGN KEY (shoe_id) REFERENCES shoes(shoe_id) ON DELETE SET NULL
            )
        """)

        # --- MIGRATION CHECK ---
        # Checks if existing tables need the new customer columns
        try:
            cursor.execute("SELECT customer_name FROM sales LIMIT 1")
            cursor.fetchall() # Consume result
        except mysql.connector.Error:
            print("Updating database schema with customer columns...")
            try:
                cursor.execute("ALTER TABLE sales ADD COLUMN customer_name VARCHAR(255) DEFAULT NULL")
                cursor.execute("ALTER TABLE sales ADD COLUMN customer_phone VARCHAR(20) DEFAULT NULL")
                conn.commit()
            except Exception as e:
                print(f"Schema update skipped or failed: {e}")

        conn.commit()
        return conn, cursor
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error connecting to MySQL:\n{err}\n\nPlease check your password in the code.")
        exit()

# Initialize Database Connection
conn, cursor = setup_db()

# ================= GUI ROOT =================
root = tk.Tk()
root.title("DRROPOFF Management System")

# --- FULL SCREEN SETTINGS ---
try:
    root.state("zoomed") 
except:
    root.attributes("-fullscreen", True)

# ================= LAYOUT =================
sidebar = tk.Frame(root, bg="#2c3e50", width=250)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

main = tk.Frame(root, bg="#ecf0f1")
main.pack(side="right", expand=True, fill="both")

header = tk.Label(main, text="DRROPOFF DASHBOARD", 
                  font=("Arial", 24, "bold"), bg="#ecf0f1", fg="#2c3e50")
header.pack(pady=20)

content = tk.Frame(main, bg="#ecf0f1")
content.pack(fill="both", expand=True, padx=20, pady=10)

# ================= HELPER FUNCTIONS =================
def clear_screen():
    for widget in content.winfo_children():
        widget.destroy()

def entry_field(parent, label_text):
    tk.Label(parent, text=label_text, bg="#ecf0f1", font=("Arial", 10)).pack(pady=(5, 0), anchor="w")
    e = tk.Entry(parent, width=30)
    e.pack(pady=5, anchor="w")
    return e

def get_brands():
    cursor.execute("SELECT brand_id, brand_name FROM brands")
    return cursor.fetchall()

def get_shoes_by_brand(brand_id):
    cursor.execute("SELECT shoe_id, size, price, stock FROM shoes WHERE brand_id = %s", (brand_id,))
    return cursor.fetchall()

def show_invoice_window(inv_id, brand, size, price, qty, total, date, c_name="N/A", c_phone="N/A"):
    """Displays a generated invoice in a popup window."""
    inv = tk.Toplevel(root)
    inv.title(f"Invoice #{inv_id}")
    inv.geometry("500x600")
    
    text = tk.Text(inv, font=("Courier New", 12))
    text.pack(fill="both", expand=True)
    
    receipt = f"""
************************************************
              DRROPOFF STORE        
************************************************
 Date       : {date}
 Invoice No : #{inv_id}
------------------------------------------------
 CUSTOMER DETAILS
------------------------------------------------
 Name       : {c_name}
 Phone      : {c_phone}
------------------------------------------------
 ITEM DETAILS
------------------------------------------------
 Brand      : {brand}
 Size       : {size}
 Price      : ₹{price}
 Quantity   : {qty}
------------------------------------------------
 TOTAL      : ₹{total}
------------------------------------------------
          Thank you for shopping
            at DRROPOFF!
************************************************
    """
    text.insert(tk.END, receipt)
    text.config(state="disabled")

# ================= 1. DASHBOARD =================
def dashboard():
    clear_screen()
    
    cursor.execute("SELECT COUNT(*) FROM brands")
    total_brands = cursor.fetchone()[0]
    
    cursor.execute("SELECT IFNULL(SUM(stock), 0) FROM shoes")
    total_shoes = cursor.fetchone()[0]
    
    cursor.execute("SELECT IFNULL(SUM(total_price), 0) FROM sales")
    total_revenue = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM shoes WHERE stock < 5")
    low_stock = cursor.fetchone()[0]

    cards_frame = tk.Frame(content, bg="#ecf0f1")
    cards_frame.pack(pady=20)

    def create_card(title, value, color, col):
        f = tk.Frame(cards_frame, bg=color, width=250, height=150)
        f.grid(row=0, column=col, padx=20)
        f.pack_propagate(False)
        tk.Label(f, text=title, bg=color, fg="white", font=("Arial", 14, "bold")).pack(pady=(30, 5))
        tk.Label(f, text=value, bg=color, fg="white", font=("Arial", 24, "bold")).pack()

    create_card("Total Brands", total_brands, "#2980b9", 0)
    create_card("Total Stock", total_shoes, "#27ae60", 1)
    create_card("Total Revenue", f"₹{total_revenue:,.0f}", "#8e44ad", 2)
    create_card("Low Stock Items", low_stock, "#c0392b", 3)

    def show_chart():
        cursor.execute("""
            SELECT brands.brand_name, IFNULL(SUM(shoes.stock), 0)
            FROM brands 
            LEFT JOIN shoes ON brands.brand_id = shoes.brand_id 
            GROUP BY brands.brand_name
        """)
        data = cursor.fetchall()
        if not data:
            messagebox.showinfo("Info", "No data available for chart.")
            return

        brands = [d[0] for d in data]
        stock = [d[1] for d in data]

        plt.figure(figsize=(10, 5))
        plt.bar(brands, stock, color="#3498db")
        plt.title("Current Stock by Brand")
        plt.xlabel("Brand")
        plt.ylabel("Stock Quantity")
        plt.tight_layout()
        plt.show()

    tk.Button(content, text="📊 View Stock Chart", command=show_chart, 
              bg="#34495e", fg="white", font=("Arial", 12), height=2, width=20).pack(pady=50)

# ================= 2. LOW STOCK ALERT =================
def low_stock_ui():
    clear_screen()
    tk.Label(content, text="⚠️ Low Stock Alerts (< 5 pairs)", font=("Arial", 16, "bold"), fg="#c0392b", bg="#ecf0f1").pack(pady=10)

    tree_frame = tk.Frame(content)
    tree_frame.pack(fill="both", expand=True, pady=10)

    columns = ("brand", "size", "price", "stock")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
    
    tree.heading("brand", text="Brand Name")
    tree.heading("size", text="Size")
    tree.heading("price", text="Price (₹)")
    tree.heading("stock", text="Stock Left")
    
    tree.column("brand", width=200)
    tree.column("size", width=100, anchor="center")
    tree.column("price", width=150, anchor="center")
    tree.column("stock", width=100, anchor="center")
    
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    cursor.execute("""
        SELECT brands.brand_name, shoes.size, shoes.price, shoes.stock
        FROM shoes JOIN brands ON shoes.brand_id = brands.brand_id
        WHERE shoes.stock < 5
        ORDER BY shoes.stock ASC
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        tk.Label(tree_frame, text="✅ All stocks are healthy!", bg="white", font=("Arial", 14), fg="green").place(relx=0.5, rely=0.5, anchor="center")
    else:
        for row in rows:
            tree.insert("", tk.END, values=row)

# ================= 3. VIEW INVENTORY =================
def view_inventory_ui():
    clear_screen()
    tk.Label(content, text="📦 Current Inventory", font=("Arial", 16, "bold"), bg="#ecf0f1").pack(pady=10)

    filter_frame = tk.Frame(content, bg="#ecf0f1")
    filter_frame.pack(pady=10)

    tk.Label(filter_frame, text="Filter by Brand:", bg="#ecf0f1").pack(side="left")
    brand_var = tk.StringVar()
    brand_cb = ttk.Combobox(filter_frame, textvariable=brand_var, values=["All"] + [b[1] for b in get_brands()], state="readonly")
    if brand_cb['values']:
        brand_cb.current(0)
    brand_cb.pack(side="left", padx=10)

    tree_frame = tk.Frame(content)
    tree_frame.pack(fill="both", expand=True, pady=10)

    columns = ("brand", "size", "price", "stock")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
    
    tree.heading("brand", text="Brand Name")
    tree.heading("size", text="Size")
    tree.heading("price", text="Price (₹)")
    tree.heading("stock", text="Stock Qty")
    
    tree.column("brand", width=200)
    tree.column("size", width=100, anchor="center")
    tree.column("price", width=150, anchor="center")
    tree.column("stock", width=100, anchor="center")
    
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    def load_data(event=None):
        for item in tree.get_children():
            tree.delete(item)
        selected_brand = brand_var.get()
        query = """
            SELECT brands.brand_name, shoes.size, shoes.price, shoes.stock
            FROM shoes JOIN brands ON shoes.brand_id = brands.brand_id
        """
        params = ()
        if selected_brand != "All" and selected_brand != "":
            query += " WHERE brands.brand_name = %s"
            params = (selected_brand,)
        query += " ORDER BY brands.brand_name ASC, shoes.size ASC"
        cursor.execute(query, params)
        for row in cursor.fetchall():
            tree.insert("", tk.END, values=row)

    brand_cb.bind("<<ComboboxSelected>>", load_data)
    load_data()

# ================= 4. ADD INVENTORY =================
def add_inventory_ui():
    clear_screen()
    
    frame_brand = tk.LabelFrame(content, text="Add New Brand", bg="#ecf0f1", font=("Arial", 12, "bold"), padx=20, pady=20)
    frame_brand.pack(fill="x", pady=10)
    
    b_name = entry_field(frame_brand, "Brand Name")
    
    def add_brand():
        if not b_name.get(): return
        try:
            cursor.execute("INSERT INTO brands (brand_name) VALUES (%s)", (b_name.get(),))
            conn.commit()
            messagebox.showinfo("Success", f"Brand '{b_name.get()}' added!")
            b_name.delete(0, tk.END)
            refresh_brand_combo() # Refresh the combo box below
        except mysql.connector.Error:
            messagebox.showerror("Error", "Brand likely already exists.")

    tk.Button(frame_brand, text="Add Brand", command=add_brand, bg="#27ae60", fg="white").pack(pady=10, anchor="w")

    frame_shoe = tk.LabelFrame(content, text="Add New Shoe Style", bg="#ecf0f1", font=("Arial", 12, "bold"), padx=20, pady=20)
    frame_shoe.pack(fill="x", pady=10)

    tk.Label(frame_shoe, text="Select Brand", bg="#ecf0f1").pack(anchor="w")
    brand_var = tk.StringVar()
    brand_cb = ttk.Combobox(frame_shoe, textvariable=brand_var, state="readonly", width=27)
    brand_cb.pack(anchor="w", pady=5)

    def refresh_brand_combo():
        brands = get_brands()
        brand_cb['values'] = [b[1] for b in brands]

    refresh_brand_combo()

    s_size = entry_field(frame_shoe, "Size")
    s_price = entry_field(frame_shoe, "Price (₹)")
    s_stock = entry_field(frame_shoe, "Initial Stock Qty")

    def add_shoe():
        if not brand_var.get() or not s_size.get() or not s_price.get():
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        cursor.execute("SELECT brand_id FROM brands WHERE brand_name=%s", (brand_var.get(),))
        result = cursor.fetchone()
        
        if result:
            bid = result[0]
            try:
                cursor.execute("INSERT INTO shoes (brand_id, size, price, stock) VALUES (%s, %s, %s, %s)",
                               (bid, s_size.get(), s_price.get(), s_stock.get()))
                conn.commit()
                messagebox.showinfo("Success", "Shoe Added Successfully")
                s_size.delete(0, tk.END)
                s_price.delete(0, tk.END)
                s_stock.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showerror("Error", "Brand not found in DB")

    tk.Button(frame_shoe, text="Add Shoe", command=add_shoe, bg="#2980b9", fg="white").pack(pady=10, anchor="w")

# ================= 5. SELL SHOE (POS) =================
def sell_shoe_ui():
    clear_screen()
    tk.Label(content, text="🛒 Point of Sale", font=("Arial", 16, "bold"), bg="#ecf0f1").pack(pady=10)

    # --- INPUT FORM CONTAINER ---
    form_frame = tk.Frame(content, bg="#ecf0f1")
    form_frame.pack(pady=10)

    # 1. Select Brand
    tk.Label(form_frame, text="Select Brand:", bg="#ecf0f1").grid(row=0, column=0, sticky="w", padx=10, pady=5)
    brand_var = tk.StringVar()
    brand_cb = ttk.Combobox(form_frame, textvariable=brand_var, state="readonly", width=40)
    brand_cb['values'] = [b[1] for b in get_brands()]
    brand_cb.grid(row=0, column=1, pady=5)

    # 2. Select Shoe
    tk.Label(form_frame, text="Select Shoe:", bg="#ecf0f1").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    shoe_var = tk.StringVar()
    shoe_cb = ttk.Combobox(form_frame, textvariable=shoe_var, state="readonly", width=40)
    shoe_cb.grid(row=1, column=1, pady=5)

    # Dictionary to hold shoe data mapped to the display string
    shoe_map = {} 

    def on_brand_select(e):
        b_name = brand_var.get()
        cursor.execute("SELECT brand_id FROM brands WHERE brand_name=%s", (b_name,))
        res = cursor.fetchone()
        if not res: return
        bid = res[0]
        shoes = get_shoes_by_brand(bid)
        
        shoe_map.clear()
        display_list = []
        for s in shoes:
            # s = (shoe_id, size, price, stock)
            display_str = f"Size: {s[1]} | Price: ₹{s[2]} | Stock: {s[3]}"
            display_list.append(display_str)
            shoe_map[display_str] = s 
        
        shoe_cb['values'] = display_list
        shoe_cb.set("")

    brand_cb.bind("<<ComboboxSelected>>", on_brand_select)

    # 3. Customer Info (Optional)
    tk.Label(form_frame, text="Customer Name (Optional):", bg="#ecf0f1").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    cust_name_entry = tk.Entry(form_frame, width=43)
    cust_name_entry.grid(row=2, column=1, pady=5)

    tk.Label(form_frame, text="Phone Number (Optional):", bg="#ecf0f1").grid(row=3, column=0, sticky="w", padx=10, pady=5)
    cust_phone_entry = tk.Entry(form_frame, width=43)
    cust_phone_entry.grid(row=3, column=1, pady=5)

    # 4. Quantity
    tk.Label(form_frame, text="Quantity:", bg="#ecf0f1").grid(row=4, column=0, sticky="w", padx=10, pady=5)
    qty_entry = tk.Entry(form_frame, width=43)
    qty_entry.grid(row=4, column=1, pady=5)

    def process_sale():
        if not shoe_var.get() or not qty_entry.get():
            messagebox.showerror("Error", "Please select a shoe and quantity")
            return
        
        shoe_data = shoe_map.get(shoe_var.get())
        if not shoe_data: return

        sid, size, price, stock = shoe_data
        
        try:
            qty = int(qty_entry.get())
        except:
            messagebox.showerror("Error", "Quantity must be a number")
            return

        if qty > stock:
            messagebox.showerror("Error", f"Not enough stock! Only {stock} left.")
            return

        total = price * qty
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get optional customer data
        c_name = cust_name_entry.get().strip() or "N/A"
        c_phone = cust_phone_entry.get().strip() or "N/A"

        if messagebox.askyesno("Confirm Sale", f"Total: ₹{total}\nProceed?"):
            try:
                # Update Stock
                cursor.execute("UPDATE shoes SET stock = stock - %s WHERE shoe_id = %s", (qty, sid))
                
                # Insert Sale with Customer Info
                cursor.execute("""
                    INSERT INTO sales 
                    (shoe_id, quantity, total_price, sale_date, customer_name, customer_phone) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (sid, qty, total, date_str, c_name, c_phone))
                
                # Get the last inserted ID (Invoice ID)
                invoice_id = cursor.lastrowid
                conn.commit()
                
                show_invoice_window(invoice_id, brand_var.get(), size, price, qty, total, date_str, c_name, c_phone)
                
                # Reset Fields
                qty_entry.delete(0, tk.END)
                cust_name_entry.delete(0, tk.END)
                cust_phone_entry.delete(0, tk.END)
                on_brand_select(None) # Refresh stock display
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Error", str(e))

    tk.Button(content, text="✅ COMPLETE SALE", command=process_sale, 
              bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), width=30).pack(pady=20)

# ================= 6. INVOICE HISTORY =================
def invoice_history_ui():
    clear_screen()
    tk.Label(content, text="🧾 Invoice History", font=("Arial", 16, "bold"), bg="#ecf0f1").pack(pady=10)

    tk.Label(content, text="Select a row to view/print the invoice", bg="#ecf0f1", fg="gray").pack()

    tree_frame = tk.Frame(content)
    tree_frame.pack(fill="both", expand=True, pady=10)

    columns = ("inv_id", "date", "brand", "size", "qty", "total", "customer")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
    
    tree.heading("inv_id", text="Inv #")
    tree.heading("date", text="Date")
    tree.heading("brand", text="Brand")
    tree.heading("size", text="Size")
    tree.heading("qty", text="Qty")
    tree.heading("total", text="Total (₹)")
    tree.heading("customer", text="Customer")
    
    tree.column("inv_id", width=50, anchor="center")
    tree.column("date", width=150, anchor="center")
    tree.column("brand", width=150, anchor="center")
    tree.column("size", width=80, anchor="center")
    tree.column("qty", width=80, anchor="center")
    tree.column("total", width=100, anchor="center")
    tree.column("customer", width=150, anchor="center")
    
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    # Fetch Data
    cursor.execute("""
        SELECT sales.sale_id, sales.sale_date, brands.brand_name, shoes.size, 
               sales.quantity, sales.total_price, shoes.price, 
               IFNULL(sales.customer_name, 'N/A'), IFNULL(sales.customer_phone, 'N/A')
        FROM sales
        JOIN shoes ON sales.shoe_id = shoes.shoe_id
        JOIN brands ON shoes.brand_id = brands.brand_id
        ORDER BY sales.sale_date DESC
    """)
    
    full_data_map = {} 

    for row in cursor.fetchall():
        # row: (id, date, brand, size, qty, total, unit_price, c_name, c_phone)
        inv_id, date, brand, size, qty, total, unit_price, c_name, c_phone = row
        tree.insert("", tk.END, values=(inv_id, date, brand, size, qty, total, c_name))
        
        # Store full data map for invoice generation
        full_data_map[inv_id] = {
            "brand": brand, "size": size, "qty": qty, 
            "total": total, "date": date, "price": unit_price,
            "c_name": c_name, "c_phone": c_phone
        }

    def on_view_invoice():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an invoice row first.")
            return
        
        item = tree.item(selected[0])
        # FIX: The ID from the treeview is a string, but keys in the map are integers from SQL
        inv_id = int(item['values'][0]) 
        
        data = full_data_map.get(inv_id)
        if data:
            show_invoice_window(
                inv_id, data['brand'], data['size'], 
                data['price'], data['qty'], data['total'], data['date'],
                data['c_name'], data['c_phone']
            )
        else:
             messagebox.showerror("Error", f"Could not find data for Invoice #{inv_id}")

    tk.Button(content, text="📄 View/Print Selected Invoice", command=on_view_invoice, 
              bg="#34495e", fg="white", font=("Arial", 12)).pack(pady=10)

# ================= 7. DELETE ITEMS =================
def delete_ui():
    clear_screen()
    tk.Label(content, text="🗑 Manage Deletions", font=("Arial", 16, "bold"), bg="#ecf0f1").pack(pady=10)

    frame_d_brand = tk.LabelFrame(content, text="Delete Entire Brand", bg="#ecf0f1", padx=10, pady=10)
    frame_d_brand.pack(fill="x", pady=10)
    
    tk.Label(frame_d_brand, text="Select Brand to Delete (Deletes all shoes of this brand!)", bg="#ecf0f1", fg="red").pack(anchor="w")
    
    d_brand_var = tk.StringVar()
    d_brand_cb = ttk.Combobox(frame_d_brand, textvariable=d_brand_var, values=[b[1] for b in get_brands()], state="readonly")
    d_brand_cb.pack(side="left", padx=5)

    def delete_brand_action():
        brand = d_brand_var.get()
        if not brand: 
            messagebox.showwarning("Warning", "Please select a brand first.")
            return
        
        if messagebox.askyesno("CRITICAL WARNING", f"Delete '{brand}' and ALL its inventory?"):
            try:
                cursor.execute("SELECT brand_id FROM brands WHERE brand_name=%s", (brand,))
                result = cursor.fetchone()
                if not result: return
                bid = result[0]

                cursor.execute("DELETE FROM shoes WHERE brand_id=%s", (bid,))
                cursor.execute("DELETE FROM brands WHERE brand_id=%s", (bid,))
                conn.commit()
                messagebox.showinfo("Deleted", f"Brand '{brand}' deleted.")
                d_brand_var.set("")
                d_brand_cb['values'] = [b[1] for b in get_brands()] 
                
            except mysql.connector.Error as e:
                conn.rollback()
                messagebox.showerror("Database Error", f"Could not delete: {e}")

    tk.Button(frame_d_brand, text="DELETE BRAND", command=delete_brand_action, bg="#c0392b", fg="white").pack(side="left", padx=10)

# ================= SIDEBAR MENU =================
def menu_btn(text, cmd):
    tk.Button(sidebar, text=text, command=cmd, width=30, height=2, 
              bg="#34495e", fg="white", relief="flat", font=("Arial", 11)).pack(pady=5)

tk.Label(sidebar, text="MENU", bg="#2c3e50", fg="#bdc3c7", font=("Arial", 14)).pack(pady=20)

menu_btn("📊 Dashboard", dashboard)
menu_btn("📦 View Inventory", view_inventory_ui)
menu_btn("⚠️ Low Stock Alerts", low_stock_ui)
menu_btn("➕ Add Brand / Shoe", add_inventory_ui)
menu_btn("🛒 Sell (POS)", sell_shoe_ui)
menu_btn("🧾 Invoice History", invoice_history_ui)
menu_btn("🗑 Delete Brand", delete_ui)
menu_btn("❌ Exit", root.quit)

# ================= START APP =================
dashboard()
root.mainloop()