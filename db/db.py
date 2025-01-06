import mysql.connector
from mysql.connector import Error
import os

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")

def create_database(cursor):
    """Check if the database exists"""
    cursor.execute("SHOW DATABASES LIKE 'shopping'")
    if not cursor.fetchone():
        print("Database does not exist.")
        cursor.execute("CREATE DATABASE `shopping`")
        print("Database 'shopping' created successfully!")

def create_user_and_grant_privileges(cursor):
    """Create user and grant privileges."""
    cursor.execute("CREATE USER IF NOT EXISTS 'user'@'localhost' IDENTIFIED BY 'passwd'")
    cursor.execute("GRANT ALL PRIVILEGES ON `shopping`.* TO 'user'@'localhost'")
    cursor.execute("FLUSH PRIVILEGES")
    print("Granted 'user'@'localhost' access to database 'shopping'")

def connect_to_mysql():
    """Establish a connection to the MySQL server."""
    return mysql.connector.connect(
        host=DATABASE_URL,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        database=DATABASE_NAME,
    )

def main():
    conn = None
    try:
        # Connect to MySQL server
        conn = connect_to_mysql()
        if conn.is_connected():
            print("Successfully connected to MySQL server")

        with conn.cursor() as cursor:  # Using cursor as a context manager
            # Check and create the database if necessary
            create_database(cursor)

            # Create user and grant permissions
            create_user_and_grant_privileges(cursor)

        # Commit changes
        conn.commit()

    except Error as e:
        print(f"Error occurred: {e}")

    finally:
        # Ensure connection is closed
        if conn:
            conn.close()
            print("Connection closed")

if __name__ == "__main__":
    main()
