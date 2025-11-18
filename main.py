from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    ContextTypes, 
    filters,
    ConversationHandler,
    CallbackQueryHandler
)
import google.generativeai as genai

from context.context import build_context
from db.queries import verificar_usuario_y_citas

from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key = os.getenv('GOOGLE_API_KEY'))
modelo = genai.GenerativeModel('gemini-2.5-flash-lite-preview-09-2025')

# Estados para ConversationHandler
EMAIL, TELEFONO = range(2)

### COMANDO /start con menú de botones MINIMALISTA
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📋 Servicios", callback_data='servicios'),
            InlineKeyboardButton("📍 Ubicación", callback_data='ubicacion')
        ],
        [
            InlineKeyboardButton("❓ Ayuda", callback_data='ayuda')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    mensaje = (
        "<b>¡Hola! 👋</b>\n\n"
        "Soy <i>LIZMAR BOT</i>, el asistente virtual del salón de belleza LIZMAR.\n\n"
        "Selecciona una opción o escríbeme directamente lo que necesites:"
    )
    
    await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='HTML')

### COMANDO /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "📚 <b>Guía de uso de LIZMAR BOT</b>\n\n"
        
        "<b>🤖 Comandos disponibles:</b>\n\n"
        
        "• /start - Menú principal con botones interactivos\n"
        "• /help - Muestra esta guía de ayuda\n"
        "• /servicios - Lista de servicios y precios\n"
        "• /horarios - Horarios de atención del salón\n"
        "• /formaspago - Formas de pago aceptadas\n"
        "• /ubicacion - Dirección del salón\n"
        "• /miscitas - Consulta tus citas programadas\n"
        "• /cancelar - Cancela una operación en curso\n\n"
        
        "<b>💬 Interacción natural:</b>\n"
        "También puedes escribirme en lenguaje natural y te responderé. Por ejemplo:\n"
        "• \"¿Cuánto cuesta un corte?\"\n"
        "• \"¿Están abiertos mañana?\"\n"
        "• \"Quiero saber sobre los servicios\"\n\n"
        
        "<b>🔐 Consulta de citas:</b>\n"
        "Para ver tus citas programadas, usa /miscitas\n"
        "Te pediré tu email y teléfono para verificar tu identidad.\n\n"
        
        "<b>📞 ¿Necesitas más ayuda?</b>\n"
        "Si tienes alguna duda, puedes visitarnos en el salón o llamarnos directamente.\n\n"
        
        "¡Estoy aquí para ayudarte! 😊"
    )
    
    await update.message.reply_text(mensaje, parse_mode='HTML')

### Handler para botones inline
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # botones con respuestas directas
    if query.data == 'ayuda':
        mensaje = (
            "📚 <b>Guía resumida de uso de LIZMAR BOT</b>\n\n"
            
            "<b>🤖 Comandos disponibles:</b>\n\n"
            
            "• /start - Menú principal\n"
            "• /help - Muestra esta guía de forma detallada\n"
            "• /servicios - Servicios y precios\n"
            "• /horarios - Horarios de atención\n"
            "• /formaspago - Formas de pago\n"
            "• /ubicacion - Dirección del salón\n"
            "• /miscitas - Consulta tus citas\n\n"
            
            "<b>💬 Interacción natural:</b>\n"
            "También puedes escribirme en lenguaje natural y te responderé usando inteligencia artificial.\n\n"
            
            "Ejemplo: \"¿Cuánto cuesta un corte?\"\n\n"
            
            "¡Estoy aquí para ayudarte! 😊"
        )
    
    elif query.data == 'servicios':
        # Obtener servicios directo de BD
        from db.queries import get_servicios
        servicios = get_servicios()
        
        mensaje = "📋 <b>Servicios disponibles en LIZMAR:</b>\n\n"
        
        if servicios:
            for servicio in servicios:
                mensaje += f"• <b>{servicio[1]}:</b> {servicio[2]} Bs\n"
        else:
            mensaje += "No hay servicios registrados actualmente.\n"
        
        mensaje += "\n💡 <i>¿Te gustaría agendar una cita? Usa nuestro sistema web o llámanos directamente.</i>"
    
    elif query.data == 'ubicacion':
        mensaje = (
            "📍 <b>Ubicación del Salón de Belleza LIZMAR:</b>\n\n"
            "El salón de belleza LIZMAR se encuentra ubicado en Avenida Barrientos, cerca de la intersección con la Calle Corneta Mamani, en la ciudad de Oruro - Bolivia.\n\n"
            "¡Te esperamos para brindarte el mejor servicio! 💇‍♀️✂️💅"
        )
    else:
        mensaje = "⚠️ Opción no reconocida."
    
    try:
        await query.edit_message_text(mensaje, parse_mode='HTML')
    except Exception as e:
        print(f"Error al editar mensaje: {e}")
        await query.message.reply_text(mensaje, parse_mode='HTML')


### CONSULTA DE CITAS - Paso 1: Recibir email
async def recibir_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip().lower()
    
    # Validación básica
    if '@' not in email or '.' not in email:
        await update.message.reply_text(
            "❌ Por favor envía un correo electrónico válido.\n"
            "Ejemplo: usuario@ejemplo.com"
        )
        return EMAIL
    
    context.user_data['email'] = email
    
    await update.message.reply_text(
        "✅ Perfecto. Ahora envíame tu <b>número de teléfono</b> registrado (8 dígitos):",
        parse_mode='HTML'
    )
    return TELEFONO

### CONSULTA DE CITAS - Paso 2: Recibir teléfono y verificar
async def recibir_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telefono = update.message.text.strip()
    email = context.user_data.get('email')
    
    # Validación básica (8 dígitos según tu BD)
    if not telefono.isdigit():
        await update.message.reply_text(
            "❌ El teléfono debe contener solo números."
        )
        return TELEFONO
    
    if len(telefono) != 8:
        await update.message.reply_text(
            "❌ El teléfono debe tener exactamente 8 dígitos.\n"
            "Ejemplo: 71234567"
        )
        return TELEFONO
    
    if not telefono.startswith(('6', '7')):
        await update.message.reply_text(
            "❌ El número de teléfono no parece válido.\n"
            "Los números en Bolivia comienzan con 6 o 7."
        )
        return TELEFONO
    
    await update.message.chat.send_action(action='typing')
    
    # Verificar en BD
    try:
        resultado = verificar_usuario_y_citas(email, telefono)
    except Exception as e:
        print(f"Error al verificar usuario: {e}")
        await update.message.reply_text(
            "⚠️ Ocurrió un error al consultar la base de datos. Por favor intenta nuevamente.",
            parse_mode='HTML'
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    if not resultado:
        await update.message.reply_text(
            "❌ <b>No encontré un usuario registrado con esos datos.</b>\n\n"
            "Por favor verifica que:\n"
            "• El correo electrónico sea correcto\n"
            "• El teléfono tenga 8 dígitos\n"
            "• Estés registrado en nuestro sistema\n\n"
            "Si necesitas ayuda, puedes visitarnos en el salón.",
            parse_mode='HTML'
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # Usuario encontrado
    usuario = resultado['usuario']
    citas = resultado['citas']
    
    nombre_completo = f"{usuario['nombre']} {usuario['apellido']}"
    
    if not citas:
        mensaje = (
            f"✅ <b>Hola {nombre_completo}!</b> 👋\n\n"
            f"No tienes citas programadas actualmente.\n\n"
            f"¿Deseas agendar una? Puedes hacerlo desde nuestro sistema web."
        )
    else:
        mensaje = f"✅ <b>Hola {nombre_completo}!</b> 👋\n\n"
        mensaje += f"Tienes <b>{len(citas)}</b> cita(s) próxima(s):\n\n"
        
        for i, cita in enumerate(citas, 1):
            # Formatear fecha (de YYYY-MM-DD a formato más legible)
            fecha_obj = cita['fecha']
            try:
                fecha_legible = fecha_obj.strftime('%d/%m/%Y')
            except:
                fecha_legible = str(fecha_obj)
            
            mensaje += f"<b>{i}. {cita['servicio']}</b>\n"
            mensaje += f"   📅 Fecha: {fecha_legible}\n"
            mensaje += f"   🕐 Horario: {cita['horario']}\n"
            mensaje += f"   💰 Precio: {cita['precio']} Bs\n"
            mensaje += f"   📊 Estado: {cita['estado']}\n"
            
            if cita['forma_pago']:
                mensaje += f"   💳 Forma de pago: {cita['forma_pago']}\n"
            
            mensaje += "\n"
        
        mensaje += "💡 <i>Para cancelar alguna cita (con tiempo de anticipación), por favor ingresa a nuestro sistema web.</i>"
    
    await update.message.reply_text(mensaje, parse_mode='HTML')
    
    # Limpiar datos del usuario
    context.user_data.clear()
    
    return ConversationHandler.END

### Cancelar conversación
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Operación cancelada.\n\n"
        "Si necesitas ayuda, escribe /start"
    )
    context.user_data.clear()
    return ConversationHandler.END

### COMANDO /miscitas directo
async def miscitas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📅 <b>Consulta de Citas</b>\n\n"
        "Para verificar tu identidad, por favor envíame tu <b>correo electrónico</b> registrado:",
        parse_mode='HTML'
    )
    return EMAIL

### COMANDO /ubicacion
async def ubicacion_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action='typing')
    contexto = build_context()
    orden_final = f"{contexto}\n\nUsuario: ¿Dónde está ubicado el salón?\nLIZMAR BOT:"
    
    try:
        respuesta = modelo.generate_content(orden_final)
        texto_respuesta = respuesta.text.strip() if respuesta.text else "Lo siento, no pude generar una respuesta."
    except Exception as e:
        print(f"Error al generar respuesta: {e}")
        texto_respuesta = "⚠️ Lo siento, el servicio está temporalmente ocupado. Por favor intenta nuevamente."
    
    await update.message.reply_text(texto_respuesta, parse_mode='HTML')

### COMANDO /servicios
async def servicios_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action='typing')
    contexto = build_context()
    orden_final = f"{contexto}\n\nUsuario: ¿Qué servicios ofrecen?\nLIZMAR BOT:"
    
    try:
        respuesta = modelo.generate_content(orden_final)
        texto_respuesta = respuesta.text.strip() if respuesta.text else "Lo siento, no pude generar una respuesta."
    except Exception as e:
        print(f"Error al generar respuesta: {e}")
        texto_respuesta = "⚠️ Lo siento, el servicio está temporalmente ocupado. Por favor intenta nuevamente."
    
    await update.message.reply_text(texto_respuesta, parse_mode='HTML')

### COMANDO /horarios
async def horarios_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action='typing')
    contexto = build_context()
    orden_final = f"{contexto}\n\nUsuario: ¿Cuáles son los horarios?\nLIZMAR BOT:"
    
    try:
        respuesta = modelo.generate_content(orden_final)
        texto_respuesta = respuesta.text.strip() if respuesta.text else "Lo siento, no pude generar una respuesta."
    except Exception as e:
        print(f"Error al generar respuesta: {e}")
        texto_respuesta = "⚠️ Lo siento, el servicio está temporalmente ocupado. Por favor intenta nuevamente."
    
    await update.message.reply_text(texto_respuesta, parse_mode='HTML')

### COMANDO /formaspago
async def formaspago_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action='typing')
    contexto = build_context()
    orden_final = f"{contexto}\n\nUsuario: ¿Qué formas de pago aceptan?\nLIZMAR BOT:"
    
    try:
        respuesta = modelo.generate_content(orden_final)
        texto_respuesta = respuesta.text.strip() if respuesta.text else "Lo siento, no pude generar una respuesta."
    except Exception as e:
        print(f"Error al generar respuesta: {e}")
        texto_respuesta = "⚠️ Lo siento, el servicio está temporalmente ocupado. Por favor intenta nuevamente."
    
    await update.message.reply_text(texto_respuesta, parse_mode='HTML')

### FUNCIÓN AUXILIAR: Extraer fecha con Gemini
async def extraer_fecha_con_gemini(texto_usuario):
    """
    Usa Gemini para interpretar fechas en lenguaje natural
    """
    from datetime import datetime
    
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
- "horarios para mañana" → {{"fecha": "2025-11-18", "encontrado": true}}
- "disponibilidad el 25 de noviembre" → {{"fecha": "2025-11-25", "encontrado": true}}
- "el próximo sábado" → {{"fecha": "2025-11-23", "encontrado": true}}
- "hola" → {{"fecha": null, "encontrado": false}}
"""
    
    try:
        respuesta = modelo.generate_content(prompt)
        texto = respuesta.text.strip()
        
        # Limpiar respuesta (quitar markdown si existe)
        texto = texto.replace('```json', '').replace('```', '').strip()
        
        import json
        resultado = json.loads(texto)
        
        return resultado
    except Exception as e:
        print(f"Error al extraer fecha: {e}")
        print(f"Respuesta de Gemini: {texto if 'texto' in locals() else 'N/A'}")
        return {"fecha": None, "encontrado": False}
    
### FUNCIÓN AUXILIAR: Validar si la fecha es domingo
def es_domingo(fecha_str):
    """
    Verifica si una fecha es domingo
    Args:
        fecha_str: string en formato 'YYYY-MM-DD'
    Returns:
        bool: True si es domingo, False si no
    """
    from datetime import datetime
    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        return fecha_obj.weekday() == 6  # 6 = Domingo
    except:
        return False
    
### RESPONDER MENSAJES (con detección de consulta de disponibilidad)
async def responder_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_usuario = update.message.text
    mensaje_lower = mensaje_usuario.lower()
    
    # Detectar si pregunta por disponibilidad/horarios libres
    palabras_clave = ['disponible', 'disponibilidad', 'horario', 'libre', 'ocupado', 'agendar', 'cuando', 'cuándo']
    
    if any(palabra in mensaje_lower for palabra in palabras_clave):
        await update.message.chat.send_action(action='typing')
        
        # Intentar extraer fecha con Gemini
        resultado = await extraer_fecha_con_gemini(mensaje_usuario)
        
        if resultado['encontrado'] and resultado['fecha']:
            fecha = resultado['fecha']
            
            # Validar si es domingo
            if es_domingo(fecha):
                from datetime import datetime
                try:
                    fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
                    fecha_legible = fecha_obj.strftime('%d/%m/%Y')
                except:
                    fecha_legible = fecha
                
                await update.message.reply_text(
                    f"❌ <b>Los domingos el salón está cerrado</b>\n\n"
                    f"La fecha {fecha_legible} es domingo. El salón de belleza LIZMAR no atiende los domingos.\n\n"
                    f"<b>Días de atención:</b> Lunes a Sábado\n"
                    f"• Mañana: 09:00 - 12:00\n"
                    f"• Tarde: 15:00 - 21:00\n\n"
                    f"¿Te gustaría consultar otro día? 📅",
                    parse_mode='HTML'
                )
                return
            
            # Obtener horarios disponibles
            from db.queries import get_horarios_disponibles
            from datetime import datetime
            
            horarios_info = get_horarios_disponibles(fecha)
            
            if not horarios_info:
                await update.message.reply_text(
                    "⚠️ Ocurrió un error al consultar los horarios. Intenta nuevamente."
                )
                return
            
            # Formatear fecha legible
            try:
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
                fecha_legible = fecha_obj.strftime('%d/%m/%Y')
                dia_semana = fecha_obj.strftime('%A')
                
                # Traducir día al español
                dias = {
                    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
                }
                dia_es = dias.get(dia_semana, dia_semana)
            except:
                fecha_legible = fecha
                dia_es = ""
            
            # Construir mensaje
            mensaje_respuesta = f"📅 <b>Disponibilidad para el {dia_es} {fecha_legible}:</b>\n\n"
            
            if not horarios_info['disponibles'] and not horarios_info['ocupados']:
                mensaje_respuesta += "⚠️ No hay horarios de atención registrados para consultar.\n"
            elif not horarios_info['disponibles']:
                mensaje_respuesta += "❌ <b>Lo sentimos, no hay horarios disponibles para esta fecha.</b>\n\n"
                mensaje_respuesta += "<b>Todos los horarios están ocupados:</b>\n"
                for h in horarios_info['ocupados']:
                    inicio = str(h['horaInicio'])[:5]  # Formato HH:MM
                    fin = str(h['horaFin'])[:5]
                    mensaje_respuesta += f"❌ {inicio} - {fin}\n"
                mensaje_respuesta += "\n💡 <i>¿Te gustaría consultar otro día?</i>"
            else:
                mensaje_respuesta += "<b><i> Horarios disponibles: </i></b>\n"
                for h in horarios_info['disponibles']:
                    inicio = str(h['horaInicio'])[:5]  # Formato HH:MM
                    fin = str(h['horaFin'])[:5]
                    mensaje_respuesta += f"✅ {inicio} - {fin}\n"
                
                if horarios_info['ocupados']:
                    mensaje_respuesta += f"\n<b><i> Horarios ocupados: </i></b>\n"
                    for h in horarios_info['ocupados']:
                        inicio = str(h['horaInicio'])[:5]
                        fin = str(h['horaFin'])[:5]
                        mensaje_respuesta += f"❌ {inicio} - {fin}\n"
                
                mensaje_respuesta += "\n💡 <i>Para agendar una cita, ingresa a nuestro sistema web.</i>"
            
            await update.message.reply_text(mensaje_respuesta, parse_mode='HTML')
            return
    
    # Si no es consulta de disponibilidad, respuesta normal con Gemini
    await update.message.chat.send_action(action='typing')
    
    try:
        contexto = build_context()
        orden_final = f"{contexto}\n\nUsuario: {mensaje_usuario}\nLIZMAR BOT:"
        respuesta = modelo.generate_content(orden_final)
        texto_respuesta = respuesta.text.strip() if respuesta.text else "Lo siento, no pude generar una respuesta."
    except Exception as e:
        print(f"Error al procesar mensaje: {e}")
        texto_respuesta = "⚠️ Lo siento, el servicio está temporalmente ocupado. Por favor intenta nuevamente en unos momentos o usa los comandos del menú: /start"

    await update.message.reply_text(texto_respuesta, parse_mode='HTML')

def main():
    app = ApplicationBuilder().token(os.getenv('TELEGRAM_API_KEY')).build()

    # Agregar handlers para botones que NO inician conversación PRIMERO
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^(servicios|ubicacion|ayuda)$'))

    # ConversationHandler para consulta de citas
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('miscitas', miscitas_command)
        ],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_email)],
            TELEFONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_telefono)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)],
        per_chat=True,
        per_user=True,
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("ubicacion", ubicacion_command))
    app.add_handler(CommandHandler("servicios", servicios_command))
    app.add_handler(CommandHandler("horarios", horarios_command))
    app.add_handler(CommandHandler("formaspago", formaspago_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_mensaje))

    print("🤖 Bot LIZMAR iniciado correctamente...")
    print("📊 Presiona Ctrl+C para detener el bot")
    app.run_polling()

if __name__ == '__main__':
    main()