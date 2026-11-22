import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

print("Host:", os.getenv("DB_HOST"))
print("User:", os.getenv("DB_USER"))
print("Database:", os.getenv("DB_NAME"))
print("Port:", os.getenv("DB_PORT"))
print("Password configured:", bool(os.getenv("DB_PASSWORD")))

try:
    print("\nTrying MySQL connection...")

    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", "3306")),
        connection_timeout=5,
        use_pure=True
    )

    print("SUCCESS! Connected to MySQL.")

    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")

    for row in cursor.fetchall():
        print(row[0])

    cursor.close()
    connection.close()

except Exception as error:
    print("CONNECTION ERROR:", repr(error))
