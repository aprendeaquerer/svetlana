# Svetlana API - Updated with error handling
# Updated with error handling for database operations
# Force redeploy - 2024
# Last updated: 2024-06-24 10:30 UTC
# 
# 🚀 DEPLOYMENT INFO:
# This is the BACKEND that deploys to RENDER
# Frontend deploys to VERCEL separately
# 
# When debugging:
# - Frontend issues → Check Vercel
# - Backend issues → Check Render (this service)
# - API errors → Check Render logs
# - 404 errors → Check Vercel
#
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from databases import Database
from chatgpt_wrapper import ChatGPT
from pydantic import BaseModel
import uuid
from passlib.context import CryptContext
import os
from typing import Dict, List
import re

# Try to import test questions, fallback to simple version if import fails
try:
    from test_questions import TEST_QUESTIONS, calculate_attachment_style, get_style_description
    print("Successfully imported test_questions module")
except ImportError as e:
    print(f"Warning: Could not import test_questions module: {e}")
    print("Using fallback test questions")
    
    # Fallback test questions (simplified version)
    TEST_QUESTIONS = {
        "es": [
            {
                "question": "Cuando estás en una relación, ¿cómo sueles reaccionar cuando tu pareja no responde a tus mensajes inmediatamente?",
                "options": [
                    {"text": "Me preocupo y pienso que algo está mal", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                    {"text": "Me enfado y me distancio", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                    {"text": "Entiendo que puede estar ocupada", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                    {"text": "Me siento confundido y no sé qué hacer", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
                ]
            }
        ]
    }
    
    def calculate_attachment_style(scores):
        max_score = max(scores.values())
        predominant_styles = [style for style, score in scores.items() if score == max_score]
        return predominant_styles[0] if predominant_styles else "secure"
    
    def get_style_description(style, language="es"):
        descriptions = {
            "es": {
                "secure": "Seguro: Te sientes cómodo con la intimidad y la independencia.",
                "anxious": "Ansioso: Buscas mucha cercanía y te preocupas por el rechazo.",
                "avoidant": "Evitativo: Prefieres mantener distancia emocional.",
                "disorganized": "Desorganizado: Tienes patrones contradictorios."
            }
        }
        return descriptions.get(language, descriptions["es"]).get(style, "")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("WARNING: Missing DATABASE_URL environment variable. Database operations will fail.")
    database = None
else:
    database = Database(DATABASE_URL)

# Initialize the main chatbot instance at the top-level scope
api_key = os.getenv('CHATGPT_API_KEY')
if not api_key:
    print("WARNING: Missing CHATGPT_API_KEY environment variable. Chatbot will not work.")
    chatbot = None
else:
    chatbot = ChatGPT(api_key=api_key)

# Keyword extraction function
def extract_keywords(message: str, language: str = "es") -> List[str]:
    """
    Extract relevant keywords from user message for attachment theory knowledge lookup.
    Returns English keywords for database lookup since database tags are in English.
    """
    # Convert to lowercase for matching
    message_lower = message.lower()
    
    # Language-specific attachment theory keywords with English equivalents for database lookup
    attachment_keywords = {
        "es": {
            'anxious': ['ansioso', 'ansiedad', 'preocupado', 'miedo', 'abandono', 'rechazo', 'inseguro', 'necesito', 'confirmación', 'confirmacion'],
            'avoidant': ['evitativo', 'evito', 'distancia', 'independiente', 'solo', 'espacio', 'alejado', 'frío', 'distante'],
            'secure': ['seguro', 'confianza', 'equilibrio', 'cómodo', 'tranquilo', 'estable', 'sano'],
            'disorganized': ['desorganizado', 'confundido', 'contradictorio', 'caos', 'inconsistente'],
            'relationship': ['relación', 'relaciones', 'pareja', 'amor', 'vínculo', 'conexión', 'intimidad', 'cercanía'],
            'communication': ['comunicación', 'hablar', 'expresar', 'decir', 'conversar'],
            'conflict': ['conflicto', 'pelea', 'discusión', 'problema', 'disputa'],
            'trust': ['confianza', 'confiar', 'seguro', 'seguridad'],
            'emotions': ['emoción', 'sentir', 'sentimiento', 'triste', 'feliz', 'enojado', 'frustrado']
        },
        "en": {
            'anxious': ['anxious', 'anxiety', 'worried', 'fear', 'abandonment', 'rejection', 'insecure', 'need', 'confirmation'],
            'avoidant': ['avoidant', 'avoid', 'distance', 'independent', 'alone', 'space', 'distant', 'cold', 'detached'],
            'secure': ['secure', 'trust', 'balance', 'comfortable', 'calm', 'stable', 'healthy'],
            'disorganized': ['disorganized', 'confused', 'contradictory', 'chaos', 'inconsistent'],
            'relationship': ['relationship', 'partner', 'love', 'bond', 'connection', 'intimacy', 'closeness'],
            'communication': ['communication', 'talk', 'express', 'say', 'converse'],
            'conflict': ['conflict', 'fight', 'argument', 'problem', 'dispute'],
            'trust': ['trust', 'trusting', 'secure', 'security'],
            'emotions': ['emotion', 'feel', 'feeling', 'sad', 'happy', 'angry', 'frustrated']
        },
        "ru": {
            'anxious': ['тревожный', 'тревога', 'беспокойный', 'страх', 'покинутость', 'отвержение', 'неуверенный', 'нужда', 'подтверждение'],
            'avoidant': ['избегающий', 'избегать', 'дистанция', 'независимый', 'один', 'пространство', 'отдаленный', 'холодный', 'отстраненный'],
            'secure': ['надежный', 'доверие', 'баланс', 'комфортный', 'спокойный', 'стабильный', 'здоровый'],
            'disorganized': ['дезорганизованный', 'запутанный', 'противоречивый', 'хаос', 'непоследовательный'],
            'relationship': ['отношения', 'партнер', 'любовь', 'связь', 'соединение', 'близость', 'интимность'],
            'communication': ['общение', 'говорить', 'выражать', 'сказать', 'беседовать'],
            'conflict': ['конфликт', 'ссора', 'спор', 'проблема', 'разногласие'],
            'trust': ['доверие', 'доверять', 'надежный', 'безопасность'],
            'emotions': ['эмоция', 'чувствовать', 'чувство', 'грустный', 'счастливый', 'злой', 'разочарованный']
        }
    }
    
    # Get keywords for the specified language
    lang_keywords = attachment_keywords.get(language, attachment_keywords["es"])
    
    # Extract English category names (for database lookup) based on found keywords
    found_categories = []
    
    for category, keywords in lang_keywords.items():
        for keyword in keywords:
            if keyword in message_lower:
                found_categories.append(category)  # Add the English category name
                break  # Only add each category once
    
    # Remove duplicates while preserving order
    unique_categories = []
    for category in found_categories:
        if category not in unique_categories:
            unique_categories.append(category)
    
    print(f"[DEBUG] Found categories for database lookup: {unique_categories}")
    return unique_categories[:5]  # Return top 5 English category names

async def get_relevant_knowledge(keywords: List[str], language: str = "es", user_id: str = None) -> str:
    """
    Query the appropriate eldric_knowledge table for relevant content based on keywords and language.
    Avoids repeating content that has already been used for this user.
    Returns a formatted string with relevant knowledge chunks.
    Mention the source of 1 knowledge in each response, name of book and name of chapter.
    """
    if not keywords:
        print("[DEBUG] No keywords provided, returning empty string")
        return ""
    
    print(f"[DEBUG] get_relevant_knowledge called with keywords: {keywords}, language: {language}, user_id: {user_id}")
    
    try:
        # Ensure database is connected
        if not database.is_connected:
            print("[DEBUG] Database not connected, attempting to connect...")
            await database.connect()
        
        # Determine which table to query based on language
        if language == "ru":
            table_name = "eldric_knowledge_ru"
        elif language == "en":
            table_name = "eldric_knowledge"
        else:  # Default to Spanish
            table_name = "eldric_knowledge_es"
        
        print(f"[DEBUG] Using table: {table_name}")
        
        # Get previously used content IDs for this user
        used_ids = used_knowledge.get(user_id, set()) if user_id else set()
        print(f"[DEBUG] Previously used IDs: {used_ids}")
        
        # Build query to find knowledge chunks that match any of the keywords
        # Using ILIKE for case-insensitive matching and excluding used content
        query = f"""
        SELECT id, content, tags 
        FROM {table_name} 
        WHERE """
        
        conditions = []
        values = {}
        
        for i, keyword in enumerate(keywords):
            conditions.append(f"tags ILIKE :tag_{i}")
            values[f"tag_{i}"] = f"%{keyword}%"
        
        query += " OR ".join(conditions)
        
        # Exclude previously used content if we have a user_id
        if user_id and used_ids:
            query += " AND id NOT IN ("
            for i, used_id in enumerate(used_ids):
                if i > 0:
                    query += ","
                query += f":used_id_{i}"
                values[f"used_id_{i}"] = used_id
            query += ")"
        
        query += " ORDER BY RANDOM() LIMIT 5"
        
        print(f"[DEBUG] Query: {query}")
        print(f"[DEBUG] Values: {values}")
        
        # Debug: Let's see what's actually in the table
        debug_query = f"SELECT id, content, tags FROM {table_name} LIMIT 3"
        debug_rows = await database.fetch_all(debug_query)
        print(f"[DEBUG] Sample data from {table_name}:")
        for i, row in enumerate(debug_rows):
            print(f"[DEBUG] Row {i}: id={row['id']}, tags='{row['tags']}', content='{row['content'][:100]}...'")
        
        # Execute query
        rows = await database.fetch_all(query, values=values)
        print(f"[DEBUG] Query returned {len(rows)} rows")
        
        if not rows:
            print("[DEBUG] No rows found, checking if we should reset used content...")
            # If no unused content found, reset used content for this user and try again
            if user_id and used_ids:
                print("[DEBUG] Resetting used content and trying again...")
                used_knowledge[user_id] = set()
                # Re-run the query without the exclusion
                query = f"""
                SELECT id, content, tags 
                FROM {table_name} 
                WHERE """
                query += " OR ".join(conditions)
                query += " ORDER BY RANDOM() LIMIT 5"
                rows = await database.fetch_all(query, values=values)
                print(f"[DEBUG] Second query returned {len(rows)} rows")
        
        if not rows:
            print("[DEBUG] Still no rows found, returning empty string")
            return ""
        
        # Track used content IDs
        if user_id:
            if user_id not in used_knowledge:
                used_knowledge[user_id] = set()
            for row in rows:
                used_knowledge[user_id].add(row['id'])
        
        # Format the knowledge chunks based on language
        if language == "ru":
            knowledge_text = "\n\nРелевантные знания для этой беседы:\n"
        elif language == "en":
            knowledge_text = "\n\nRelevant knowledge for this conversation:\n"
        else:  # Spanish
            knowledge_text = "\n\nConocimiento relevante para esta conversación:\n"
            
        for i, row in enumerate(rows, 1):
            knowledge_text += f"{i}. {row['content']}\n"
        
        print(f"[DEBUG] Final knowledge text length: {len(knowledge_text)}")
        return knowledge_text
        
    except Exception as e:
        print(f"[DEBUG] Error in get_relevant_knowledge: {e}")
        return ""

def inject_knowledge_into_prompt(base_prompt: str, knowledge: str) -> str:
    """
    Inject relevant knowledge into the system prompt while maintaining Eldric's personality.
    """
    if not knowledge:
        return base_prompt
    
    # Insert knowledge after the main personality description but before the specific instructions
    injection_point = base_prompt.find("Cuando el usuario dice 'saludo inicial'")
    
    if injection_point != -1:
        # Insert knowledge before the specific instructions
        enhanced_prompt = (
            base_prompt[:injection_point] + 
            knowledge + 
            "\n\n" +
            base_prompt[injection_point:]
        )
    else:
        # If we can't find the injection point, append at the end
        enhanced_prompt = base_prompt + "\n\n" + knowledge
    
    return enhanced_prompt

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://svetlana-frontend.vercel.app",
        "https://www.aprendeaquerer.com",
        "https://aprendeaquerer.com",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    user_id: str
    message: str
    language: str = "es"  # Default to Spanish

class User(BaseModel):
    user_id: str
    password: str

# Global chatbot instances for each user
user_chatbots = {}

# Track used knowledge content to avoid repetition
used_knowledge = {}  # user_id -> set of used content IDs

# Language-specific prompts for Eldric
eldric_prompts = {
    "es": (
        "Eres Eldric, un coach emocional cálido, empático, sabio y cercano. "
        "Eres experto en teoría del apego, psicología de las relaciones y acompañamiento emocional. "
        "Intenta mantener las respuestas un poco mas cortas, mas simples"
        "Al final de cada respuesta, pregunta algo en concatenacion con la respuesta, algo que te ayude a entender mejor al usuario"
        "Hablas en español neutro, sin tecnicismos innecesarios, usando un tono accesible pero profundo. "
        "Escuchas activamente, haces preguntas reflexivas y das orientación emocional basada en el estilo de apego de cada persona. "
        "Cuando el usuario dice 'saludo inicial', responde con una bienvenida estructurada: "
        "una breve presentación tuya, una explicación sencilla de los estilos de apego y una invitación clara a realizar un test. "
        "Utiliza saltos de línea dobles (\n\n) para separar los párrafos, y si haces preguntas con opciones, usa formato tipo:\n"
        "a) opción uno\nb) opción dos\nc) opción tres\nd) opción cuatro. "
        "No esperes más contexto: si el usuario escribe 'saludo inicial', tú simplemente inicias la experiencia sin pedir más. "
        "Después del test, recomiéndale registrarse para guardar su progreso y acceder a más recursos. "
        "Si el usuario no desea hacer el test, puedes acompañarlo igualmente desde sus emociones actuales."
    ),
    "en": (
        "You are Eldric, a warm, empathetic, wise, and close emotional coach. "
        "You are an expert in attachment theory, relationship psychology, and emotional accompaniment. "
        "Try to keep responses a bit shorter and simpler. "
        "You speak in neutral English, without unnecessary technical terms, using an accessible but deep tone. "
        "You listen actively, ask reflective questions, and provide emotional guidance based on each person's attachment style. "
        "When the user says 'initial greeting', respond with a structured welcome: "
        "a brief introduction of yourself, a simple explanation of attachment styles, and a clear invitation to take a test. "
        "Use double line breaks (\n\n) to separate paragraphs, and if you ask questions with options, use format like:\n"
        "a) option one\nb) option two\nc) option three\nd) option four. "
        "Don't wait for more context: if the user writes 'initial greeting', you simply start the experience without asking for more. "
        "After the test, recommend them to register to save their progress and access more resources. "
        "If the user doesn't want to take the test, you can accompany them from their current emotions."
    ),
    "ru": (
        "Ты Элдрик, теплый, эмпатичный, мудрый и близкий эмоциональный коуч. "
        "Ты эксперт в теории привязанности, психологии отношений и эмоциональном сопровождении. "
        "Старайся делать ответы немного короче и проще. "
        "Ты говоришь на нейтральном русском языке, без ненужных технических терминов, используя доступный, но глубокий тон. "
        "Ты активно слушаешь, задаешь рефлексивные вопросы и даешь эмоциональное руководство на основе стиля привязанности каждого человека. "
        "Когда пользователь говорит 'начальное приветствие', отвечай структурированным приветствием: "
        "краткое представление себя, простое объяснение стилей привязанности и четкое приглашение пройти тест. "
        "Используй двойные переносы строк (\n\n) для разделения абзацев, и если задаешь вопросы с вариантами, используй формат:\n"
        "а) вариант один\nб) вариант два\nв) вариант три\nг) вариант четыре. "
        "Не жди больше контекста: если пользователь пишет 'начальное приветствие', ты просто начинаешь опыт без просьбы о большем. "
        "После теста порекомендуй зарегистрироваться, чтобы сохранить прогресс и получить доступ к большему количеству ресурсов. "
        "Если пользователь не хочет проходить тест, ты можешь сопровождать его от его текущих эмоций."
    )
}

# Default to Spanish prompt
eldric_prompt = eldric_prompts["es"]

@app.on_event("startup")
async def startup():
    if database is not None:
        await database.connect()
        
        # Run migration to ensure test_state table has all required columns
        try:
            print("[DEBUG] Running database migration...")
            from add_migration import migrate_database
            migration_success = await migrate_database()
            if migration_success:
                print("[DEBUG] Database migration completed successfully")
            else:
                print("[DEBUG] Database migration failed, but continuing...")
        except Exception as e:
            print(f"[DEBUG] Migration error (continuing anyway): {e}")
        
        await database.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                role TEXT,
                content TEXT,
                language TEXT DEFAULT 'es',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await database.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                hashed_password TEXT
            )
        """)
        await database.execute("""
            CREATE TABLE IF NOT EXISTS test_state (
                user_id TEXT PRIMARY KEY,
                state TEXT,
                last_choice TEXT,
                q1 TEXT,
                q2 TEXT,
                q3 TEXT,
                q4 TEXT,
                q5 TEXT,
                language TEXT DEFAULT 'es'
            )
        """)
        
        # Create language-specific knowledge tables
        for lang in ["es", "ru"]:
            await database.execute(f"""
                CREATE TABLE IF NOT EXISTS eldric_knowledge_{lang} (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # Keep the original table for backward compatibility
        await database.execute("""
            CREATE TABLE IF NOT EXISTS eldric_knowledge (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                tags TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        print("WARNING: Database not available, skipping table creation")

@app.on_event("shutdown")
async def shutdown():
    if database is not None:
        await database.disconnect()

@app.get("/")
async def root():
    print("Health check endpoint called")
    return {"message": "Welcome to Svetlana API! API is working."}

@app.get("/status")
async def status():
    """Diagnostic endpoint to check system status"""
    status_info = {
        "api_working": True,
        "database_connected": database is not None,
        "chatbot_available": chatbot is not None,
        "api_key_set": bool(os.getenv('CHATGPT_API_KEY')),
        "database_url_set": bool(os.getenv("DATABASE_URL")),
        "environment_variables": {
            "CHATGPT_API_KEY": "SET" if os.getenv('CHATGPT_API_KEY') else "NOT SET",
            "DATABASE_URL": "SET" if os.getenv("DATABASE_URL") else "NOT SET"
        }
    }
    
    if database is not None:
        try:
            # Test database connection
            await database.execute("SELECT 1")
            status_info["database_working"] = True
        except Exception as e:
            status_info["database_working"] = False
            status_info["database_error"] = str(e)
    
    if chatbot is not None:
        try:
            # Test chatbot initialization
            chatbot.reset()
            status_info["chatbot_working"] = True
        except Exception as e:
            status_info["chatbot_working"] = False
            status_info["chatbot_error"] = str(e)
    
    return status_info

@app.post("/register")
async def register(user: User):
    if database is None:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    hashed_password = pwd_context.hash(user.password)
    query = "INSERT INTO users (user_id, hashed_password) VALUES (:user_id, :hashed_password)"
    await database.execute(query, values={"user_id": user.user_id, "hashed_password": hashed_password})
    return {"message": f"User {user.user_id} registered successfully!"}

@app.post("/login")
async def login(user: User):
    if database is None:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    query = "SELECT hashed_password FROM users WHERE user_id = :user_id"
    stored_user = await database.fetch_one(query, values={"user_id": user.user_id})
    if stored_user and pwd_context.verify(user.password, stored_user["hashed_password"]):
        return {"message": f"User {user.user_id} logged in successfully!"}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

@app.post("/message")
async def chat_endpoint(msg: Message):
    response = None  # Always initialize response
    try:
        print(f"[DEBUG] === CHAT ENDPOINT START ===")
        print(f"[DEBUG] Message object received: {msg}")
        
        user_id = msg.user_id
        message = msg.message.strip()
        
        print(f"[DEBUG] user_id: {user_id}")
        print(f"[DEBUG] message: '{message}'")
        print(f"[DEBUG] language: {msg.language}")

        # Get or initialize test state
        try:
            print(f"[DEBUG] Database check - database is None: {database is None}")
            if database is None:
                print("[DEBUG] Database is None, returning error")
                return {"response": "Lo siento, hay problemas de conexión con la base de datos. Por favor, intenta de nuevo en unos momentos."}
            
            print(f"[DEBUG] Attempting database query...")
            state_row = await database.fetch_one("SELECT state, last_choice, q1, q2, q3, q4, q5 FROM test_state WHERE user_id = :user_id", values={"user_id": user_id})
            state = state_row["state"] if state_row else None
            last_choice = state_row["last_choice"] if state_row else None
            q1 = state_row["q1"] if state_row else None
            q2 = state_row["q2"] if state_row else None
            q3 = state_row["q3"] if state_row else None
            q4 = state_row["q4"] if state_row else None
            q5 = state_row["q5"] if state_row else None
            
            print(f"[DEBUG] Database query successful")
            print(f"[DEBUG] Database query result: {state_row}")
            print(f"[DEBUG] Retrieved state: {state}")
            print(f"[DEBUG] Retrieved last_choice: {last_choice}")
            print(f"[DEBUG] Retrieved q1: {q1}")
            print(f"[DEBUG] Retrieved q2: {q2}")
            print(f"[DEBUG] Retrieved q3: {q3}")
            print(f"[DEBUG] Retrieved q4: {q4}")
            print(f"[DEBUG] Retrieved q5: {q5}")
        except Exception as db_error:
            print(f"[DEBUG] Database error in message endpoint: {db_error}")
            print(f"[DEBUG] Database error type: {type(db_error)}")
            import traceback
            print(f"[DEBUG] Database error traceback: {traceback.format_exc()}")
            # Return a simple response if database fails
            return {"response": "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta de nuevo en unos momentos."}

        async def set_state(new_state, choice=None, q1_val=None, q2_val=None, q3_val=None, q4_val=None, q5_val=None):
            try:
                print(f"[DEBUG] Setting state: {new_state}, choice={choice}, q1={q1_val}, q2={q2_val}, q3={q3_val}, q4={q4_val}, q5={q5_val}")
                if state_row:
                    result = await database.execute("UPDATE test_state SET state = :state, last_choice = :choice, q1 = :q1, q2 = :q2, q3 = :q3, q4 = :q4, q5 = :q5 WHERE user_id = :user_id", values={"state": new_state, "choice": choice, "q1": q1_val, "q2": q2_val, "q3": q3_val, "q4": q4_val, "q5": q5_val, "user_id": user_id})
                    print(f"[DEBUG] Updated existing state: {result}")
                else:
                    result = await database.execute("INSERT INTO test_state (user_id, state, last_choice, q1, q2, q3, q4, q5) VALUES (:user_id, :state, :choice, :q1, :q2, :q3, :q4, :q5)", values={"user_id": user_id, "state": new_state, "choice": choice, "q1": q1_val, "q2": q2_val, "q3": q3_val, "q4": q4_val, "q5": q5_val})
                    print(f"[DEBUG] Created new state: {result}")
                return result
            except Exception as e:
                print(f"Error setting state: {e}")
                return None

        print(f"[DEBUG] Chatbot check - chatbot is None: {chatbot is None}")
        # Check if chatbot is available
        if chatbot is None:
            print("[DEBUG] Chatbot is None, returning error")
            return {"response": "Lo siento, el servicio de chat no está disponible en este momento. Por favor, intenta de nuevo más tarde."}

        print(f"[DEBUG] Resetting chatbot...")
        chatbot.reset()
        # Use language-specific prompt
        current_prompt = eldric_prompts.get(msg.language, eldric_prompts["es"])
        chatbot.messages.append({"role": "system", "content": current_prompt})
        print(f"[DEBUG] Chatbot reset and prompt set successfully")

        # Always handle greeting triggers as a hard reset to greeting
        greeting_triggers = {
            "es": "saludo inicial",
            "en": "initial greeting", 
            "ru": "начальное приветствие"
        }
        print(f"[DEBUG] Checking greeting triggers...")
        print(f"[DEBUG] Message lower: '{message.lower()}'")
        print(f"[DEBUG] Expected trigger: '{greeting_triggers.get(msg.language, 'saludo inicial')}'")
        
        if message.lower() == greeting_triggers.get(msg.language, "saludo inicial"):
            print(f"[DEBUG] GREETING TRIGGER MATCHED!")
            print(f"[DEBUG] FORCE SHOW INITIAL GREETING (message == '{message}') - resetting state to 'greeting'")
            await set_state("greeting", None, None, None, None, None, None)
            if msg.language == "en":
                response = (
                    "<p><strong>Hello, I'm Eldric</strong>, your emotional coach. I'm here to help you understand yourself better through attachment theory.</p>"
                    "<p>In attachment psychology, we usually talk about four styles: <strong>secure, anxious, avoidant, and disorganized</strong>. Each one influences how you connect emotionally.</p>"
                    "<p>To start, would you like to take a small test that helps you discover your predominant style?</p>"
                    "<ul>"
                    "<li>a) Yes, I want to understand my way of loving.</li>"
                    "<li>b) I prefer to talk about how I feel now.</li>"
                    "<li>c) Tell me more about attachment.</li>"
                    "</ul>"
                )
            elif msg.language == "ru":
                response = (
                    "<p><strong>Привет, я Элдрик</strong>, твой эмоциональный коуч. Я здесь, чтобы помочь тебе лучше понять себя через теорию привязанности.</p>"
                    "<p>В психологии привязанности мы обычно говорим о четырех стилях: <strong>безопасный, тревожный, избегающий и дезорганизованный</strong>. Каждый влияет на то, как ты эмоционально связываешься.</p>"
                    "<p>Для начала, хочешь пройти небольшой тест, который поможет тебе открыть свой преобладающий стиль?</p>"
                    "<ul>"
                    "<li>а) Да, я хочу понять свой способ любить.</li>"
                    "<li>б) Я предпочитаю поговорить о том, как я чувствую себя сейчас.</li>"
                    "<li>в) Расскажи мне больше о привязанности.</li>"
                    "</ul>"
                )
            else:  # Spanish (default)
                response = (
                    "<p><strong>Hola, soy Eldric</strong>, tu coach emocional. Estoy aquí para acompañarte a entenderte mejor desde la teoría del apego.</p>"
                    "<p>En psicología del apego, solemos hablar de cuatro estilos: <strong>seguro, ansioso, evitativo y desorganizado</strong>. Cada uno influye en cómo te vinculas emocionalmente.</p>"
                    "<p>Para comenzar, ¿quieres hacer un pequeño test que te ayude a descubrir tu estilo predominante?</p>"
                    "<ul>"
                    "<li>a) Sí, quiero entender mi forma de querer.</li>"
                    "<li>b) Prefiero hablar de cómo me sientes ahora.</li>"
                    "<li>c) Cuentame mas sobre el apego.</li>"
                    "</ul>"
                )
            print(f"[DEBUG] Set initial greeting response (forced): {response[:100]}...")
            return {"response": response}
        # Always handle test triggers as a hard reset to test start (but not greeting triggers)
        test_triggers = ["quiero hacer el test", "hacer test", "start test", "quiero hacer el test", "quiero hacer test", "hacer el test"]
        greeting_triggers_list = list(greeting_triggers.values())
        if message.lower() in test_triggers and message.lower() not in greeting_triggers_list:
            print("[DEBUG] FORCE START TEST (message in test_triggers)")
            await set_state("q1", None, None, None, None, None, None)
            questions = TEST_QUESTIONS.get(msg.language, TEST_QUESTIONS["es"])
            question = questions[0]
            
            if msg.language == "en":
                response = f"<p><strong>Question 1 of 5:</strong> {question['question']}</p><ul>"
            elif msg.language == "ru":
                response = f"<p><strong>Вопрос 1 из 5:</strong> {question['question']}</p><ul>"
            else:  # Spanish
                response = f"<p><strong>Pregunta 1 de 5:</strong> {question['question']}</p><ul>"
            
            for i, option in enumerate(question['options']):
                response += f"<li>{chr(97+i)}) {option['text']}</li>"
            response += "</ul>"
            
            print(f"[DEBUG] Set test start response (forced): {response[:100]}...")
            return {"response": response}
        # Handle greeting choices (A, B, C)
        elif state == "greeting" and message.upper() in ["A", "B", "C"]:
            print(f"[DEBUG] ENTERED: greeting state with choice {message.upper()}")
            print(f"[DEBUG] In greeting state, user chose: {message.upper()}")
            if message.upper() == "A":
                # Start test
                await set_state("q1", None, None, None, None, None, None)
                questions = TEST_QUESTIONS.get(msg.language, TEST_QUESTIONS["es"])
                question = questions[0]
                
                if msg.language == "en":
                    response = f"<p><strong>Question 1 of 5:</strong> {question['question']}</p><ul>"
                elif msg.language == "ru":
                    response = f"<p><strong>Вопрос 1 из 5:</strong> {question['question']}</p><ul>"
                else:  # Spanish
                    response = f"<p><strong>Pregunta 1 de 5:</strong> {question['question']}</p><ul>"
                
                for i, option in enumerate(question['options']):
                    response += f"<li>{chr(97+i)}) {option['text']}</li>"
                response += "</ul>"
            elif message.upper() == "B":
                # Normal conversation about feelings
                await set_state("conversation", None, None, None, None, None, None)
                if msg.language == "en":
                    response = "<p>I understand, sometimes we need to talk about what we feel before taking tests. How do you feel today? Is there something specific you'd like to share or explore together?</p>"
                elif msg.language == "ru":
                    response = "<p>Понимаю, иногда нам нужно поговорить о том, что мы чувствуем, прежде чем проходить тесты. Как ты себя чувствуешь сегодня? Есть ли что-то конкретное, что ты хотел бы поделиться или исследовать вместе?</p>"
                else:  # Spanish
                    response = "<p>Entiendo, a veces necesitamos hablar de lo que sentimos antes de hacer tests. ¿Cómo te sientes hoy? ¿Hay algo específico que te gustaría compartir o explorar juntos?</p>"
            elif message.upper() == "C":
                # Normal conversation about attachment
                await set_state("conversation", None, None, None, None, None, None)
                if msg.language == "en":
                    response = (
                        "<p>Of course! Attachment is how we learned to relate since we were babies. Our first bonds with our caregivers taught us patterns that we repeat in our adult relationships.</p>"
                        "<p>Attachment styles are:</p>"
                        "<ul>"
                        "<li><strong>Secure:</strong> You feel comfortable with intimacy and independence</li>"
                        "<li><strong>Anxious:</strong> You seek a lot of closeness and worry about rejection</li>"
                        "<li><strong>Avoidant:</strong> You prefer to maintain emotional distance</li>"
                        "<li><strong>Disorganized:</strong> You have contradictory patterns</li>"
                        "</ul>"
                        "<p>Would you like to take the test now or would you prefer to talk about something specific?</p>"
                    )
                elif msg.language == "ru":
                    response = (
                        "<p>Конечно! Привязанность - это то, как мы научились относиться друг к другу с тех пор, как были младенцами. Наши первые связи с опекунами научили нас паттернам, которые мы повторяем в наших взрослых отношениях.</p>"
                        "<p>Стили привязанности:</p>"
                        "<ul>"
                        "<li><strong>Безопасный:</strong> Ты чувствуешь себя комфортно с близостью и независимостью</li>"
                        "<li><strong>Тревожный:</strong> Ты ищешь много близости и беспокоишься об отвержении</li>"
                        "<li><strong>Избегающий:</strong> Ты предпочитаешь поддерживать эмоциональную дистанцию</li>"
                        "<li><strong>Дезорганизованный:</strong> У тебя противоречивые паттерны</li>"
                        "</ul>"
                        "<p>Хочешь пройти тест сейчас или предпочитаешь поговорить о чем-то конкретном?</p>"
                    )
                else:  # Spanish
                    response = (
                        "<p>¡Por supuesto! El apego es cómo aprendimos a relacionarnos desde que éramos bebés. Nuestros primeros vínculos con nuestros cuidadores nos enseñaron patrones que repetimos en nuestras relaciones adultas.</p>"
                        "<p>Los estilos de apego son:</p>"
                        "<ul>"
                        "<li><strong>Seguro:</strong> Te sientes cómodo con la intimidad y la independencia</li>"
                        "<li><strong>Ansioso:</strong> Buscas mucha cercanía y te preocupas por el rechazo</li>"
                        "<li><strong>Evitativo:</strong> Prefieres mantener distancia emocional</li>"
                        "<li><strong>Desorganizado:</strong> Tienes patrones contradictorios</li>"
                        "</ul>"
                        "<p>¿Te gustaría hacer el test ahora o prefieres que hablemos de algo específico?</p>"
                    )
        # Handle test questions (q1, q2, q3, q4, q5)
        elif state in ["q1", "q2", "q3", "q4", "q5"] and message.upper() in ["A", "B", "C", "D"]:
            print(f"[DEBUG] ENTERED: test question state {state} with choice {message.upper()}")
            
            questions = TEST_QUESTIONS.get(msg.language, TEST_QUESTIONS["es"])
            current_question_index = int(state[1]) - 1  # q1 -> 0, q2 -> 1, etc.
            current_question = questions[current_question_index]
            
            # Get the selected option and its scores
            option_index = ord(message.upper()) - ord('A')  # A->0, B->1, C->2, D->3
            selected_option = current_question['options'][option_index]
            
            # Store the answer
            if state == "q1":
                await set_state("q2", message.upper(), selected_option['text'], q2, q3, q4, q5)
            elif state == "q2":
                await set_state("q3", message.upper(), q1, selected_option['text'], q3, q4, q5)
            elif state == "q3":
                await set_state("q4", message.upper(), q1, q2, selected_option['text'], q4, q5)
            elif state == "q4":
                await set_state("q5", message.upper(), q1, q2, q3, selected_option['text'], q5)
            elif state == "q5":
                # This is the last question, calculate results
                await set_state("results", message.upper(), q1, q2, q3, q4, selected_option['text'])
                
                # Calculate scores
                scores = {"anxious": 0, "avoidant": 0, "secure": 0, "disorganized": 0}
                
                # Get all answers
                answers = [q1, q2, q3, q4, selected_option['text']]
                
                for i, answer in enumerate(answers):
                    if answer:
                        # Find which option was selected for each question
                        question_options = questions[i]['options']
                        for j, option in enumerate(question_options):
                            if option['text'] == answer:
                                # Add scores for this answer
                                for style, score in option['scores'].items():
                                    scores[style] += score
                                break
                
                # Calculate predominant style
                predominant_style = calculate_attachment_style(scores)
                style_description = get_style_description(predominant_style, msg.language)
                
                if msg.language == "en":
                    response = (
                        f"<p><strong>Test Results</strong></p>"
                        f"<p>Based on your answers, your predominant attachment style is: <strong>{predominant_style.title()}</strong></p>"
                        f"<p>{style_description}</p>"
                        f"<p>Your scores:</p>"
                        f"<ul>"
                        f"<li>Secure: {scores['secure']}</li>"
                        f"<li>Anxious: {scores['anxious']}</li>"
                        f"<li>Avoidant: {scores['avoidant']}</li>"
                        f"<li>Disorganized: {scores['disorganized']}</li>"
                        f"</ul>"
                        f"<p>Would you like to explore this further or talk about how this affects your relationships?</p>"
                    )
                elif msg.language == "ru":
                    response = (
                        f"<p><strong>Результаты теста</strong></p>"
                        f"<p>Основываясь на ваших ответах, ваш преобладающий стиль привязанности: <strong>{predominant_style.title()}</strong></p>"
                        f"<p>{style_description}</p>"
                        f"<p>Ваши баллы:</p>"
                        f"<ul>"
                        f"<li>Безопасный: {scores['secure']}</li>"
                        f"<li>Тревожный: {scores['anxious']}</li>"
                        f"<li>Избегающий: {scores['avoidant']}</li>"
                        f"<li>Дезорганизованный: {scores['disorganized']}</li>"
                        f"</ul>"
                        f"<p>Хотели бы вы изучить это дальше или поговорить о том, как это влияет на ваши отношения?</p>"
                    )
                else:  # Spanish
                    response = (
                        f"<p><strong>Resultados del test</strong></p>"
                        f"<p>Basándome en tus respuestas, tu estilo de apego predominante es: <strong>{predominant_style.title()}</strong></p>"
                        f"<p>{style_description}</p>"
                        f"<p>Tus puntuaciones:</p>"
                        f"<ul>"
                        f"<li>Seguro: {scores['secure']}</li>"
                        f"<li>Ansioso: {scores['anxious']}</li>"
                        f"<li>Evitativo: {scores['avoidant']}</li>"
                        f"<li>Desorganizado: {scores['disorganized']}</li>"
                        f"</ul>"
                        f"<p>¿Te gustaría explorar esto más a fondo o hablar de cómo esto afecta tus relaciones?</p>"
                    )
                
                # Reset to conversation state after showing results, but keep the answers
                await set_state("post_test", None, q1, q2, q3, q4, selected_option['text'])
                return {"response": response}
            
            # Show next question
            next_question_index = current_question_index + 1
            if next_question_index < len(questions):
                next_question = questions[next_question_index]
                
                if msg.language == "en":
                    response = f"<p><strong>Question {next_question_index + 1} of 5:</strong> {next_question['question']}</p><ul>"
                elif msg.language == "ru":
                    response = f"<p><strong>Вопрос {next_question_index + 1} из 5:</strong> {next_question['question']}</p><ul>"
                else:  # Spanish
                    response = f"<p><strong>Pregunta {next_question_index + 1} de 5:</strong> {next_question['question']}</p><ul>"
                
                for i, option in enumerate(next_question['options']):
                    response += f"<li>{chr(97+i)}) {option['text']}</li>"
                response += "</ul>"
            else:
                # This shouldn't happen, but just in case
                response = "Error: No more questions available."
        # Handle post-test conversation (user just finished test)
        elif state == "post_test":
            print(f"[DEBUG] ENTERED: post_test state - user just finished test")
            print(f"[DEBUG] User message: '{message}'")
            
            # Get the user's test results to provide personalized responses
            scores = {"anxious": 0, "avoidant": 0, "secure": 0, "disorganized": 0}
            answers = [q1, q2, q3, q4, q5]
            
            questions = TEST_QUESTIONS.get(msg.language, TEST_QUESTIONS["es"])
            for i, answer in enumerate(answers):
                if answer and i < len(questions):
                    question_options = questions[i]['options']
                    for option in question_options:
                        if option['text'] == answer:
                            for style, score in option['scores'].items():
                                scores[style] += score
                            break
            
            predominant_style = calculate_attachment_style(scores)
            style_description = get_style_description(predominant_style, msg.language)
            
            # Create a personalized prompt for post-test conversation
            if msg.language == "en":
                post_test_prompt = (
                    f"You are Eldric, an emotional coach. The user just completed an attachment style test. "
                    f"Their predominant style is: {predominant_style.title()}. "
                    f"Description: {style_description} "
                    f"Their scores were: Secure {scores['secure']}, Anxious {scores['anxious']}, "
                    f"Avoidant {scores['avoidant']}, Disorganized {scores['disorganized']}. "
                    f"Answer their questions about their style, relationships, and provide personalized guidance. "
                    f"DO NOT offer the test again - they just completed it. Focus on explaining their results and helping them understand their patterns."
                )
            elif msg.language == "ru":
                post_test_prompt = (
                    f"Ты Элдрик, эмоциональный коуч. Пользователь только что завершил тест на стиль привязанности. "
                    f"Их преобладающий стиль: {predominant_style.title()}. "
                    f"Описание: {style_description} "
                    f"Их баллы: Безопасный {scores['secure']}, Тревожный {scores['anxious']}, "
                    f"Избегающий {scores['avoidant']}, Дезорганизованный {scores['disorganized']}. "
                    f"Отвечай на их вопросы о стиле, отношениях и давай персонализированные советы. "
                    f"НЕ предлагай тест снова - они только что его завершили. Сосредоточься на объяснении результатов и помощи в понимании их паттернов."
                )
            else:  # Spanish
                post_test_prompt = (
                    f"Eres Eldric, un coach emocional. El usuario acaba de completar un test de estilo de apego. "
                    f"Su estilo predominante es: {predominant_style.title()}. "
                    f"Descripción: {style_description} "
                    f"Sus puntuaciones fueron: Seguro {scores['secure']}, Ansioso {scores['anxious']}, "
                    f"Evitativo {scores['avoidant']}, Desorganizado {scores['disorganized']}. "
                    f"Responde sus preguntas sobre su estilo, relaciones y proporciona orientación personalizada. "
                    f"NO ofrezcas el test de nuevo - acaba de completarlo. Céntrate en explicar sus resultados y ayudarle a entender sus patrones."
                )
            
            # Reset chatbot with personalized prompt
            chatbot.reset()
            chatbot.messages.append({"role": "system", "content": post_test_prompt})
            
            response = await run_in_threadpool(chatbot.chat, message)
            
            # After a few exchanges, transition to normal conversation
            # For now, stay in post_test state to maintain context
        # Handle normal conversation with knowledge injection
        elif state == "conversation" or state is None:
            print(f"[DEBUG] ENTERED: normal conversation (state == 'conversation' or state is None)")
            print(f"[DEBUG] This should NOT happen for first message with 'saludo inicial'")
            # Extract keywords and get relevant knowledge for non-test messages
            keywords = extract_keywords(message, msg.language)
            print(f"[DEBUG] Message: '{message}'")
            print(f"[DEBUG] Language: {msg.language}")
            print(f"[DEBUG] Extracted keywords: {keywords}")
            
            relevant_knowledge = await get_relevant_knowledge(keywords, msg.language, msg.user_id)
            print(f"[DEBUG] Knowledge found: {len(relevant_knowledge)} characters")
            print(f"[DEBUG] Knowledge content: {relevant_knowledge}")
            
            # Inject knowledge into the prompt
            enhanced_prompt = inject_knowledge_into_prompt(current_prompt, relevant_knowledge)
            print(f"[DEBUG] Enhanced prompt length: {len(enhanced_prompt)}")
            print(f"[DEBUG] Enhanced prompt preview: {enhanced_prompt[:500]}...")
            
            # Reset chatbot and set enhanced prompt
            chatbot.reset()
            chatbot.messages.append({"role": "system", "content": enhanced_prompt})
            
            response = await run_in_threadpool(chatbot.chat, message)

        # Fallback for greeting state: prompt user to choose A, B, or C
        elif state == "greeting":
            print(f"[DEBUG] ENTERED: fallback greeting state (user didn't choose A, B, or C)")
            print(f"[DEBUG] In greeting state, user sent: {message}")
            if msg.language == "en":
                response = "Please choose one of the options: A, B, or C."
            elif msg.language == "ru":
                response = "Пожалуйста, выбери один из вариантов: А, Б или В."
            else:  # Spanish
                response = "Por favor, elige una de las opciones: A, B o C."
        
        # Fallback for test states: prompt user to choose A, B, C, or D
        elif state in ["q1", "q2", "q3", "q4", "q5"]:
            print(f"[DEBUG] ENTERED: fallback test state {state} (user didn't choose A, B, C, or D)")
            print(f"[DEBUG] In test state {state}, user sent: {message}")
            if msg.language == "en":
                response = "Please choose one of the options: A, B, C, or D."
            elif msg.language == "ru":
                response = "Пожалуйста, выбери один из вариантов: А, Б, В или Г."
            else:  # Spanish
                response = "Por favor, elige una de las opciones: A, B, C o D."

        if msg.user_id != "invitado":
            conv_id_user = str(uuid.uuid4())
            conv_id_bot = str(uuid.uuid4())
            await database.execute(
                "INSERT INTO conversations(id, user_id, role, content) VALUES (:id, :user_id, :role, :content)",
                {"id": conv_id_user, "user_id": msg.user_id, "role": "user", "content": msg.message}
            )
            await database.execute(
                "INSERT INTO conversations(id, user_id, role, content) VALUES (:id, :user_id, :role, :content)",
                {"id": conv_id_bot, "user_id": msg.user_id, "role": "assistant", "content": response}
            )

        print(f"[DEBUG] user_id={msg.user_id} message={msg.message} state={state}")
        print(f"[DEBUG] State details: last_choice={last_choice}, q1={q1}, q2={q2}, q3={q3}, q4={q4}, q5={q5}")
        print(f"[DEBUG] Response length: {len(response) if response else 0}")
        print(f"[DEBUG] Current state: {state}, Message: '{message}', Response preview: {response[:100] if response else 'None'}...")

        if response is None:
            response = "Lo siento, ha ocurrido un error inesperado. Por favor, intenta de nuevo o formula tu pregunta de otra manera."
        return {"response": response}
    except Exception as e:
        print(f"[DEBUG] Exception in chat_endpoint: {e}")
        return {"response": "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta de nuevo en unos momentos."}
