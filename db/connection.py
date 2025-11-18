import mysql.connector
from dotenv import load_dotenv
import os
import time

load_dotenv()

def connect_db(reintentos=3):
    """Conecta a la base de datos con reintentos"""
    for intento in range(reintentos):
        try:
            conn = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                autocommit=True
            )
            return conn
        except Exception as e:
            print(f"Intento {intento + 1}/{reintentos} - Error al conectar: {e}")
            if intento < reintentos - 1:
                time.sleep(2)
            else:
                return None

def close_db(conn):
    """Cierra la conexión de forma segura"""
    if conn and conn.is_connected():
        conn.close()