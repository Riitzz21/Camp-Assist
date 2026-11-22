from app import app, get_db_connection
from werkzeug.security import generate_password_hash
import getpass

print("Create Admin Account")

name = input("Enter admin name: ").strip()
email = input("Enter admin email: ").strip().lower()
password = getpass.getpass("Enter admin password: ")

if not name or not email or not password:
    print("All fields are required.")
    raise SystemExit

if len(password) < 8:
    print("Password must contain at least 8 characters.")
    raise SystemExit

connection = None
cursor = None

try:
    connection = get_db_connection()
    cursor = connection.cursor()

    password_hash = generate_password_hash(password)

    query = """
        INSERT INTO users
        (name, email, password_hash, role, department)
        VALUES (%s, %s, %s, 'admin', %s)
    """

    cursor.execute(
        query,
        (name, email, password_hash, "Administration")
    )

    connection.commit()

    print("Admin account created successfully!")

except Exception as error:
    if connection and connection.is_connected():
        connection.rollback()

    print("Error creating admin:", error)

finally:
    if cursor is not None:
        cursor.close()

    if connection is not None and connection.is_connected():
        connection.close()
