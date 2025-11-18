"""
Utilidades para interacción con Google Gemini
"""
import google.generativeai as genai
from datetime import datetime
import json
import os


modelo = genai.GenerativeModel('gemini-2.5-flash-lite-preview-09-2025')


async def extraer_fecha_con_gemini(texto_usuario):
    """
    Usa Gemini para interpretar fechas en lenguaje natural
    
    Args:
        texto_usuario (str): Texto del usuario que puede contener una fecha
    
    Returns:
        dict: {'fecha': 'YYYY-MM-DD' | None, 'encontrado': bool}
    """
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    dia_hoy = datetime.now().strftime('%A')
    
    # Traducir día actual al español
    dias_es = {
        'Monday': 'lunes', 'Tuesday': 'martes', 'Wednesday': 'miércoles',
        'Thursday': 'jueves', 'Friday': 'viernes', 'Saturday': 'sábado', 'Sunday': 'domingo'
    }
    dia_hoy_es = dias_es.get(dia_hoy, dia_hoy)
    
    prompt = f"""
Hoy es {dia_hoy_es} {fecha_hoy} (formato YYYY-MM-DD).

El usuario escribió: "{texto_usuario}"

Si el usuario está preguntando por horarios disponibles, disponibilidad o cuándo puede agendar, extrae la fecha mencionada.

IMPORTANTE: 
- Si dice "mañana", suma 1 día a {fecha_hoy}
- Si dice "pasado mañana", suma 2 días
- Si dice "hoy", usa {fecha_hoy}
- Si dice un día de la semana (ej: "el sábado", "próximo martes"), calcula la fecha del próximo día que coincida
- Si dice una fecha específica (ej: "25 de noviembre", "19/11"), convierte a formato YYYY-MM-DD

Responde SOLO con este JSON (sin comentarios, sin markdown, sin texto adicional):
{{"fecha": "YYYY-MM-DD", "encontrado": true}}

Si NO menciona una fecha clara, responde:
{{"fecha": null, "encontrado": false}}

Ejemplos válidos:
- "horarios para mañana" → {{"fecha": "{_sumar_dias(fecha_hoy, 1)}", "encontrado": true}}
- "disponibilidad el 25 de noviembre" → {{"fecha": "2025-11-25", "encontrado": true}}
- "el próximo sábado" → {{"fecha": "2025-11-23", "encontrado": true}}
- "hola" → {{"fecha": null, "encontrado": false}}
"""
    
    try:
        respuesta = modelo.generate_content(prompt)
        texto = respuesta.text.strip()
        
        # Limpiar respuesta (quitar markdown si existe)
        texto = texto.replace('```json', '').replace('```', '').strip()
        
        resultado = json.loads(texto)
        return resultado
        
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON de Gemini: {e}")
        print(f"Respuesta de Gemini: {texto if 'texto' in locals() else 'N/A'}")
        return {"fecha": None, "encontrado": False}
        
    except Exception as e:
        print(f"Error al extraer fecha con Gemini: {e}")
        return {"fecha": None, "encontrado": False}


def _sumar_dias(fecha_str, dias):
    """Función auxiliar para sumar días a una fecha"""
    from datetime import timedelta
    fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
    nueva_fecha = fecha_obj + timedelta(days=dias)
    return nueva_fecha.strftime('%Y-%m-%d')