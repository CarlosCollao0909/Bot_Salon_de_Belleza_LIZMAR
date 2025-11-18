"""
Utilidades para manejo de fechas
"""
from datetime import datetime


def es_domingo(fecha_str):
    """
    Verifica si una fecha es domingo
    
    Args:
        fecha_str (str): Fecha en formato 'YYYY-MM-DD'
    
    Returns:
        bool: True si es domingo, False si no
    """
    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        return fecha_obj.weekday() == 6  # 6 = Domingo
    except Exception as e:
        print(f"Error al verificar si es domingo: {e}")
        return False


def es_fecha_pasada(fecha_str):
    """
    Verifica si una fecha ya pasó
    
    Args:
        fecha_str (str): Fecha en formato 'YYYY-MM-DD'
    
    Returns:
        bool: True si la fecha ya pasó, False si no
    """
    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        fecha_hoy = datetime.now().date()
        return fecha_obj.date() < fecha_hoy
    except Exception as e:
        print(f"Error al verificar si es fecha pasada: {e}")
        return False


def formatear_fecha_legible(fecha_str):
    """
    Convierte fecha de YYYY-MM-DD a formato legible DD/MM/YYYY con día de la semana
    
    Args:
        fecha_str (str): Fecha en formato 'YYYY-MM-DD'
    
    Returns:
        dict: {'fecha': 'DD/MM/YYYY', 'dia': 'Lunes', 'dia_corto': 'Lun'}
    """
    dias_es = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    
    dias_cortos = {
        'Monday': 'Lun', 'Tuesday': 'Mar', 'Wednesday': 'Mié',
        'Thursday': 'Jue', 'Friday': 'Vie', 'Saturday': 'Sáb', 'Sunday': 'Dom'
    }
    
    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        dia_semana = fecha_obj.strftime('%A')
        
        return {
            'fecha': fecha_obj.strftime('%d/%m/%Y'),
            'dia': dias_es.get(dia_semana, dia_semana),
            'dia_corto': dias_cortos.get(dia_semana, dia_semana[:3])
        }
    except Exception as e:
        print(f"Error al formatear fecha: {e}")
        return {'fecha': fecha_str, 'dia': '', 'dia_corto': ''}