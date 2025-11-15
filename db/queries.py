from db.connection import connect_db


def get_horarios():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM horarios")
        resultados = cursor.fetchall()
        conn.close()
        return resultados
    except Exception as e:
        print(f"Error al obtener los horarios: {e}")
        return []
    
def get_servicios():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM servicios")
        resultados = cursor.fetchall()
        conn.close()
        return resultados
    except Exception as e:
        print(f"Error al obtener los servicios: {e}")
        return []
    
def get_formas_pago():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, tipo FROM formaspagos")
        resultados = cursor.fetchall()
        conn.close()
        return resultados
    except Exception as e:
        print(f"Error al obtener las formas de pago: {e}")
        return []