import mysql.connector
conn = mysql.connector.connect(
    host ="localhost",
    user ="root",
    password ="ulushahad10",
    database = "shoe_store"
)
print("connected successfully")

cursor = conn.cursor()

def add_brand():
    brand_name = input("Enter brand name: ")
    query = "INSERT INTO brands (brand_name) VALUES (%s)"
    cursor.execute(query, (brand_name,))
    conn.commit()

    print("Brand added successfully")

def view_brands():
        print("\nAVAILABLE BRANDS")
        cursor.execute("SELECT * FROM brands")
        brands = cursor.fetchall()
        for brand in brands:
         print("ID:", brand[0], "| Brand:", brand[1])

        
def add_shoe():
        print("\nADD NEW SHOE")
        view_brands()
        brand_id = int(input("Enter brand ID: "))
        shoe_size = int(input("Enter shoe size: "))
        shoe_price = float(input("Enter shoe price: "))
        shoe_stock = int(input("Enter stock quantity: "))
        query = "INSERT INTO shoes (brand_id, size, price, stock) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (brand_id, shoe_size, shoe_price, shoe_stock))
        conn.commit()
        print("Shoe added successfully")

def view_shoes():
     print("\nAVAILABLE SHOES")
     size = int(input("Enter shoe size: "))
     query= ("""SELECT shoes.shoe_id, brands.brand_name, shoes.size, shoes.price, shoes.stock 
             FROM shoes 
             JOIN brands ON shoes.brand_id = brands.brand_id
             WHERE shoes.size = %s""")
    
     cursor.execute(query, (size,))
     shoes = cursor.fetchall()
    
     if shoes:
      for shoe in shoes:
         print("ID:", shoe[0], "| Brand:", shoe[1], "| Size:", shoe[2], "| Price:", shoe[3], "| Stock:", shoe[4])
       
     else:
      print("No shoes available for this size.")


def low_stock_alert():
    print("\nSHOES LOW IN STOCK")

    query = """
    SELECT shoes.shoe_id, brands.brand_name, shoes.size, shoes.stock
    FROM shoes
    JOIN brands ON shoes.brand_id = brands.brand_id
    WHERE shoes.stock < 5
    """

    cursor.execute(query)
    shoes = cursor.fetchall()

    if shoes:
        for shoe in shoes:
            print(shoe)
    else:
        print("No low stock items ")


while True:
    print("\n=== SHOE STORE MENU ===")
    print("1. Add Brand")
    print("2. View Brands")
    print("3. Add Shoe")
    print("4. View Shoes by Size")
    print("5. Low Stock Alert")
    print("6. Exit")

    choice = input("Enter your choice (1-6): ")

    if choice == "1":
        add_brand()
    elif choice == "2":
        view_brands()
    elif choice == "3":
        add_shoe()
    elif choice == "4":
        view_shoes()
    elif choice == "5":
        low_stock_alert()
    elif choice == "6":
        print("Exiting the program.")
        break
    else:
        print("Invalid choice. Please try again.")


    
     
        
