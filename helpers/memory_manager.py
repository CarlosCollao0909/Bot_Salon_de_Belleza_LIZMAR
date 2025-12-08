"""
Sistema de memoria conversacional para el bot LIZMAR
"""
from datetime import datetime, timedelta
from collections import deque

class ConversationMemory:
    """Gestiona la memoria conversacional de cada usuario"""
    
    def __init__(self, max_messages=10, session_timeout_minutes=30):
        """
        Args:
            max_messages: Número máximo de mensajes a recordar
            session_timeout_minutes: Tiempo en minutos antes de resetear la conversación
        """
        self.max_messages = max_messages
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
    
    def get_history(self, context):
        """Obtiene el historial de conversación del usuario"""
        if 'conversation_history' not in context.user_data:
            context.user_data['conversation_history'] = deque(maxlen=self.max_messages)
            context.user_data['last_interaction'] = datetime.now()
        
        # Verificar si la sesión expiró
        last_time = context.user_data.get('last_interaction', datetime.now())
        if datetime.now() - last_time > self.session_timeout:
            # Sesión expirada, resetear historial
            context.user_data['conversation_history'] = deque(maxlen=self.max_messages)
        
        return context.user_data['conversation_history']
    
    def add_message(self, context, role, content):
        """
        Agrega un mensaje al historial
        
        Args:
            role: 'user' o 'assistant'
            content: Contenido del mensaje
        """
        history = self.get_history(context)
        history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        context.user_data['last_interaction'] = datetime.now()
    
    def format_for_gemini(self, context):
        """
        Formatea el historial para enviarlo a Gemini
        Returns: String formateado con el historial
        """
        history = self.get_history(context)
        
        if not history:
            return ""
        
        formatted = "\n\n━━━━ HISTORIAL DE CONVERSACIÓN ━━━━\n\n"
        
        for msg in history:
            role_label = "Usuario" if msg['role'] == 'user' else "LIZMAR BOT"
            formatted += f"{role_label}: {msg['content']}\n\n"
        
        formatted += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        return formatted
    
    def clear_history(self, context):
        """Limpia el historial de conversación"""
        if 'conversation_history' in context.user_data:
            context.user_data['conversation_history'] = deque(maxlen=self.max_messages)
        context.user_data['last_interaction'] = datetime.now()
    
    def get_summary(self, context):
        """Obtiene un resumen del historial"""
        history = self.get_history(context)
        
        if not history:
            return "No hay historial de conversación"
        
        total = len(history)
        last_time = context.user_data.get('last_interaction', datetime.now())
        time_ago = datetime.now() - last_time
        
        return {
            'total_messages': total,
            'last_interaction': time_ago,
            'session_active': time_ago < self.session_timeout
        }


# Instancia global del gestor de memoria
memory_manager = ConversationMemory(max_messages=10, session_timeout_minutes=30)