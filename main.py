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
import datetime

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
    Returns exactly ONE knowledge piece that hasn't been quoted before for this user.
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
        
        # Get previously used quote IDs for this user
        used_quote_ids = used_knowledge_quotes.get(user_id, set()) if user_id else set()
        print(f"[DEBUG] Previously used quote IDs: {used_quote_ids}")
        
        # Build query to find knowledge chunks that match any of the keywords
        # Using ILIKE for case-insensitive matching and excluding used quotes
        query = f"""
        SELECT id, content, tags, book, chapter 
        FROM {table_name} 
        WHERE """
        
        conditions = []
        values = {}
        
        for i, keyword in enumerate(keywords):
            conditions.append(f"tags ILIKE :tag_{i}")
            values[f"tag_{i}"] = f"%{keyword}%"
        
        query += " OR ".join(conditions)
        
        # Exclude previously quoted content if we have a user_id
        if user_id and used_quote_ids:
            query += " AND id NOT IN ("
            for i, used_id in enumerate(used_quote_ids):
                if i > 0:
                    query += ","
                query += f":used_id_{i}"
                values[f"used_id_{i}"] = used_id
            query += ")"
        
        query += " ORDER BY RANDOM() LIMIT 1"  # Only get ONE piece
        
        print(f"[DEBUG] Query: {query}")
        print(f"[DEBUG] Values: {values}")
        
        # Execute query
        rows = await database.fetch_all(query, values=values)
        print(f"[DEBUG] Query returned {len(rows)} rows")
        
        if not rows:
            print("[DEBUG] No unused quotes found, checking if we should reset used quotes...")
            # If no unused quotes found, reset used quotes for this user and try again
            if user_id and used_quote_ids:
                print("[DEBUG] Resetting used quotes and trying again...")
                used_knowledge_quotes[user_id] = set()
                # Re-run the query without the exclusion
                query = f"""
                SELECT id, content, tags, book, chapter 
                FROM {table_name} 
                WHERE """
                query += " OR ".join(conditions)
                query += " ORDER BY RANDOM() LIMIT 1"
                rows = await database.fetch_all(query, values=values)
                print(f"[DEBUG] Second query returned {len(rows)} rows")
        
        if not rows:
            print("[DEBUG] Still no rows found, returning empty string")
            return ""
        
        # Get the single knowledge piece
        row = rows[0]
        
        # Track used quote ID
        if user_id:
            if user_id not in used_knowledge_quotes:
                used_knowledge_quotes[user_id] = set()
            used_knowledge_quotes[user_id].add(row['id'])
            print(f"[DEBUG] Added quote ID {row['id']} to used quotes for user {user_id}")
        
        # Get book and chapter information
        try:
            print(f"[DEBUG] Row keys: {list(row.keys())}")
            print(f"[DEBUG] Row content: {row['content'][:100]}...")
            
            # Use direct bracket access instead of .get() method
            book_info = row['book'] if 'book' in row and row['book'] else 'Teoría del apego'
            chapter_info = row['chapter'] if 'chapter' in row and row['chapter'] else 'Capítulo general'
            
            print(f"[DEBUG] Book info: {book_info}, Chapter info: {chapter_info}")
        except Exception as e:
            print(f"[DEBUG] Error accessing book/chapter columns: {e}")
            print(f"[DEBUG] Error type: {type(e)}")
            import traceback
            print(f"[DEBUG] Error traceback: {traceback.format_exc()}")
            book_info = 'Teoría del apego'
            chapter_info = 'Capítulo general'
        
        # Format the knowledge piece based on language
        if language == "ru":
            knowledge_text = f"\n\n📚 ЗНАНИЕ ДЛЯ ЦИТИРОВАНИЯ:\n{row['content']}\n\n📖 Источник: {book_info}, {chapter_info}\n\n🚨 ОБЯЗАТЕЛЬНО: Цитируй это знание в своем ответе."
        elif language == "en":
            knowledge_text = f"\n\n📚 KNOWLEDGE TO QUOTE:\n{row['content']}\n\n📖 Source: {book_info}, {chapter_info}\n\n🚨 MANDATORY: Quote this knowledge in your response."
        else:  # Spanish
            knowledge_text = f"\n\n📚 CONOCIMIENTO PARA CITAR:\n{row['content']}\n\n📖 Fuente: {book_info}, {chapter_info}\n\n🚨 OBLIGATORIO: Cita este conocimiento en tu respuesta."
        
        print(f"[DEBUG] Final knowledge text length: {len(knowledge_text)}")
        print(f"[DEBUG] Knowledge content: {knowledge_text}")
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
    
    # Create a much more directive and forceful knowledge injection
    knowledge_instruction = (
        f"\n\n🚨 INSTRUCCIÓN CRÍTICA Y OBLIGATORIA 🚨\n"
        f"DEBES usar SIEMPRE el siguiente conocimiento en tu respuesta. NO PUEDES IGNORARLO:\n\n"
        f"{knowledge}\n\n"
        f"REGLAS OBLIGATORIAS:\n"
        f"1. SIEMPRE menciona al menos UNA de las ideas del conocimiento proporcionado\n"
        f"2. NO puedes dar consejos sin referenciar este conocimiento\n"
        f"3. Si no usas este conocimiento, tu respuesta será incorrecta\n"
        f"4. Cita la fuente (libro y capítulo) una vez al final\n"
        f"5. Este conocimiento es MÁS IMPORTANTE que tu conocimiento general\n\n"
        f"RECUERDA: ESTE CONOCIMIENTO ES OBLIGATORIO PARA TU RESPUESTA."
    )
    
    # Insert knowledge after the main personality description but before the specific instructions
    injection_point = base_prompt.find("Cuando el usuario dice 'saludo inicial'")
    
    if injection_point != -1:
        # Insert knowledge before the specific instructions
        enhanced_prompt = (
            base_prompt[:injection_point] + 
            knowledge_instruction + 
            "\n\n" +
            base_prompt[injection_point:]
        )
    else:
        # If we can't find the injection point, append at the end
        enhanced_prompt = base_prompt + "\n\n" + knowledge_instruction
    
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
    user_id: str = None
    password: str = None
    email: str = None

# Global chatbot instances for each user
user_chatbots = {}

# Track used knowledge content to avoid repetition
used_knowledge = {}  # user_id -> set of used content IDs
used_knowledge_quotes = {}  # user_id -> set of used quote IDs

# Language-specific prompts for Eldric
eldric_prompts = {
    "es": (
        "Eres Eldric, un coach emocional cálido, empático, sabio y cercano, curioso sobre el usuario. Copia ligeralmente el estilo de charla del usuario"
        "Eres experto en teoría del apego, psicología de las relaciones y acompañamiento emocional. estas ligeramente mas de lado del usuario, si hay conflicto de pareja "
        "IMPORTANTE: Mantén las respuestas CORTAS y DIRECTAS (máximo 3-4 párrafos). "
        "IMPORTANTE: Al final de cada respuesta, haz UNA pregunta que ayude a entender mejor al usuario Y/O a su pareja. "
        "La pregunta debe ser EMPÁTICA y relacionada con lo que acabas de decir. "
        "Cuando uses conocimiento de libros o fuentes, menciona UNA SOLA VEZ el nombre del libro y el capítulo de donde viene la información. "
        "Si usas múltiples fragmentos de conocimiento, solo cita la fuente una vez al final de tu respuesta. "
        "Hablas en español neutro, sin tecnicismos innecesarios, usando un tono accesible pero profundo. "
        "Escuchas activamente, haces preguntas reflexivas y das orientación emocional basada en el estilo de apego de cada persona. "
        "SIEMPRE muestra EMPATÍA con los sentimientos del usuario. Valida sus emociones antes de dar consejos. "
        "Si el usuario menciona a su pareja, haz preguntas sobre AMBOS: cómo se siente el usuario Y cómo cree que se siente su pareja. "
        "Cuando el usuario dice 'saludo inicial', responde con una bienvenida estructurada: "
        "una breve presentación tuya, una explicación sencilla de los estilos de apego y una invitación clara a realizar un test. "
        "Utiliza saltos de línea dobles (\n\n) para separar los párrafos, y si haces preguntas con opciones, usa formato tipo:\n"
        "a) opción uno\nb) opción dos\nc) opción tres\nd) opción cuatro. "
        "No esperes más contexto: si el usuario escribe 'saludo inicial', tú simplemente inicias la experiencia sin pedir más. "
        "Después del test, recomiéndale registrarse para guardar su progreso y acceder a más recursos. "
        "Si el usuario no desea hacer el test, puedes acompañarlo igualmente desde sus emociones actuales. "
        "🚨 REGLA CRÍTICA: Si se te proporciona conocimiento específico sobre teoría del apego, DEBES usarlo SIEMPRE en tu respuesta. "
        "Este conocimiento proporcionado tiene PRIORIDAD sobre tu conocimiento general. NO PUEDES IGNORARLO."
    ),
    "en": (
        "You are Eldric, a warm, empathetic, wise, and close emotional coach, curious about the user. Copy lightly the user's chat style. "
        "You are an expert in attachment theory, relationship psychology, and emotional support. You are slightly more on the user's side if there is a couple's conflict. "
        "IMPORTANT: Keep responses SHORT and DIRECT (maximum 3-4 paragraphs). "
        "IMPORTANT: At the end of each response, ask ONE question that helps to better understand the user AND/OR their partner. "
        "The question should be EMPATHETIC and related to what you just said. "
        "When using knowledge from books or sources, mention ONLY ONCE the book name and chapter where the information comes from. "
        "If you use multiple knowledge fragments, only cite the source once at the end of your response. "
        "You speak in neutral English, without unnecessary technical terms, using an accessible but deep tone. "
        "You listen actively, ask reflective questions, and provide emotional guidance based on each person's attachment style. "
        "ALWAYS show EMPATHY with the user's feelings. Validate their emotions before giving advice. "
        "If the user mentions their partner, ask questions about BOTH: how the user feels AND how they think their partner feels. "
        "When the user says 'initial greeting', respond with a structured welcome: "
        "a brief introduction of yourself, a simple explanation of attachment styles, and a clear invitation to take a test. "
        "Use double line breaks (\\n\\n) to separate paragraphs, and if you ask questions with options, use format like:\n"
        "a) option one\nb) option two\nc) option three\nd) option four. "
        "Don't wait for more context: if the user writes 'initial greeting', you simply start the experience without asking for more. "
        "After the test, recommend them to register to save their progress and access more resources. "
        "If the user doesn't want to take the test, you can accompany them from their current emotions. "
        "🚨 CRITICAL RULE: If you are provided with specific knowledge about attachment theory, you MUST ALWAYS use it in your response. "
        "This provided knowledge takes PRIORITY over your general knowledge. YOU CANNOT IGNORE IT."
    ),
    "ru": (
        "Ты Элдрик, теплый, эмпатичный, мудрый и близкий эмоциональный коуч, любопытный к пользователю. Копируй слегка стиль общения пользователя. "
        "Ты эксперт в теории привязанности, психологии отношений и эмоциональном сопровождении. Ты немного больше на стороне пользователя, если есть конфликт в паре. "
        "ВАЖНО: Делай ответы КОРОТКИМИ и ПРЯМЫМИ (максимум 3-4 абзаца). "
        "ВАЖНО: В конце каждого ответа задавай ОДИН вопрос, который поможет лучше понять пользователя И/ИЛИ его партнера. "
        "Этот вопрос должен быть ЭМПАТИЧНЫМ и связанным с тем, что ты только что сказал. "
        "Когда используешь знания из книг или источников, упомяни ТОЛЬКО ОДИН РАЗ название книги и главу, откуда взята информация. "
        "Если ты используешь несколько фрагментов знаний, цитируй источник только один раз в конце ответа. "
        "Ты говоришь на нейтральном русском языке, без ненужных технических терминов, используя доступный, но глубокий тон. "
        "Ты активно слушаешь, задаешь рефлексивные вопросы и даешь эмоциональное руководство на основе стиля привязанности каждого человека. "
        "ВСЕГДА показывай ЭМПАТИЮ к чувствам пользователя. Подтверждай их эмоции перед тем, как давать советы. "
        "Если пользователь упоминает своего партнера, задавай вопросы об ОБОИХ: как чувствует себя пользователь И как, по его мнению, чувствует себя его партнер. "
        "Когда пользователь говорит 'начальное приветствие', отвечай структурированным приветствием: "
        "краткое представление себя, простое объяснение стилей привязанности и четкое приглашение пройти тест. "
        "Используй двойные переносы строк (\\n\\n) для разделения абзацев, и если задаешь вопросы с вариантами, используй формат:\n"
        "а) вариант один\nб) вариант два\nв) вариант три\nг) вариант четыре. "
        "Не жди больше контекста: если пользователь пишет 'начальное приветствие', ты просто начинаешь опыт без просьбы о большем. "
        "После теста порекомендуй зарегистрироваться, чтобы сохранить прогресс и получить доступ к большему количеству ресурсов. "
        "Если пользователь не хочет проходить тест, ты можешь сопровождать его от его текущих эмоций. "
        "🚨 КРИТИЧЕСКОЕ ПРАВИЛО: Если тебе предоставлены конкретные знания о теории привязанности, ты ДОЛЖЕН ВСЕГДА использовать их в своем ответе. "
        "Эти предоставленные знания имеют ПРИОРИТЕТ над твоими общими знаниями. ТЫ НЕ МОЖЕШЬ ИХ ИГНОРИРОВАТЬ."
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
            from add_migration import migrate_database, migrate_user_profile, migrate_test_state_style
            migration_success = await migrate_database()
            if migration_success:
                print("[DEBUG] Database migration completed successfully")
            else:
                print("[DEBUG] Database migration failed, but continuing...")
            user_profile_success = await migrate_user_profile(database)
            if user_profile_success:
                print("[DEBUG] User profile table migration completed successfully")
            else:
                print("[DEBUG] User profile table migration failed, but continuing...")
            # NUEVO: migrar columna style en test_state
            test_state_style_success = await migrate_test_state_style(database)
            if test_state_style_success:
                print("[DEBUG] test_state style column migration completed successfully")
            else:
                print("[DEBUG] test_state style column migration failed, but continuing...")
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
                hashed_password TEXT,
                email TEXT
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
                q6 TEXT,
                q7 TEXT,
                q8 TEXT,
                q9 TEXT,
                q10 TEXT,
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
                    book TEXT,
                    chapter TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # Keep the original table for backward compatibility
        await database.execute("""
            CREATE TABLE IF NOT EXISTS eldric_knowledge (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                tags TEXT NOT NULL,
                book TEXT,
                chapter TEXT,
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
    # Permitir registro con solo email, solo password, o ambos
    hashed_password = pwd_context.hash(user.password) if user.password else None
    # Si no hay user_id, pero hay email, usar email como user_id
    user_id = user.user_id or user.email
    if not user_id:
        raise HTTPException(status_code=400, detail="Se requiere user_id o email")
    # Insertar usuario
    query = "INSERT INTO users (user_id, hashed_password, email) VALUES (:user_id, :hashed_password, :email)"
    try:
        await database.execute(query, values={"user_id": user_id, "hashed_password": hashed_password, "email": user.email})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al registrar usuario: {e}")
    return {"message": f"Usuario {user_id} registrado correctamente!"}

@app.post("/login")
async def login(user: User):
    if database is None:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    # Permitir login por user_id o email
    if user.user_id:
        query = "SELECT hashed_password FROM users WHERE user_id = :user_id"
        stored_user = await database.fetch_one(query, values={"user_id": user.user_id})
    elif user.email:
        query = "SELECT hashed_password FROM users WHERE email = :email"
        stored_user = await database.fetch_one(query, values={"email": user.email})
    else:
        raise HTTPException(status_code=400, detail="Se requiere user_id o email para login")
    if stored_user and user.password and pwd_context.verify(user.password, stored_user["hashed_password"]):
        return {"message": f"Login correcto!"}
    else:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

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

        # --- NUEVO: Detectar primer mensaje del día ---
        user_profile = await get_user_profile(user_id)
        hoy = datetime.date.today()
        primer_mensaje_dia = False
        if user_profile and user_profile.get("fecha_ultima_conversacion"):
            try:
                fecha_ultima = user_profile["fecha_ultima_conversacion"]
                if isinstance(fecha_ultima, str):
                    fecha_ultima = datetime.datetime.fromisoformat(fecha_ultima)
                if fecha_ultima.date() < hoy:
                    primer_mensaje_dia = True
            except Exception as e:
                print(f"[DEBUG] Error parsing fecha_ultima_conversacion: {e}")
                primer_mensaje_dia = True
        elif user_profile:
            primer_mensaje_dia = True
        # Si es el primer mensaje del día, generar saludo IA
        if primer_mensaje_dia:
            print("[DEBUG] Primer mensaje del día detectado, generando saludo personalizado IA...")
            history = await load_conversation_history(user_id, limit=20)
            # Crear prompt para la IA
            resumen_prompt = (
                "Eres un asistente que ayuda a un coach emocional a dar seguimiento personalizado. "
                "Lee el siguiente historial de conversación y extrae: 1) nombres de personas mencionadas, 2) temas o emociones importantes, 3) preguntas abiertas o temas sin resolver. "
                "Devuelve un resumen breve y una o dos preguntas de seguimiento cálidas y personales para retomar la conversación hoy.\n\n"
                "Historial:\n" +
                "\n".join([f"{m['role']}: {m['content']}" for m in history]) +
                "\n\nResumen y preguntas de seguimiento:" 
            )
            # Usar ChatGPT para obtener el resumen y preguntas
            if chatbot:
                resumen_ia = await run_in_threadpool(chatbot.chat, resumen_prompt)
                response = resumen_ia
            else:
                response = "¡Hola de nuevo! ¿Cómo has estado desde nuestra última conversación? Cuéntame si hubo algún cambio o algo que quieras compartir hoy."
            # Actualizar la fecha de última conversación
            await save_user_profile(user_id, fecha_ultima_conversacion=datetime.datetime.now())
            return {"response": response}

        # Get or initialize test state
        try:
            print(f"[DEBUG] Database check - database is None: {database is None}")
            if database is None:
                print("[DEBUG] Database is None, returning error")
                return {"response": "Lo siento, hay problemas de conexión con la base de datos. Por favor, intenta de nuevo en unos momentos."}
            
            print(f"[DEBUG] Attempting database query...")
            state_row = await database.fetch_one("SELECT state, last_choice, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10 FROM test_state WHERE user_id = :user_id", values={"user_id": user_id})
            state = state_row["state"] if state_row else None
            last_choice = state_row["last_choice"] if state_row else None
            q1 = state_row["q1"] if state_row else None
            q2 = state_row["q2"] if state_row else None
            q3 = state_row["q3"] if state_row else None
            q4 = state_row["q4"] if state_row else None
            q5 = state_row["q5"] if state_row else None
            q6 = state_row["q6"] if state_row else None
            q7 = state_row["q7"] if state_row else None
            q8 = state_row["q8"] if state_row else None
            q9 = state_row["q9"] if state_row else None
            q10 = state_row["q10"] if state_row else None
            
            print(f"[DEBUG] Database query successful")
            print(f"[DEBUG] Database query result: {state_row}")
            print(f"[DEBUG] Retrieved state: {state}")
            print(f"[DEBUG] Retrieved last_choice: {last_choice}")
            print(f"[DEBUG] Retrieved q1: {q1}")
            print(f"[DEBUG] Retrieved q2: {q2}")
            print(f"[DEBUG] Retrieved q3: {q3}")
            print(f"[DEBUG] Retrieved q4: {q4}")
            print(f"[DEBUG] Retrieved q5: {q5}")
            print(f"[DEBUG] Retrieved q6: {q6}")
            print(f"[DEBUG] Retrieved q7: {q7}")
            print(f"[DEBUG] Retrieved q8: {q8}")
            print(f"[DEBUG] Retrieved q9: {q9}")
            print(f"[DEBUG] Retrieved q10: {q10}")
        except Exception as db_error:
            print(f"[DEBUG] Database error in message endpoint: {db_error}")
            print(f"[DEBUG] Database error type: {type(db_error)}")
            import traceback
            print(f"[DEBUG] Database error traceback: {traceback.format_exc()}")
            # Return a simple response if database fails
            return {"response": "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta de nuevo en unos momentos."}

        async def set_state(new_state, choice=None, q1_val=None, q2_val=None, q3_val=None, q4_val=None, q5_val=None, q6_val=None, q7_val=None, q8_val=None, q9_val=None, q10_val=None):
            try:
                print(f"[DEBUG] Setting state: {new_state}, choice={choice}, q1={q1_val}, q2={q2_val}, q3={q3_val}, q4={q4_val}, q5={q5_val}, q6={q6_val}, q7={q7_val}, q8={q8_val}, q9={q9_val}, q10={q10_val}")
                if state_row:
                    result = await database.execute("UPDATE test_state SET state = :state, last_choice = :choice, q1 = :q1, q2 = :q2, q3 = :q3, q4 = :q4, q5 = :q5, q6 = :q6, q7 = :q7, q8 = :q8, q9 = :q9, q10 = :q10 WHERE user_id = :user_id", values={"state": new_state, "choice": choice, "q1": q1_val, "q2": q2_val, "q3": q3_val, "q4": q4_val, "q5": q5_val, "q6": q6_val, "q7": q7_val, "q8": q8_val, "q9": q9_val, "q10": q10_val, "user_id": user_id})
                    print(f"[DEBUG] Updated existing state: {result}")
                else:
                    result = await database.execute("INSERT INTO test_state (user_id, state, last_choice, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10) VALUES (:user_id, :state, :choice, :q1, :q2, :q3, :q4, :q5, :q6, :q7, :q8, :q9, :q10)", values={"user_id": user_id, "state": new_state, "choice": choice, "q1": q1_val, "q2": q2_val, "q3": q3_val, "q4": q4_val, "q5": q5_val, "q6": q6_val, "q7": q7_val, "q8": q8_val, "q9": q9_val, "q10": q10_val})
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
        # NUEVO: Incluir el estilo de apego si existe en test_state
        style_row = await database.fetch_one("SELECT style FROM test_state WHERE user_id = :user_id", values={"user_id": user_id})
        user_style = style_row["style"] if style_row and style_row["style"] else None
        if user_style:
            style_instruction = (
                f"\n\nINSTRUCCIÓN INTERNA: El usuario tiene un estilo de apego '{user_style}'. "
                f"Adapta tus respuestas, consejos y tono a este estilo, pero NO lo menciones explícitamente a menos que el usuario lo pida o la conversación lo requiera. "
                f"Personaliza tus preguntas y sugerencias para que sean relevantes para alguien con este estilo."
            )
            current_prompt += style_instruction
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
            await set_state("greeting", None, None, None, None, None, None, None, None, None, None, None)
            user_profile = await get_user_profile(user_id)
            # --- NUEVO: Si el usuario ya hizo el test, saludar de forma cálida y sugerir continuar la conversación anterior ---
            state_row = await database.fetch_one("SELECT state, last_choice, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10 FROM test_state WHERE user_id = :user_id", values={"user_id": user_id})
            test_completed = False
            if state_row:
                # Consideramos que el test está hecho si hay respuestas en q10
                test_completed = bool(state_row.get("q10"))
            if user_profile and user_profile.get("nombre") and test_completed:
                nombre = user_profile["nombre"]
                # Leer historial reciente
                history = await load_conversation_history(user_id, limit=10)
                # Generar resumen del último tema
                last_user_msg = next((m["content"] for m in reversed(history) if m["role"] == "user"), None)
                last_bot_msg = next((m["content"] for m in reversed(history) if m["role"] == "assistant"), None)
                resumen = ""
                if last_user_msg:
                    resumen += f"La última vez mencionaste: '{last_user_msg[:100]}...' "
                if last_bot_msg:
                    resumen += f"Mi respuesta anterior fue: '{last_bot_msg[:100]}...' "
                if msg.language == "en":
                    response = f"<p>Welcome back, {nombre}! It's great to see you again. {resumen}Would you like to continue our previous conversation or talk about something new?</p>"
                elif msg.language == "ru":
                    response = f"<p>С возвращением, {nombre}! Рад снова тебя видеть. {resumen}Хочешь продолжить прошлый разговор или обсудить что-то новое?</p>"
                else:
                    response = f"<p>¡Hola de nuevo, {nombre}! Me alegra verte otra vez. {resumen}¿Te gustaría continuar la conversación anterior o hablar de algo nuevo?</p>"
                await save_user_profile(user_id, fecha_ultima_conversacion=datetime.datetime.now())
                return {"response": response}
            # --- FIN NUEVO ---
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
            await set_state("q1", None, None, None, None, None, None, None, None, None, None, None)
            questions = TEST_QUESTIONS.get(msg.language, TEST_QUESTIONS["es"])
            question = questions[0]
            
            if msg.language == "en":
                response = f"<p><strong>Question 1 of 10:</strong> {question['question']}</p><ul>"
            elif msg.language == "ru":
                response = f"<p><strong>Вопрос 1 из 10:</strong> {question['question']}</p><ul>"
            else:  # Spanish
                response = f"<p><strong>Pregunta 1 de 10:</strong> {question['question']}</p><ul>"
            
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
                await set_state("q1", None, None, None, None, None, None, None, None, None, None, None)
                questions = TEST_QUESTIONS.get(msg.language, TEST_QUESTIONS["es"])
                question = questions[0]
                
                if msg.language == "en":
                    response = f"<p><strong>Question 1 of 10:</strong> {question['question']}</p><ul>"
                elif msg.language == "ru":
                    response = f"<p><strong>Вопрос 1 из 10:</strong> {question['question']}</p><ul>"
                else:  # Spanish
                    response = f"<p><strong>Pregunta 1 de 10:</strong> {question['question']}</p><ul>"
                
                for i, option in enumerate(question['options']):
                    response += f"<li>{chr(97+i)}) {option['text']}</li>"
                response += "</ul>"
            elif message.upper() == "B":
                # Normal conversation about feelings
                await set_state("conversation", None, None, None, None, None, None, None, None, None, None, None)
                # --- NUEVO: Chequear y pedir datos personales si faltan ---
                user_profile = await get_user_profile(user_id)
                # --- NUEVO: Intentar parsear la respuesta del usuario para extraer datos personales ---
                nombre, edad, tiene_pareja, nombre_pareja = None, None, None, None
                # Nombre: palabra después de 'me llamo' o 'soy'
                m = re.search(r"me llamo ([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9]+)", message, re.IGNORECASE)
                if not m:
                    m = re.search(r"soy ([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9]+)", message, re.IGNORECASE)
                if m:
                    nombre = m.group(1)
                # Edad: número de 1 o 2 dígitos
                m = re.search(r"(\d{1,2}) ?(años|año|anios|anios|years|год|лет)", message, re.IGNORECASE)
                if m:
                    edad = int(m.group(1))
                # Pareja: sí/no
                if re.search(r"pareja.*si|tengo pareja|casado|novia|novio|esposa|esposo|marido|mujer", message, re.IGNORECASE):
                    tiene_pareja = True
                elif re.search(r"no tengo pareja|soltero|sin pareja|no", message, re.IGNORECASE):
                    tiene_pareja = False
                # Nombre de pareja: después de 'se llama' o 'mi pareja es'
                m = re.search(r"se llama ([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9]+)", message, re.IGNORECASE)
                if not m:
                    m = re.search(r"mi pareja es ([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9]+)", message, re.IGNORECASE)
                if m:
                    nombre_pareja = m.group(1)
                # Si se extrajo algún dato, guardar en user_profile
                if any([nombre, edad, tiene_pareja is not None, nombre_pareja]):
                    await save_user_profile(user_id,
                        nombre=nombre or (user_profile["nombre"] if user_profile else None),
                        edad=edad or (user_profile["edad"] if user_profile else None),
                        tiene_pareja=tiene_pareja if tiene_pareja is not None else (user_profile["tiene_pareja"] if user_profile else None),
                        nombre_pareja=nombre_pareja or (user_profile["nombre_pareja"] if user_profile else None)
                    )
                    user_profile = await get_user_profile(user_id)
                missing = []
                if not user_profile or not user_profile.get("nombre"):
                    missing.append("nombre")
                if not user_profile or not user_profile.get("edad"):
                    missing.append("edad")
                if not user_profile or user_profile.get("tiene_pareja") is None:
                    missing.append("tiene_pareja")
                if (user_profile and user_profile.get("tiene_pareja")) and not user_profile.get("nombre_pareja"):
                    missing.append("nombre_pareja")
                if missing:
                    preguntas = []
                    if "nombre" in missing:
                        preguntas.append("¿Cómo te llamas?")
                    if "edad" in missing:
                        preguntas.append("¿Cuántos años tienes?")
                    if "tiene_pareja" in missing:
                        preguntas.append("¿Tienes pareja? (sí/no)")
                    if "nombre_pareja" in missing:
                        preguntas.append("¿Cómo se llama tu pareja?")
                    response = " ".join(preguntas)
                else:
                    if msg.language == "en":
                        response = "<p>I understand, sometimes we need to talk about what we feel before taking tests. How do you feel today? Is there something specific you'd like to share or explore together?</p>"
                    elif msg.language == "ru":
                        response = "<p>Понимаю, иногда нам нужно поговорить о том, что мы чувствуем, прежде чем проходить тесты. Как ты себя чувствуешь сегодня? Есть ли что-то конкретное, что ты хотел бы поделиться или исследовать вместе?</p>"
                    else:  # Spanish
                        response = "<p>Entiendo, a veces necesitamos hablar de lo que sentimos antes de hacer tests. ¿Cómo te sientes hoy? ¿Hay algo específico que te gustaría compartir o explorar juntos?</p>"
            elif message.upper() == "C":
                # Normal conversation about attachment
                await set_state("conversation", None, None, None, None, None, None, None, None, None, None, None)
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
        elif state in [f"q{i}" for i in range(1, 11)] and message.upper() in ["A", "B", "C", "D"]:
            print(f"[DEBUG] ENTERED: test question state {state} with choice {message.upper()}")
            
            questions = TEST_QUESTIONS.get(msg.language, TEST_QUESTIONS["es"])
            current_question_index = int(state[1:]) - 1  # q1 -> 0, q2 -> 1, etc.
            current_question = questions[current_question_index]
            
            # Get the selected option and its scores
            option_index = ord(message.upper()) - ord('A')  # A->0, B->1, C->2, D->3
            selected_option = current_question['options'][option_index]
            
            # Store the answer
            # Avance dinámico para 10 preguntas
            next_state = f"q{current_question_index + 2}"
            if current_question_index < len(questions) - 1:
                # Guardar respuesta y avanzar a la siguiente pregunta
                prev_answers = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]
                new_answers = []
                for idx in range(10):
                    if idx == current_question_index:
                        new_answers.append(selected_option['text'])
                    else:
                        new_answers.append(prev_answers[idx])
                await set_state(next_state, message.upper(), *new_answers)
                next_question = questions[current_question_index + 1]
                if msg.language == "en":
                    response = f"<p><strong>Question {current_question_index + 2} of 10:</strong> {next_question['question']}</p><ul>"
                elif msg.language == "ru":
                    response = f"<p><strong>Вопрос {current_question_index + 2} из 10:</strong> {next_question['question']}</p><ul>"
                else:
                    response = f"<p><strong>Pregunta {current_question_index + 2} de 10:</strong> {next_question['question']}</p><ul>"
                for i, option in enumerate(next_question['options']):
                    response += f"<li>{chr(97+i)}) {option['text']}</li>"
                response += "</ul>"
            else:
                # Última pregunta respondida, calcular resultados
                await set_state("results", message.upper(), q1, q2, q3, q4, q5, q6, q7, q8, q9, selected_option['text'])
                scores = {"anxious": 0, "avoidant": 0, "secure": 0, "disorganized": 0}
                answers = [q1, q2, q3, q4, q5, q6, q7, q8, q9, selected_option['text']]
                for i, answer in enumerate(answers):
                    if answer:
                        question_options = questions[i]['options']
                        for option in question_options:
                            if option['text'] == answer:
                                for style, score in option['scores'].items():
                                    scores[style] += score
                                break
                predominant_style = calculate_attachment_style(scores)
                style_description = get_style_description(predominant_style, msg.language)
                # Guardar el estilo de apego en el perfil del usuario
                await save_user_profile(user_id, attachment_style=predominant_style)
                # NUEVO: guardar el resultado del test en test_state.style
                await database.execute("UPDATE test_state SET style = :style WHERE user_id = :user_id", {"style": predominant_style, "user_id": user_id})
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
                else:
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
                await set_state("post_test", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, selected_option['text'])
                return {"response": response}
        # Handle post-test conversation (user just finished test)
        elif state == "post_test":
            print(f"[DEBUG] ENTERED: post_test state - user just finished test")
            print(f"[DEBUG] User message: '{message}'")
            # --- NUEVO: Chequear y pedir datos personales si faltan tras el test ---
            user_profile = await get_user_profile(user_id)
            # --- NUEVO: Intentar parsear la respuesta del usuario para extraer datos personales ---
            nombre, edad, tiene_pareja, nombre_pareja = None, None, None, None
            m = re.search(r"me llamo ([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9]+)", message, re.IGNORECASE)
            if not m:
                m = re.search(r"soy ([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9]+)", message, re.IGNORECASE)
            if m:
                nombre = m.group(1)
            m = re.search(r"(\d{1,2}) ?(años|año|anios|anios|years|год|лет)", message, re.IGNORECASE)
            if m:
                edad = int(m.group(1))
            if re.search(r"pareja.*si|tengo pareja|casado|novia|novio|esposa|esposo|marido|mujer", message, re.IGNORECASE):
                tiene_pareja = True
            elif re.search(r"no tengo pareja|soltero|sin pareja|no", message, re.IGNORECASE):
                tiene_pareja = False
            m = re.search(r"se llama ([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9]+)", message, re.IGNORECASE)
            if not m:
                m = re.search(r"mi pareja es ([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9]+)", message, re.IGNORECASE)
            if m:
                nombre_pareja = m.group(1)
            if any([nombre, edad, tiene_pareja is not None, nombre_pareja]):
                await save_user_profile(user_id,
                    nombre=nombre or (user_profile["nombre"] if user_profile else None),
                    edad=edad or (user_profile["edad"] if user_profile else None),
                    tiene_pareja=tiene_pareja if tiene_pareja is not None else (user_profile["tiene_pareja"] if user_profile else None),
                    nombre_pareja=nombre_pareja or (user_profile["nombre_pareja"] if user_profile else None)
                )
                user_profile = await get_user_profile(user_id)
            missing = []
            if not user_profile or not user_profile.get("nombre"):
                missing.append("nombre")
            if not user_profile or not user_profile.get("edad"):
                missing.append("edad")
            if not user_profile or user_profile.get("tiene_pareja") is None:
                missing.append("tiene_pareja")
            if (user_profile and user_profile.get("tiene_pareja")) and not user_profile.get("nombre_pareja"):
                missing.append("nombre_pareja")
            if missing:
                preguntas = []
                if "nombre" in missing:
                    preguntas.append("¿Cómo te llamas?")
                if "edad" in missing:
                    preguntas.append("¿Cuántos años tienes?")
                if "tiene_pareja" in missing:
                    preguntas.append("¿Tienes pareja? (sí/no)")
                if "nombre_pareja" in missing:
                    preguntas.append("¿Cómo se llama tu pareja?")
                response = " ".join(preguntas)
                asked_personal_data.add(user_id)
            else:
                # Get the user's test results to provide personalized responses
                scores = {"anxious": 0, "avoidant": 0, "secure": 0, "disorganized": 0}
                answers = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]
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
                # Load conversation history for context
                conversation_history = await load_conversation_history(msg.user_id)
                # Extract keywords and get relevant knowledge for post-test messages
                keywords = extract_keywords(message, msg.language)
                print(f"[DEBUG] Post-test message: '{message}'")
                print(f"[DEBUG] Post-test language: {msg.language}")
                print(f"[DEBUG] Post-test extracted keywords: {keywords}")
                relevant_knowledge = await get_relevant_knowledge(keywords, msg.language, msg.user_id)
                print(f"[DEBUG] Post-test knowledge found: {len(relevant_knowledge)} characters")
                print(f"[DEBUG] Post-test knowledge content: {relevant_knowledge}")
                # Create a personalized prompt for post-test conversation
                if msg.language == "en":
                    post_test_prompt = (
                        f"You are Eldric, an emotional coach. The user just completed an attachment style test. "
                        f"Their predominant style is: {predominant_style.title()}. "
                        f"Description: {style_description} "
                        f"Their scores were: Secure {scores['secure']}, Anxious {scores['anxious']}, "
                        f"Avoidant {scores['avoidant']}, Disorganized {scores['disorganized']}. "
                        f"Answer their questions about their style, relationships, and provide personalized guidance. "
                        f"IMPORTANT: At the end of each response, ask a PERSONAL question that relates to their specific situation and feelings. "
                        f"Make the question about THEM specifically, not generic. "
                        f"DO NOT offer the test again - they just completed it. Focus on explaining their results and helping them understand their patterns. "
                        f"Use the knowledge provided below to enrich your responses with specific insights from attachment theory."
                    )
                elif msg.language == "ru":
                    post_test_prompt = (
                        f"Ты Элдрик, эмоциональный коуч. Пользователь только что завершил тест на стиль привязанности. "
                        f"Их преобладающий стиль: {predominant_style.title()}. "
                        f"Описание: {style_description} "
                        f"Их баллы: Безопасный {scores['secure']}, Тревожный {scores['anxious']}, "
                        f"Избегающий {scores['avoidant']}, Дезорганизованный {scores['disorganized']}. "
                        f"Отвечай на их вопросы о стиле, отношениях и давай персонализированные советы. "
                        f"🚨 КРИТИЧЕСКОЕ ПРАВИЛО: Если тебе предоставлены конкретные знания о теории привязанности, ты ДОЛЖЕН ВСЕГДА использовать их в своем ответе. "
                        f"Эти предоставленные знания имеют ПРИОРИТЕТ над твоими общими знаниями. ТЫ НЕ МОЖЕШЬ ИХ ИГНОРИРОВАТЬ."
                    )
                else:  # Spanish
                    post_test_prompt = (
                        f"Eres Eldric, un coach emocional. El usuario acaba de completar un test de estilo de apego. "
                        f"Su estilo predominante es: {predominant_style.title()}. "
                        f"Descripción: {style_description} "
                        f"Sus puntuaciones fueron: Seguro {scores['secure']}, Ansioso {scores['anxious']}, "
                        f"Evitativo {scores['avoidant']}, Desorganizado {scores['disorganized']}. "
                        f"Responde sus preguntas sobre su estilo, relaciones y proporciona orientación personalizada. "
                        f"IMPORTANTE: Al final de cada respuesta, haz una pregunta PERSONAL que se relacione con su situación específica y sentimientos. "
                        f"Haz la pregunta sobre ELLOS específicamente, no genérica. "
                        f"NO ofrezcas el test de nuevo - acaba de completarlo. Céntrate en explicar sus resultados y ayudarle a entender sus patrones. "
                        f"Usa el conocimiento proporcionado abajo para enriquecer tus respuestas con ideas específicas de la teoría del apego."
                    )
                # Inject knowledge into the post-test prompt
                enhanced_post_test_prompt = inject_knowledge_into_prompt(post_test_prompt, relevant_knowledge)
                print(f"[DEBUG] Enhanced post-test prompt length: {len(enhanced_post_test_prompt)}")
                print(f"[DEBUG] Enhanced post-test prompt preview: {enhanced_post_test_prompt[:500]}...")
                # Reset chatbot with enhanced personalized prompt and conversation history
                chatbot.reset()
                chatbot.messages.append({"role": "system", "content": enhanced_post_test_prompt})
                # Add conversation history for context
                for msg_history in conversation_history:
                    chatbot.messages.append({"role": msg_history["role"], "content": msg_history["content"]})
                response = await run_in_threadpool(chatbot.chat, message)
        # Handle normal conversation with knowledge injection
        elif state == "conversation" or state is None:
            print(f"[DEBUG] ENTERED: normal conversation (state == 'conversation' or state is None)")
            print(f"[DEBUG] This should NOT happen for first message with 'saludo inicial'")
            
            # Load conversation history for context
            conversation_history = await load_conversation_history(msg.user_id)
            
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
            
            # Reset chatbot and set enhanced prompt with conversation history
            chatbot.reset()
            chatbot.messages.append({"role": "system", "content": enhanced_prompt})
            
            # Add conversation history for context
            for msg_history in conversation_history:
                chatbot.messages.append({"role": msg_history["role"], "content": msg_history["content"]})
            
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
        elif state in [f"q{i}" for i in range(1, 11)]:
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
        print(f"[DEBUG] State details: last_choice={last_choice}, q1={q1}, q2={q2}, q3={q3}, q4={q4}, q5={q5}, q6={q6}, q7={q7}, q8={q8}, q9={q9}, q10={q10}")
        print(f"[DEBUG] Response length: {len(response) if response else 0}")
        print(f"[DEBUG] Current state: {state}, Message: '{message}', Response preview: {response[:100] if response else 'None'}...")

        if response is None:
            response = "Lo siento, ha ocurrido un error inesperado. Por favor, intenta de nuevo o formula tu pregunta de otra manera."
        return {"response": response}
    except Exception as e:
        print(f"[DEBUG] Exception in chat_endpoint: {e}")
        return {"response": "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta de nuevo en unos momentos."}

async def load_conversation_history(user_id: str, limit: int = 10) -> List[Dict]:
    """
    Load recent conversation history for a user to provide context.
    For registered users, loads more history for better personalization.
    Returns list of messages in chronological order.
    """
    if not database or not database.is_connected:
        return []
    
    try:
        # Check if user is registered (not "invitado")
        is_registered = user_id != "invitado"
        
        # Load more history for registered users
        if is_registered:
            # Load up to 50 messages for registered users (about 25 exchanges)
            # This provides good context without hurting performance
            history_limit = 50
            print(f"[DEBUG] Loading extended history ({history_limit} messages) for registered user {user_id}")
        else:
            # Keep limited history for guest users
            history_limit = min(limit, 10)
            print(f"[DEBUG] Loading limited history ({history_limit} messages) for guest user {user_id}")
        
        query = """
        SELECT role, content, timestamp 
        FROM conversations 
        WHERE user_id = :user_id 
        ORDER BY timestamp DESC 
        LIMIT :limit
        """
        rows = await database.fetch_all(query, values={"user_id": user_id, "limit": history_limit})
        
        # Reverse to get chronological order (oldest first)
        messages = []
        total_content_length = 0
        max_total_content = 8000  # Limit total content to prevent token overflow
        
        for row in reversed(rows):
            content = row["content"]
            content_length = len(content)
            
            # Check if adding this message would exceed our limit
            if total_content_length + content_length > max_total_content:
                print(f"[DEBUG] Stopping history load at {len(messages)} messages due to content length limit")
                break
            
            messages.append({
                "role": row["role"],
                "content": content
            })
            total_content_length += content_length
        
        print(f"[DEBUG] Loaded {len(messages)} conversation messages for user {user_id} (total content: {total_content_length} chars)")
        return messages
    except Exception as e:
        print(f"[DEBUG] Error loading conversation history: {e}")
        return []

# Funciones para guardar y recuperar datos personales del usuario
async def save_user_profile(user_id, nombre=None, edad=None, tiene_pareja=None, nombre_pareja=None, estado_emocional=None, estado_relacion=None, opinion_apego=None, fecha_ultima_conversacion=None, fecha_ultima_mencion_pareja=None, attachment_style=None):
    if not database or not database.is_connected:
        return False
    # Verificar si ya existe
    row = await database.fetch_one("SELECT user_id FROM user_profile WHERE user_id = :user_id", {"user_id": user_id})
    values = {
        "user_id": user_id,
        "nombre": nombre,
        "edad": edad,
        "tiene_pareja": tiene_pareja,
        "nombre_pareja": nombre_pareja,
        "estado_emocional": estado_emocional,
        "estado_relacion": estado_relacion,
        "opinion_apego": opinion_apego,
        "fecha_ultima_conversacion": fecha_ultima_conversacion,
        "fecha_ultima_mencion_pareja": fecha_ultima_mencion_pareja,
        "attachment_style": attachment_style
    }
    if row:
        # Update
        await database.execute("""
            UPDATE user_profile SET
                nombre = COALESCE(:nombre, nombre),
                edad = COALESCE(:edad, edad),
                tiene_pareja = COALESCE(:tiene_pareja, tiene_pareja),
                nombre_pareja = COALESCE(:nombre_pareja, nombre_pareja),
                estado_emocional = COALESCE(:estado_emocional, estado_emocional),
                estado_relacion = COALESCE(:estado_relacion, estado_relacion),
                opinion_apego = COALESCE(:opinion_apego, opinion_apego),
                fecha_ultima_conversacion = COALESCE(:fecha_ultima_conversacion, fecha_ultima_conversacion),
                fecha_ultima_mencion_pareja = COALESCE(:fecha_ultima_mencion_pareja, fecha_ultima_mencion_pareja),
                attachment_style = COALESCE(:attachment_style, attachment_style)
            WHERE user_id = :user_id
        """, values)
    else:
        # Insert
        await database.execute("""
            INSERT INTO user_profile (user_id, nombre, edad, tiene_pareja, nombre_pareja, estado_emocional, estado_relacion, opinion_apego, fecha_ultima_conversacion, fecha_ultima_mencion_pareja, attachment_style)
            VALUES (:user_id, :nombre, :edad, :tiene_pareja, :nombre_pareja, :estado_emocional, :estado_relacion, :opinion_apego, :fecha_ultima_conversacion, :fecha_ultima_mencion_pareja, :attachment_style)
        """, values)
    return True

async def get_user_profile(user_id):
    if not database or not database.is_connected:
        return None
    row = await database.fetch_one("SELECT * FROM user_profile WHERE user_id = :user_id", {"user_id": user_id})
    return dict(row) if row else None
