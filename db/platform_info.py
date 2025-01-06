import mysql.connector
from mysql.connector import Error

conn = None
try:
    # Connect to the MySQL database
    conn = mysql.connector.connect(
        #host="mysql_server",
        host="127.0.0.1",
        user="user",
        password="passwd",
        database="shopping"
    )

    if conn.is_connected():
        print("Successfully connected to the database")

    cursor = conn.cursor()

    # Data for Platforms table
    PLATFORM = [
        "seven_eleven",
        "family_mart",
        "ok_mart",
        "shopee",
    ]

    platform_to_id = {
        "seven_eleven": 1,
        "family_mart": 2,
        "ok_mart": 3,
        "shopee": 4,
    }

    # Insert data into Platforms table
    for platform in PLATFORM:
        platform_name = platform.replace('_', ' ').title()  # Format name (e.g., "seven_eleven" to "Seven Eleven")
        print(platform_name)
        cursor.execute("""
        INSERT IGNORE INTO Platforms (name)
        VALUES (%s)
        """, (platform_name,))

    # Commit changes
    conn.commit()
    print("Platform data inserted successfully!")

except Error as e:
    print(f"Error occurred: {e}")

finally:
    # Ensure resources are released
    if cursor:
        cursor.close()
    if conn:
        conn.close()
