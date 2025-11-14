from connection import connect_db

conn = connect_db()

def get_horarios():
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM horarios")
        resultados = cursor.fetchall()
        print(f'Horarios obtenidos: {resultados}')
        return resultados
    except Exception as e:
        print(f"Error al obtener los horarios: {e}")
        return []
    
def get_servicios():
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM servicios")
        resultados = cursor.fetchall()
        print(f'Servicios obtenidos: {resultados}')
        return resultados
    except Exception as e:
        print(f"Error al obtener los servicios: {e}")
        return []
    
def get_formas_pago():
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, tipo FROM formas_pago")
        resultados = cursor.fetchall()
        print(f'Formas de pago obtenidas: {resultados}')
        return resultados
    except Exception as e:
        print(f"Error al obtener las formas de pago: {e}")
        return []