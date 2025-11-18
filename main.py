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

### RESPONDER MENSAJES
async def responder_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_usuario = update.message.text
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