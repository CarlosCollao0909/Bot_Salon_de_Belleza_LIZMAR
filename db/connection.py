import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def connect_db():
    try:
        conn = mysql.connector.connect(
            host = os.getenv('DB_HOST'),
            user = os.getenv('DB_USER'),
            password = os.getenv('DB_PASSWORD'),
            database = os.getenv('DB_NAME')
        )
        return conn
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def close_db(conn):
    if conn:
        conn.close()

connect_db()