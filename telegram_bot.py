import os
import json
import asyncio
import aiohttp
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Configuration
TELEGRAM_TOKEN = "7556773897:AAH_e2Piz8Q78TRWy55jilqmTxjfrhTAnjI"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
SVETLANA_API_URL = os.getenv("SVETLANA_API_URL", "https://svetlana-api-ak3a.onrender.com")

# Initialize FastAPI app
app = FastAPI(title="Svetlana Telegram Bot")

# Store user states (in production, use database)
user_states = {}

class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_TOKEN
        self.api_url = TELEGRAM_API_URL
        self.svetlana_url = SVETLANA_API_URL
    
    async def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram user"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                }
                async with session.post(f"{self.api_url}/sendMessage", json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Message sent to chat_id {chat_id}")
                        return True
                    else:
                        logger.error(f"Failed to send message: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def send_typing_action(self, chat_id: int) -> bool:
        """Send typing indicator"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "chat_id": chat_id,
                    "action": "typing"
                }
                async with session.post(f"{self.api_url}/sendChatAction", json=payload) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error sending typing action: {e}")
            return False
    
    def format_message_for_telegram(self, html_content: str) -> str:
        """Convert HTML content to Telegram-compatible format"""
        # Remove HTML tags but keep formatting
        text = html_content
        
        # Convert HTML tags to Telegram markdown
        text = re.sub(r'<p>(.*?)</p>', r'\1\n\n', text, flags=re.DOTALL)
        text = re.sub(r'<strong>(.*?)</strong>', r'*\1*', text)
        text = re.sub(r'<em>(.*?)</em>', r'_\1_', text)
        text = re.sub(r'<ul>(.*?)</ul>', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'<li>(.*?)</li>', r'• \1\n', text)
        text = re.sub(r'<br/?>', r'\n', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n\s*\n', r'\n\n', text)
        text = text.strip()
        
        return text
    
    async def call_svetlana_api(self, user_id: str, message: str, language: str = "es") -> Dict[str, Any]:
        """Call Svetlana API with user message"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "user_id": user_id,
                    "message": message,
                    "language": language
                }
                
                logger.info(f"Calling Svetlana API: {payload}")
                
                async with session.post(f"{self.svetlana_url}/message", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Svetlana API response: {result}")
                        return result
                    else:
                        logger.error(f"Svetlana API error: {response.status}")
                        return {"response": "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta de nuevo en unos momentos."}
        except Exception as e:
            logger.error(f"Error calling Svetlana API: {e}")
            return {"response": "Lo siento, estoy teniendo problemas de conexión. Por favor, intenta de nuevo en unos momentos."}
    
    async def register_user(self, user_id: str, password: str) -> Dict[str, Any]:
        """Register user with Svetlana API"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "user_id": user_id,
                    "password": password
                }
                
                logger.info(f"Registering user: {user_id}")
                
                async with session.post(f"{self.svetlana_url}/register", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Registration successful: {result}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Registration failed: {response.status} - {error_text}")
                        return {"error": f"Registration failed: {error_text}"}
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return {"error": "Connection error during registration"}
    
    async def login_user(self, user_id: str, password: str) -> Dict[str, Any]:
        """Login user with Svetlana API"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "user_id": user_id,
                    "password": password
                }
                
                logger.info(f"Logging in user: {user_id}")
                
                async with session.post(f"{self.svetlana_url}/login", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Login successful: {result}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Login failed: {response.status} - {error_text}")
                        return {"error": f"Login failed: {error_text}"}
        except Exception as e:
            logger.error(f"Error logging in user: {e}")
            return {"error": "Connection error during login"}

# Initialize bot
bot = TelegramBot()

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook"""
    try:
        data = await request.json()
        logger.info(f"Received webhook: {data}")
        
        # Extract message data
        if "message" not in data:
            return JSONResponse({"status": "ok"})
        
        message = data["message"]
        chat_id = message["chat"]["id"]
        user_id = str(message["from"]["id"])
        text = message.get("text", "")
        
        # Handle commands
        if text.startswith("/"):
            await handle_command(chat_id, user_id, text)
            return JSONResponse({"status": "ok"})
        
        # Handle regular messages
        await handle_message(chat_id, user_id, text)
        
        return JSONResponse({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JSONResponse({"status": "error", "message": str(e)})

async def handle_command(chat_id: int, user_id: str, command: str):
    """Handle Telegram commands"""
    if command == "/start":
        # Show the same greeting as the web version
        welcome_message = (
            "🤖 *¡Hola! Soy Eldric, tu coach emocional*\n\n"
            "Estoy aquí para ayudarte a entender mejor tus relaciones desde la teoría del apego.\n\n"
            "Para comenzar, escribe *'saludo inicial'* y te guiaré a través de un pequeño test que te ayudará a descubrir tu estilo de apego predominante.\n\n"
            "También puedes simplemente contarme cómo te sientes y te acompañaré desde ahí.\n\n"
            "¿Cómo te gustaría empezar?"
        )
        await bot.send_message(chat_id, welcome_message, parse_mode="Markdown")
    
    elif command == "/help":
        help_message = (
            "📚 *Comandos disponibles:*\n\n"
            "/start - Iniciar conversación\n"
            "/register - Crear una cuenta\n"
            "/login - Iniciar sesión\n"
            "/help - Mostrar esta ayuda\n"
            "/test - Realizar test de apego\n\n"
            "💡 *Consejos:*\n"
            "• Escribe 'saludo inicial' para comenzar\n"
            "• Comparte tus sentimientos libremente\n"
            "• Te haré preguntas para conocerte mejor\n"
            "• Regístrate para guardar tu progreso"
        )
        await bot.send_message(chat_id, help_message, parse_mode="Markdown")
    
    elif command == "/test":
        await bot.send_message(chat_id, "Para realizar el test, escribe *'saludo inicial'* y te guiaré paso a paso.", parse_mode="Markdown")
    
    elif command == "/register":
        # Set user state to registration
        user_states[user_id] = {"state": "registering", "step": "username"}
        register_message = (
            "📝 *Registro de cuenta*\n\n"
            "Vamos a crear tu cuenta paso a paso.\n\n"
            "Primero, elige un nombre de usuario (sin espacios):\n"
            "Ejemplo: *miusuario123*"
        )
        await bot.send_message(chat_id, register_message, parse_mode="Markdown")
    
    elif command == "/login":
        # Set user state to login
        user_states[user_id] = {"state": "logging_in", "step": "username"}
        login_message = (
            "🔐 *Iniciar sesión*\n\n"
            "Vamos a iniciar sesión en tu cuenta.\n\n"
            "Primero, escribe tu nombre de usuario:"
        )
        await bot.send_message(chat_id, login_message, parse_mode="Markdown")

async def handle_message(chat_id: int, user_id: str, text: str):
    """Handle regular text messages"""
    try:
        # Check if user is in a special state (registering or logging in)
        user_state = user_states.get(user_id, {})
        
        if user_state.get("state") == "registering":
            await handle_registration(chat_id, user_id, text, user_state)
            return
        elif user_state.get("state") == "logging_in":
            await handle_login(chat_id, user_id, text, user_state)
            return
        
        # Send typing indicator
        await bot.send_typing_action(chat_id)
        
        # Determine language (simple detection)
        language = "es"  # Default to Spanish
        if any(word in text.lower() for word in ["hello", "hi", "how are you"]):
            language = "en"
        elif any(word in text.lower() for word in ["привет", "здравствуйте"]):
            language = "ru"
        
        # Call Svetlana API - this will handle all the logic like the web version
        result = await bot.call_svetlana_api(user_id, text, language)
        
        if "response" in result:
            # Format response for Telegram
            formatted_response = bot.format_message_for_telegram(result["response"])
            
            # Send response
            await bot.send_message(chat_id, formatted_response, parse_mode="Markdown")
        else:
            await bot.send_message(chat_id, "Lo siento, no pude procesar tu mensaje. Por favor, intenta de nuevo.")
    
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await bot.send_message(chat_id, "Lo siento, ocurrió un error. Por favor, intenta de nuevo en unos momentos.")

async def handle_registration(chat_id: int, user_id: str, text: str, user_state: dict):
    """Handle user registration flow"""
    step = user_state.get("step", "username")
    
    if step == "username":
        # Validate username
        if len(text) < 3 or len(text) > 20 or " " in text:
            await bot.send_message(chat_id, "❌ El nombre de usuario debe tener entre 3 y 20 caracteres sin espacios. Intenta de nuevo:")
            return
        
        # Store username and move to password step
        user_states[user_id] = {
            "state": "registering", 
            "step": "password", 
            "username": text
        }
        
        await bot.send_message(chat_id, "✅ Nombre de usuario válido.\n\nAhora elige una contraseña (mínimo 6 caracteres):")
    
    elif step == "password":
        # Validate password
        if len(text) < 6:
            await bot.send_message(chat_id, "❌ La contraseña debe tener al menos 6 caracteres. Intenta de nuevo:")
            return
        
        # Get stored username
        username = user_state.get("username")
        
        # Register user with Svetlana API
        result = await bot.register_user(username, text)
        
        if "error" not in result:
            # Registration successful
            await bot.send_message(chat_id, "🎉 *¡Registro exitoso!*\n\nTu cuenta ha sido creada. Ahora puedes usar /login para iniciar sesión.", parse_mode="Markdown")
            # Clear user state
            user_states.pop(user_id, None)
        else:
            # Registration failed
            error_msg = result.get("error", "Error desconocido")
            if "already exists" in error_msg.lower():
                await bot.send_message(chat_id, "❌ Este nombre de usuario ya existe. Usa /register para intentar con otro nombre.")
            else:
                await bot.send_message(chat_id, f"❌ Error en el registro: {error_msg}\n\nIntenta de nuevo con /register")
            # Clear user state
            user_states.pop(user_id, None)

async def handle_login(chat_id: int, user_id: str, text: str, user_state: dict):
    """Handle user login flow"""
    step = user_state.get("step", "username")
    
    if step == "username":
        # Store username and move to password step
        user_states[user_id] = {
            "state": "logging_in", 
            "step": "password", 
            "username": text
        }
        
        await bot.send_message(chat_id, "Ahora escribe tu contraseña:")
    
    elif step == "password":
        # Get stored username
        username = user_state.get("username")
        
        # Login user with Svetlana API
        result = await bot.login_user(username, text)
        
        if "error" not in result:
            # Login successful
            await bot.send_message(chat_id, "✅ *¡Inicio de sesión exitoso!*\n\nAhora puedes usar todas las funciones. Escribe *'saludo inicial'* para comenzar.", parse_mode="Markdown")
            # Clear user state
            user_states.pop(user_id, None)
        else:
            # Login failed
            error_msg = result.get("error", "Error desconocido")
            if "invalid" in error_msg.lower() or "not found" in error_msg.lower():
                await bot.send_message(chat_id, "❌ Usuario o contraseña incorrectos. Usa /login para intentar de nuevo.")
            else:
                await bot.send_message(chat_id, f"❌ Error en el inicio de sesión: {error_msg}\n\nIntenta de nuevo con /login")
            # Clear user state
            user_states.pop(user_id, None)

@app.get("/set-webhook")
async def set_webhook():
    """Set Telegram webhook URL"""
    try:
        # Get your Render URL (you'll need to set this)
        webhook_url = os.getenv("WEBHOOK_URL", "https://your-render-app.onrender.com/webhook")
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "url": webhook_url,
                "allowed_updates": ["message"]
            }
            
            async with session.post(f"{bot.api_url}/setWebhook", json=payload) as response:
                result = await response.json()
                logger.info(f"Webhook set result: {result}")
                return result
    
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return {"error": str(e)}

@app.get("/delete-webhook")
async def delete_webhook():
    """Delete Telegram webhook"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{bot.api_url}/deleteWebhook") as response:
                result = await response.json()
                logger.info(f"Webhook deleted: {result}")
                return result
    
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "Svetlana Telegram Bot is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 