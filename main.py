from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import google.generativeai as genai

from context.context import build_context

from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key = os.getenv('GOOGLE_API_KEY'))
modelo = genai.GenerativeModel('gemini-2.5-flash-lite-preview-09-2025')

### COMANDO /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('<b>¡Hola!</b> Soy <i>LIZMAR BOT</i>, el asistente virtual del salón de belleza LIZMAR. ¿En qué puedo ayudarte hoy?', parse_mode='HTML')

### COMANDO /ubicacion
async def ubicacion_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contexto = build_context()
    orden_final = f"{contexto}\n\nUsuario: ¿Dónde está ubicado el salón de belleza LIZMAR?\nLIZMAR BOT:"
    respuesta = modelo.generate_content(orden_final)
    texto_respuesta = respuesta.text.strip() if respuesta.text else "Lo siento, no pude generar una respuesta en este momento."
    await update.message.reply_text(texto_respuesta, parse_mode='HTML')

### COMANDO /servicios
async def servicios_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contexto = build_context()
    orden_final = f"{contexto}\n\nUsuario: ¿Qué servicios ofrecen en el salón?\nLIZMAR BOT:"
    respuesta = modelo.generate_content(orden_final)
    texto_respuesta = respuesta.text.strip() if respuesta.text else "Lo siento, no pude generar una respuesta en este momento."
    await update.message.reply_text(texto_respuesta, parse_mode='HTML')

### COMANDO /horarios
async def horarios_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contexto = build_context()
    orden_final = f"{contexto}\n\nUsuario: ¿Cuáles son los horarios de atención del salón?\nLIZMAR BOT:"
    respuesta = modelo.generate_content(orden_final)
    texto_respuesta = respuesta.text.strip() if respuesta.text else "Lo siento, no pude generar una respuesta en este momento."
    await update.message.reply_text(texto_respuesta, parse_mode='HTML')

### COMANDO /formaspago
async def formaspago_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contexto = build_context()
    orden_final = f"{contexto}\n\nUsuario: ¿Qué formas de pago aceptan en el salón?\nLIZMAR BOT:"
    respuesta = modelo.generate_content(orden_final)
    texto_respuesta = respuesta.text.strip() if respuesta.text else "Lo siento, no pude generar una respuesta en este momento."
    await update.message.reply_text(texto_respuesta, parse_mode='HTML')

### RESPONDER MENSAJES
async def responder_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_usuario = update.message.text
    await update.message.chat.send_action(action='typing')

    try:
        contexto = build_context()
        orden_final = f"{contexto}\n\nUsuario: {mensaje_usuario}\nLIZMAR BOT:"
        respuesta = modelo.generate_content(orden_final)
        texto_respuesta = respuesta.text.strip() if respuesta.text else "Lo siento, no pude generar una respuesta en este momento."
    except Exception as e:
        texto_respuesta = f"Lo siento, ocurrió un error al procesar tu solicitud: {e}"

    await update.message.reply_text(texto_respuesta, parse_mode='HTML')

def main():
    app = ApplicationBuilder().token(os.getenv('TELEGRAM_API_KEY')).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ubicacion", ubicacion_command))
    app.add_handler(CommandHandler("servicios", servicios_command))
    app.add_handler(CommandHandler("horarios", horarios_command))
    app.add_handler(CommandHandler("formaspago", formaspago_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_mensaje))

    print("Bot iniciado...")
    app.run_polling()

if __name__ == '__main__':
    main()