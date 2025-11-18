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