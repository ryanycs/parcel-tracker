import mysql.connector
from mysql.connector import Error
import os

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")

def create_tables(cursor):
    """Create tables if not exist"""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Parcels (
        id INT AUTO_INCREMENT PRIMARY KEY,
        order_id VARCHAR(255) NOT NULL,
        platform_id INT NOT NULL,
        status VARCHAR(255) NOT NULL,
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY (order_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Subscriptions (
        sub_id INT AUTO_INCREMENT PRIMARY KEY,
        order_id VARCHAR(255) NOT NULL,
        email VARCHAR(255),
        discord_id VARCHAR(255),
        platform_id INT NOT NULL,
        sub_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT email_or_dc CHECK (email IS NOT NULL OR discord_id IS NOT NULL),
        FOREIGN KEY (order_id) REFERENCES Parcels (order_id),
        UNIQUE (email, discord_id, order_id, platform_id) 
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Platforms (
        platform_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL
    )
    """)

def create_index_if_not_exists(cursor):
    """Create index on order_id if not exists"""
    cursor.execute("""
    SELECT COUNT(*) 
    FROM information_schema.statistics 
    WHERE table_schema = 'shopping' 
    AND table_name = 'Parcels' 
    AND index_name = 'idx_order_id';
    """)

    index_exists = cursor.fetchone()[0] > 0

    if not index_exists:
        cursor.execute("CREATE INDEX idx_order_id ON Parcels (order_id);")

def main():
    conn = None
    try:
        # Connect to the MySQL database
        conn = mysql.connector.connect(
            host=DATABASE_URL,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database=DATABASE_NAME,
        )

        if conn.is_connected():
            print("Successfully connected to the database")

        cursor = conn.cursor()

        # Create tables
        create_tables(cursor)

        # Create index if not exists
        create_index_if_not_exists(cursor)

        # Commit changes after all operations
        conn.commit()
        print("Tables and index created successfully")

    except Error as e:
        print(f"Error: {e}")
        cursor = None
    finally:
        # Close connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
