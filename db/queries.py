from db.connection import connect_db


def get_horarios():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM horarios WHERE estado = 1")
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
        cursor.execute("SELECT * FROM servicios WHERE estado = 1")
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


def verificar_usuario_y_citas(email, telefono):
    """Verifica usuario y retorna sus citas próximas"""
    try:
        conn = connect_db()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        
        # Verificar usuario
        query_usuario = """
            SELECT id, nombre, apellido 
            FROM usuarios 
            WHERE email = %s AND telefono = %s
        """
        cursor.execute(query_usuario, (email, telefono))
        usuario = cursor.fetchone()
        
        if not usuario:
            conn.close()
            return None
        
        # Obtener citas futuras del usuario
        query_citas = """
            SELECT 
                c.id,
                c.fecha,
                c.estado,
                s.nombre as servicio,
                s.precio,
                CONCAT(h.horaInicio, ' - ', horaFin) as horario,
                fp.tipo as forma_pago
            FROM citas c
            JOIN servicios s ON c.servicioID = s.id
            JOIN horarios h ON c.horarioID = h.id
            LEFT JOIN formaspagos fp ON c.formaPagoID = fp.id
            WHERE c.usuarioID = %s 
            AND c.fecha >= CURDATE()
            ORDER BY c.fecha ASC, h.horaInicio ASC
        """
        cursor.execute(query_citas, (usuario['id'],))
        citas = cursor.fetchall()
        
        conn.close()
        
        return {
            'usuario': usuario,
            'citas': citas
        }
        
    except Exception as e:
        print(f"Error al verificar usuario: {e}")
        return None

def get_horarios_disponibles(fecha):
    """
    Obtiene los horarios disponibles para una fecha específica
    Args:
        fecha: string en formato 'YYYY-MM-DD'
    Returns:
        dict con horarios_disponibles y horarios_ocupados
    """
    try:
        conn = connect_db()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        
        # Obtener TODOS los horarios activos del salón
        query_todos = """
            SELECT id, horaInicio, horaFin
            FROM horarios
            WHERE estado = 1
            ORDER BY horaInicio ASC
        """
        cursor.execute(query_todos)
        todos_horarios = cursor.fetchall()
        
        # Obtener horarios YA OCUPADOS en esa fecha (solo confirmadas)
        query_ocupados = """
            SELECT horarioID
            FROM citas
            WHERE fecha = %s
            AND estado = 'confirmada'
        """
        cursor.execute(query_ocupados, (fecha,))
        ocupados = cursor.fetchall()
        
        conn.close()
        
        # IDs de horarios ocupados
        ids_ocupados = [h['horarioID'] for h in ocupados]
        
        # Separar disponibles de ocupados
        horarios_disponibles = [h for h in todos_horarios if h['id'] not in ids_ocupados]
        horarios_ocupados = [h for h in todos_horarios if h['id'] in ids_ocupados]
        
        return {
            'disponibles': horarios_disponibles,
            'ocupados': horarios_ocupados,
            'fecha': fecha
        }
        
    except Exception as e:
        print(f"Error al obtener horarios disponibles: {e}")
        return None