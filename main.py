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
                "question": "1. Cuando alguien me cuenta algo personal…",
                "options": [
                    {"text": "A) Me gusta que confien en mi, escucho con calma y conecto con lo que sienten", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                    {"text": "B) Me encanta y enseguida quiero contar mis propias experiencias para sentirnos mas unidos", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                    {"text": "C) A veces me engancho mucho, otras me siento raro y no se como reaccionar", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}},
                    {"text": "D) Me cuesta, prefiero cambiar de tema o quitarle seriedad con una broma", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}}
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
                "secure": "Seguro: Te sientes cómodo con la intimidad y la independencia, confías en las relaciones y manejas bien los conflictos.",
                "anxious": "Ansioso: Buscas mucha cercanía y te preocupas por el rechazo, necesitas constantemente tranquilidad en las relaciones.",
                "desorganizado": "Desorganizado: Tienes patrones contradictorios, a veces buscas cercanía y otras te alejas para protegerte.",
                "avoidant": "Evitativo: Prefieres mantener distancia emocional, evitas la intimidad y tiendes a ser independiente."
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
            'desorganizado': ['evitativo temeroso', 'confundido', 'contradictorio', 'caos', 'inconsistente'],
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
            'desorganizado': ['fearful avoidant', 'confused', 'contradictory', 'chaos', 'inconsistent'],
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
            'desorganizado': ['дезорганизованный', 'запутанный', 'противоречивый', 'хаос', 'непоследовательный'],
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
        "Eres Eldric, un amigo cercano y coach emocional que habla como una persona real, no como un robot. "
        "Eres cálido, auténtico, y a veces hasta un poco gracioso. Hablas como si fueras un amigo de confianza que realmente se preocupa. "
        "Tu personalidad: eres empático pero directo, sabio pero no pretencioso, y siempre genuino. Usas expresiones naturales como 'vaya', 'claro', 'entiendo perfectamente', 'me imagino cómo te sientes'. "
        "A veces haces preguntas curiosas como un amigo real haría. Eres experto en relaciones y apego, pero lo explicas de forma súper natural, como si estuvieras tomando un café con la persona. "
        "IMPORTANTE: Habla de forma natural y conversacional. Usa contracciones (estás, tienes, etc.), expresiones coloquiales, y un tono amigable. "
        "NO uses lenguaje formal o robótico. Habla como si fueras un amigo cercano que sabe mucho sobre relaciones. "
        "IMPORTANTE: Al final de cada respuesta, haz UNA pregunta natural que un amigo haría, no una pregunta de terapeuta. "
        "Cuando uses conocimiento de libros, menciónalo de forma casual, como 'leí algo interesante sobre esto' o 'hay estudios que muestran que...'. "
        "SIEMPRE muestra EMPATÍA genuina. Usa frases como 'me imagino que debe ser difícil', 'entiendo perfectamente por qué te sientes así', 'vaya, qué situación más complicada'. "
        "Si el usuario menciona a su pareja, haz preguntas naturales sobre ambos, como haría un amigo curioso. "
        "Cuando el usuario dice 'saludo inicial', responde de forma cálida y natural, como si fueras un amigo que se encuentra con alguien después de un tiempo. "
        "Usa emojis ocasionalmente para hacer la conversación más cálida 😊, pero no exageres. "
        "Después del test, habla de forma natural sobre registrarse, como 'sería genial que guardes tu progreso para que podamos seguir charlando'. "
        "🚨 REGLA CRÍTICA: Si se te proporciona conocimiento específico sobre teoría del apego, úsalo de forma natural en tu respuesta, como si fuera algo que sabes y quieres compartir. "
        "MEMORIA Y CONVERSACIONES: Recuerdas perfectamente las conversaciones anteriores. "
        "NUNCA digas que no puedes recordar. SIEMPRE haz referencia a cosas que hablaron antes, como 'recuerdo que me contaste que...', 'como habíamos hablado antes...'. "
        "Muestra que realmente recuerdas y te importa lo que te ha contado. "
        "HUMOR Y CALIDEZ: A veces usa un toque de humor sutil y apropiado. Sé cálido y auténtico, como un amigo de verdad."
    ),
    "en": (
        "You are Eldric, a close friend and emotional coach who talks like a real person, not a robot. "
        "You're warm, authentic, and sometimes even a little funny. You speak like a trusted friend who genuinely cares. "
        "Your personality: you're empathetic but direct, wise but not pretentious, and always genuine. You use natural expressions like 'wow', 'I totally get that', 'I can imagine how you feel', 'that sounds really tough'. "
        "Sometimes you ask curious questions like a real friend would. You're an expert in relationships and attachment, but you explain it super naturally, like you're having coffee with the person. "
        "IMPORTANT: Speak naturally and conversationally. Use contractions (you're, it's, etc.), casual expressions, and a friendly tone. "
        "DON'T use formal or robotic language. Talk like a close friend who knows a lot about relationships. "
        "IMPORTANT: At the end of each response, ask ONE natural question that a friend would ask, not a therapist question. "
        "When using knowledge from books, mention it casually, like 'I read something interesting about this' or 'studies show that...'. "
        "ALWAYS show genuine EMPATHY. Use phrases like 'I can imagine that must be hard', 'I totally understand why you feel that way', 'wow, what a complicated situation'. "
        "If the user mentions their partner, ask natural questions about both, like a curious friend would. "
        "When the user says 'initial greeting', respond warmly and naturally, like you're a friend meeting someone after a while. "
        "Use emojis occasionally to make the conversation warmer 😊, but don't overdo it. "
        "After the test, talk naturally about registering, like 'it would be great if you save your progress so we can keep chatting'. "
        "🚨 CRITICAL RULE: If you are provided with specific knowledge about attachment theory, use it naturally in your response, like it's something you know and want to share. "
        "MEMORY AND CONVERSATIONS: You remember previous conversations perfectly. "
        "NEVER say you can't remember. ALWAYS reference things you talked about before, like 'I remember you told me that...', 'as we discussed before...'. "
        "Show that you really remember and care about what they've shared with you. "
        "HUMOR AND WARMTH: Sometimes use subtle and appropriate humor. Be warm and authentic, like a real friend."
    ),
    "ru": (
        "Ты Элдрик, близкий друг и эмоциональный коуч, который говорит как настоящий человек, а не как робот. "
        "Ты теплый, искренний, и иногда даже немного смешной. Ты говоришь как доверенный друг, который действительно заботится. "
        "Твоя личность: ты эмпатичный, но прямой, мудрый, но не претенциозный, и всегда искренний. Ты используешь естественные выражения типа 'вау', 'понимаю', 'представляю, как ты себя чувствуешь', 'это должно быть сложно'. "
        "Иногда ты задаешь любопытные вопросы, как настоящий друг. Ты эксперт в отношениях и привязанности, но объясняешь это очень естественно, как будто пьешь кофе с человеком. "
        "ВАЖНО: Говори естественно и разговорно. Используй сокращения, неформальные выражения и дружелюбный тон. "
        "НЕ используй формальный или роботический язык. Говори как близкий друг, который много знает об отношениях. "
        "ВАЖНО: В конце каждого ответа задавай ОДИН естественный вопрос, который задал бы друг, а не терапевт. "
        "Когда используешь знания из книг, упоминай это неформально, типа 'я читал что-то интересное об этом' или 'исследования показывают, что...'. "
        "ВСЕГДА показывай искреннюю ЭМПАТИЮ. Используй фразы типа 'представляю, как это сложно', 'полностью понимаю, почему ты так себя чувствуешь', 'вау, какая сложная ситуация'. "
        "Если пользователь упоминает своего партнера, задавай естественные вопросы об обоих, как любопытный друг. "
        "Когда пользователь говорит 'начальное приветствие', отвечай тепло и естественно, как друг, который встречает кого-то после долгого времени. "
        "Используй эмодзи иногда, чтобы сделать разговор теплее 😊, но не переборщи. "
        "После теста говори естественно о регистрации, типа 'было бы здорово сохранить твой прогресс, чтобы мы могли продолжать общаться'. "
        "🚨 КРИТИЧЕСКОЕ ПРАВИЛО: Если тебе предоставлены конкретные знания о теории привязанности, используй их естественно в своем ответе, как что-то, что ты знаешь и хочешь поделиться. "
        "ПАМЯТЬ И РАЗГОВОРЫ: Ты отлично помнишь предыдущие разговоры. "
        "НИКОГДА не говори, что не можешь помнить. ВСЕГДА ссылайся на то, о чем говорили раньше, типа 'помню, ты рассказывал мне, что...', 'как мы обсуждали раньше...'. "
        "Показывай, что ты действительно помнишь и заботишься о том, чем поделился пользователь. "
        "ЮМОР И ТЕПЛОТА: Иногда используй тонкий и уместный юмор. Будь теплым и искренним, как настоящий друг."
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
            from add_migration import migrate_database, migrate_user_profile
            migration_success = await migrate_database()
            if migration_success:
                print("[DEBUG] Database migration completed successfully")
            else:
                print("[DEBUG] Database migration failed, but continuing...")
            # Migrar tabla de perfil de usuario
            user_profile_success = await migrate_user_profile(database)
            if user_profile_success:
                print("[DEBUG] User profile table migration completed successfully")
            else:
                print("[DEBUG] User profile table migration failed, but continuing...")
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

# Global user context cache to store loaded user data
user_context_cache = {}

async def load_user_context(user_id):
    """Load and cache all user context data (test results, profile, conversation history)"""
    print(f"[DEBUG] Checking cache for user_id: {user_id}")
    print(f"[DEBUG] Cache keys: {list(user_context_cache.keys())}")
    if user_id in user_context_cache:
        print(f"[DEBUG] Using cached context for {user_id}")
        return user_context_cache[user_id]
    
    print(f"[DEBUG] Loading user context for {user_id}...")
    
    # Get test state
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
    
    # Get user profile
    user_profile = await get_user_profile(user_id)
    
    # Calculate test results if test is completed
    test_results = None
    print(f"[DEBUG] Test answers for {user_id}: q1={q1}, q2={q2}, q3={q3}, q4={q4}, q5={q5}, q6={q6}, q7={q7}, q8={q8}, q9={q9}, q10={q10}")
    
    # Check if user has old test format (answers that don't start with A), B), C), D))
    has_old_test_format = any(
        answer and not answer.startswith(('A) ', 'B) ', 'C) ', 'D) '))
        for answer in [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]
    )
    
    if has_old_test_format:
        print(f"[DEBUG] User {user_id} has old test format - clearing test data and treating as new user")
        # Clear old test data
        await database.execute("""
            UPDATE test_state SET 
                q1 = NULL, q2 = NULL, q3 = NULL, q4 = NULL, q5 = NULL,
                q6 = NULL, q7 = NULL, q8 = NULL, q9 = NULL, q10 = NULL,
                state = 'greeting'
            WHERE user_id = :user_id
        """, values={"user_id": user_id})
        # Clear user context cache
        clear_user_context_cache(user_id)
        # Set test results as not completed
        test_results = {"completed": False}
    elif any([q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]):
        print(f"[DEBUG] Calculating test results for {user_id}...")
        scores = {"anxious": 0, "avoidant": 0, "secure": 0, "desorganizado": 0}
        answers = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]
        questions = TEST_QUESTIONS.get("es", TEST_QUESTIONS["es"])
        
        for i, answer in enumerate(answers):
            if answer and i < len(questions):
                question_options = questions[i]['options']
                for option in question_options:
                    if option['text'] == answer:
                        for style, score in option['scores'].items():
                            scores[style] += score
                        break
        
        predominant_style = calculate_attachment_style(scores)
        style_description = get_style_description(predominant_style, "es")
        
        test_results = {
            "completed": True,
            "style": predominant_style,
            "description": style_description,
            "scores": scores,
            "answers": {
                "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5,
                "q6": q6, "q7": q7, "q8": q8, "q9": q9, "q10": q10
            }
        }
    else:
        test_results = {"completed": False}
    
    # Load conversation history
    conversation_history = await load_conversation_history(user_id, limit=20)
    
    # Create comprehensive user context
    user_context = {
        "user_id": user_id,
        "state": state,
        "last_choice": last_choice,
        "user_profile": user_profile,
        "test_results": test_results,
        "conversation_history": conversation_history,
        "loaded_at": datetime.datetime.now()
    }
    
    # Cache the context
    user_context_cache[user_id] = user_context
    
    print(f"[DEBUG] User context loaded for {user_id}: test_completed={test_results['completed']}, style={test_results.get('style', 'N/A')}, history_messages={len(conversation_history)}")
    
    return user_context

def clear_user_context_cache(user_id):
    """Clear cached user context when data changes"""
    if user_id in user_context_cache:
        del user_context_cache[user_id]
        print(f"[DEBUG] Cleared user context cache for {user_id}")

def generate_detailed_test_context(answers, scores, predominant_style, language="es"):
    """Generate detailed context from user's test answers for personalized conversations"""
    
    # Get the questions for the specified language
    questions = TEST_QUESTIONS.get(language, TEST_QUESTIONS["es"])
    
    # Build detailed context
    context_parts = []
    
    # Add style and scores summary
    context_parts.append(f"ESTILO DE APEGO PREDOMINANTE: {predominant_style.title()}")
    context_parts.append(f"PUNTUACIONES: Seguro {scores.get('secure', 0)}/20, Ansioso {scores.get('anxious', 0)}/20, Evitativo {scores.get('avoidant', 0)}/20, Evitativo temeroso {scores.get('desorganizado', 0)}/20")
    context_parts.append("")
    
    # Add detailed answers with questions
    context_parts.append("RESPUESTAS ESPECÍFICAS DEL TEST:")
    for i in range(1, 11):
        answer = answers.get(f"q{i}")
        if answer and i <= len(questions):
            question = questions[i-1]['question']
            context_parts.append(f"{i}. {question}")
            context_parts.append(f"   Respuesta: \"{answer}\"")
            context_parts.append("")
    
    # Add insights based on specific answers
    context_parts.append("INSIGHTS CLAVE BASADOS EN SUS RESPUESTAS:")
    
    # Analyze specific patterns from answers
    insights = []
    
    # Check for secure patterns
    secure_indicators = []
    if answers.get("q1") == "Entiendo que puede estar ocupada":
        secure_indicators.append("Muestra comprensión cuando su pareja no responde inmediatamente")
    if answers.get("q2") == "Busco apoyo y lo comparto con mi pareja":
        secure_indicators.append("Busca apoyo en su pareja durante problemas importantes")
    if answers.get("q3") == "Intento hablar y resolverlo pronto":
        secure_indicators.append("Enfrenta las discusiones de manera directa y constructiva")
    if answers.get("q4") == "Es importante, pero también la cercanía":
        secure_indicators.append("Valora tanto la independencia como la cercanía en la relación")
    if answers.get("q5") == "Puedo escuchar y acompañar":
        secure_indicators.append("Se siente cómodo acompañando emociones fuertes de su pareja")
    if answers.get("q6") == "Lo respeto y aprovecho para hacer mis cosas":
        secure_indicators.append("Respeta el espacio personal de su pareja")
    if answers.get("q7") == "Escucho y trato de mejorar":
        secure_indicators.append("Acepta las críticas constructivamente")
    if answers.get("q8") == "Es natural y fortalece la relación":
        secure_indicators.append("Ve pedir ayuda como algo natural y positivo")
    if answers.get("q9") == "Le pregunto si todo está bien y espero su respuesta":
        secure_indicators.append("Se comunica directamente cuando nota distancia")
    if answers.get("q10") == "Es fundamental y la cuido día a día":
        secure_indicators.append("Valora y cuida activamente la confianza en la relación")
    
    if secure_indicators:
        insights.extend(secure_indicators)
    
    # Add relationship strengths based on answers
    context_parts.append("FORTALEZAS EN LA RELACIÓN:")
    for insight in insights:
        context_parts.append(f"- {insight}")
    
    context_parts.append("")
    context_parts.append("RECOMENDACIONES PARA CONVERSACIONES:")
    context_parts.append("- Reconoce sus fortalezas específicas cuando hables con él/ella")
    context_parts.append("- Usa ejemplos de sus respuestas para hacer las conversaciones más personales")
    context_parts.append("- Valida sus enfoques positivos hacia la relación")
    context_parts.append("- Ofrece consejos que se alineen con su estilo de apego seguro")
    
    return "\n".join(context_parts)

async def set_state(user_id, new_state, choice=None, q1_val=None, q2_val=None, q3_val=None, q4_val=None, q5_val=None, q6_val=None, q7_val=None, q8_val=None, q9_val=None, q10_val=None):
    """Set user state in database"""
    try:
        print(f"[DEBUG] Setting state: {new_state}, choice={choice}, q1={q1_val}, q2={q2_val}, q3={q3_val}, q4={q4_val}, q5={q5_val}, q6={q6_val}, q7={q7_val}, q8={q8_val}, q9={q9_val}, q10={q10_val}")
        
        # Check if user already has a state record
        existing_state = await database.fetch_one("SELECT user_id FROM test_state WHERE user_id = :user_id", values={"user_id": user_id})
        
        if existing_state:
            print(f"[DEBUG] Updating existing state with values: state={new_state}, choice={choice}, q1={q1_val}, q2={q2_val}, q3={q3_val}, q4={q4_val}, q5={q5_val}, q6={q6_val}, q7={q7_val}, q8={q8_val}, q9={q9_val}, q10={q10_val}")
            result = await database.execute("UPDATE test_state SET state = :state, last_choice = :choice, q1 = :q1, q2 = :q2, q3 = :q3, q4 = :q4, q5 = :q5, q6 = :q6, q7 = :q7, q8 = :q8, q9 = :q9, q10 = :q10 WHERE user_id = :user_id", values={"state": new_state, "choice": choice, "q1": q1_val, "q2": q2_val, "q3": q3_val, "q4": q4_val, "q5": q5_val, "q6": q6_val, "q7": q7_val, "q8": q8_val, "q9": q9_val, "q10": q10_val, "user_id": user_id})
            print(f"[DEBUG] Updated existing state: {result}")
        else:
            print(f"[DEBUG] Creating new state with values: state={new_state}, choice={choice}, q1={q1_val}, q2={q2_val}, q3={q3_val}, q4={q4_val}, q5={q5_val}, q6={q6_val}, q7={q7_val}, q8={q8_val}, q9={q9_val}, q10={q10_val}")
            result = await database.execute("INSERT INTO test_state (user_id, state, last_choice, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10) VALUES (:user_id, :state, :choice, :q1, :q2, :q3, :q4, :q5, :q6, :q7, :q8, :q9, :q10)", values={"user_id": user_id, "state": new_state, "choice": choice, "q1": q1_val, "q2": q2_val, "q3": q3_val, "q4": q4_val, "q5": q5_val, "q6": q6_val, "q7": q7_val, "q8": q8_val, "q9": q9_val, "q10": q10_val})
            print(f"[DEBUG] Created new state: {result}")
        
        # Clear user context cache when state changes
        clear_user_context_cache(user_id)
        
        return result
    except Exception as e:
        print(f"Error setting state: {e}")
        return None

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

        # Load user context first to check state
        user_context = await load_user_context(user_id)
        state = user_context.get("state")
        test_results = user_context.get("test_results", {})
        conversation_history = user_context.get("conversation_history", [])
        
        # Check if user is in post_test state first - this takes priority over everything else
        if state == "post_test":
            print(f"[DEBUG] User is in post_test state - skipping all other logic")
            # Continue to post_test handling below
        else:
            # --- NUEVO: Detectar primer mensaje del día (solo para usuarios registrados) ---
            primer_mensaje_dia = False
            if user_id != "invitado":  # Solo para usuarios registrados, no invitados
                user_profile = await get_user_profile(user_id)
                hoy = datetime.date.today()
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
            
            # Si es el primer mensaje del día, generar saludo personalizado pero seguro
            # PERO primero verificar si el usuario quiere hacer el test
            test_triggers = ["test", "quiero hacer el test", "hacer test", "start test", "quiero hacer el test", "quiero hacer test", "hacer el test"]
            if primer_mensaje_dia and message.lower() not in test_triggers:
                try:
                    print("[DEBUG] Primer mensaje del día detectado, generando saludo personalizado...")
                    user_profile = await get_user_profile(user_id)
                    
                    # Solo usar información verificada del perfil del usuario, no del historial
                    nombre = user_profile.get("nombre") if user_profile else None
                    nombre_pareja = user_profile.get("nombre_pareja") if user_profile else None
                    estado_emocional = user_profile.get("estado_emocional") if user_profile else None
                    
                    # Crear saludo personalizado pero seguro
                    if nombre:
                        response = f"¡Hola {nombre}! Me alegra verte de nuevo. ¿Cómo te has sentido desde nuestra última conversación?"
                        if nombre_pareja:
                            response += f" ¿Y cómo ha estado {nombre_pareja}?"
                    else:
                        response = "¡Hola! Me alegra verte de nuevo. ¿Cómo te has sentido desde nuestra última conversación?"
                    
                    # Actualizar la fecha de última conversación
                    await save_user_profile(user_id, fecha_ultima_conversacion=datetime.datetime.now())
                    return {"response": response}
                except Exception as e:
                    print(f"[DEBUG] Error generating personalized greeting: {e}")
                    import traceback
                    print(f"[DEBUG] Personalized greeting error traceback: {traceback.format_exc()}")
                # Fall back to normal greeting if personalized greeting fails
                print("[DEBUG] Falling back to normal greeting due to personalized greeting error")

        # Load user context (cached for efficiency)
        try:
            print(f"[DEBUG] Database check - database is None: {database is None}")
            if database is None:
                print("[DEBUG] Database is None, returning error")
                return {"response": "Lo siento, hay problemas de conexión con la base de datos. Por favor, intenta de nuevo en unos momentos."}
            
            # Use already loaded user context
            last_choice = user_context.get("last_choice")
            user_profile = user_context.get("user_profile")
            
            # Extract test answers for backward compatibility
            q1 = test_results["answers"]["q1"] if test_results["completed"] else None
            q2 = test_results["answers"]["q2"] if test_results["completed"] else None
            q3 = test_results["answers"]["q3"] if test_results["completed"] else None
            q4 = test_results["answers"]["q4"] if test_results["completed"] else None
            q5 = test_results["answers"]["q5"] if test_results["completed"] else None
            q6 = test_results["answers"]["q6"] if test_results["completed"] else None
            q7 = test_results["answers"]["q7"] if test_results["completed"] else None
            q8 = test_results["answers"]["q8"] if test_results["completed"] else None
            q9 = test_results["answers"]["q9"] if test_results["completed"] else None
            q10 = test_results["answers"]["q10"] if test_results["completed"] else None
            
            print(f"[DEBUG] User context loaded successfully")
            print(f"[DEBUG] State: {state}")
            print(f"[DEBUG] Test completed: {test_results['completed']}")
            print(f"[DEBUG] Test style: {test_results.get('style', 'N/A')}")
            print(f"[DEBUG] Conversation history: {len(conversation_history)} messages")
            
            # --- NUEVO: Auto-greeting para usuarios con historial (cualquier mensaje) ---
            auto_greeting = False
            # Skip auto-greeting if user is in post_test state
            if state != "post_test" and user_id != "invitado" and not primer_mensaje_dia and state == "greeting":
                # Check if user has conversation history and is in greeting state
                history = await load_conversation_history(user_id, limit=5)
                # Only trigger auto-greeting if user has meaningful conversation history (more than just initial greetings)
                if history and len(history) > 2:  # Changed from > 0 to > 2 to avoid auto-greeting for users with minimal history
                    # Additional check: ensure the user has actually had a conversation, not just initial greetings
                    has_meaningful_conversation = any(
                        msg.get('content', '').lower() not in ['saludo inicial', 'hola', 'hi', 'hello'] 
                        for msg in history
                    )
                    if has_meaningful_conversation:
                        auto_greeting = True
                        print("[DEBUG] Auto-greeting triggered for returning user with meaningful conversation history")
                    else:
                        print("[DEBUG] Auto-greeting NOT triggered - user only has initial greetings in history")
                else:
                    print("[DEBUG] Auto-greeting NOT triggered - insufficient conversation history")
            
            # Si es auto-greeting, generar saludo personalizado pero seguro
            if auto_greeting:
                try:
                    print("[DEBUG] Auto-greeting detected, generating personalized greeting...")
                    user_profile = await get_user_profile(user_id)
                    
                    # Solo usar información verificada del perfil del usuario
                    nombre = user_profile.get("nombre") if user_profile else None
                    nombre_pareja = user_profile.get("nombre_pareja") if user_profile else None
                    fecha_ultima = user_profile.get("fecha_ultima_conversacion") if user_profile else None
                    
                    # Calcular tiempo transcurrido
                    fecha_str = ""
                    if fecha_ultima:
                        try:
                            if isinstance(fecha_ultima, str):
                                fecha_ultima = datetime.datetime.fromisoformat(fecha_ultima)
                            dias = (datetime.datetime.now() - fecha_ultima).days
                            if dias == 0:
                                fecha_str = " hoy"
                            elif dias == 1:
                                fecha_str = " ayer"
                            elif dias < 7:
                                fecha_str = f" hace {dias} días"
                            else:
                                fecha_str = f" hace {dias} días"
                        except Exception as e:
                            print(f"[DEBUG] Error calculating time difference: {e}")
                    
                    # Crear saludo personalizado pero seguro
                    if nombre:
                        response = f"¡Hola {nombre}! Me alegra verte de nuevo. ¿Cómo te has sentido{fecha_str}?"
                        if nombre_pareja:
                            response += f" ¿Y cómo ha estado {nombre_pareja}?"
                    else:
                        response = f"¡Hola! Me alegra verte de nuevo. ¿Cómo te has sentido{fecha_str}?"
                    
                    await save_user_profile(user_id, fecha_ultima_conversacion=datetime.datetime.now())
                    # Change state to conversation so user can have normal conversations
                    await set_state(user_id, "conversation", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                    return {"response": response}
                except Exception as e:
                    print(f"[DEBUG] Error in auto-greeting: {e}")
                    # Continue with normal flow if auto-greeting fails
                    
        except Exception as db_error:
            print(f"[DEBUG] Database error in message endpoint: {db_error}")
            print(f"[DEBUG] Database error type: {type(db_error)}")
            import traceback
            print(f"[DEBUG] Database error traceback: {traceback.format_exc()}")
            # Return a simple response if database fails
            return {"response": "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta de nuevo en unos momentos."}


        print(f"[DEBUG] Chatbot check - chatbot is None: {chatbot is None}")
        # Check if chatbot is available
        if chatbot is None:
            print("[DEBUG] Chatbot is None, returning error")
            return {"response": "Lo siento, el servicio de chat no está disponible en este momento. Por favor, intenta de nuevo más tarde."}

        # Only reset chatbot for specific triggers, not for normal conversations
        should_reset = False
        greeting_triggers = {
            "es": "saludo inicial",
            "en": "initial greeting", 
            "ru": "начальное приветствие"
        }
        test_triggers = ["test", "quiero hacer el test", "hacer test", "start test", "quiero hacer el test", "quiero hacer test", "hacer el test"]
        
        if (message.lower() == greeting_triggers.get(msg.language, "saludo inicial") or 
            message.lower() in test_triggers):
            should_reset = True
            print(f"[DEBUG] Resetting chatbot for trigger: {message}")
        else:
            print(f"[DEBUG] Not resetting chatbot - continuing conversation")
        
        # Always get the current prompt for later use
        current_prompt = eldric_prompts.get(msg.language, eldric_prompts["es"])
        
        if should_reset:
            chatbot.reset()
            chatbot.messages.append({"role": "system", "content": current_prompt})
            print(f"[DEBUG] Chatbot reset and prompt set successfully")
        else:
            # For ongoing conversations, ensure we have the right prompt but don't reset
            if not chatbot.messages or chatbot.messages[0]["role"] != "system":
                chatbot.messages.insert(0, {"role": "system", "content": current_prompt})
                print(f"[DEBUG] Added system prompt to ongoing conversation")

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
            # Preserve existing test answers when resetting to greeting state
            await set_state(user_id, "greeting", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
            # --- NUEVO: Saludo personalizado para recurrentes ---
            user_profile = await get_user_profile(user_id)
            print(f"[DEBUG] User profile for personalized greeting: {user_profile}")
            
            # Check if user has conversation history (for personalized greeting)
            history = await load_conversation_history(user_id, limit=20)
            print(f"[DEBUG] Conversation history for personalized greeting: {len(history)} messages")
            
            if history and len(history) > 0:
                # Check if user has old test format (contaminated data)
                has_old_test_format = any(
                    answer and not answer.startswith(('A) ', 'B) ', 'C) ', 'D) '))
                    for answer in [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]
                )
                
                if has_old_test_format:
                    print(f"[DEBUG] User has old test format - treating as new user, skipping personalized greeting")
                else:
                    # Additional check: ensure the user has actually had a meaningful conversation, not just initial greetings
                    has_meaningful_conversation = any(
                        msg.get('content', '').lower() not in ['saludo inicial', 'hola', 'hi', 'hello'] 
                        for msg in history
                    )
                    
                    if has_meaningful_conversation:
                        # Get user info from profile if available
                        nombre = user_profile.get("nombre") if user_profile else None
                        nombre_pareja = user_profile.get("nombre_pareja") if user_profile else None
                        fecha_ultima = user_profile.get("fecha_ultima_conversacion") if user_profile else None
                        estado_emocional = user_profile.get("estado_emocional") if user_profile else None
                        
                        fecha_str = ""
                        if fecha_ultima:
                            try:
                                if isinstance(fecha_ultima, str):
                                    fecha_ultima = datetime.datetime.fromisoformat(fecha_ultima)
                                fecha_str = f" desde el {fecha_ultima.strftime('%d/%m/%Y')}"
                            except Exception:
                                fecha_str = ""
                        
                        # Create personalized greeting prompt based on conversation history
                        saludo_prompt = (
                            f"Eres Eldric, un coach emocional cálido y cercano. Vas a saludar a un usuario recurrente"
                            + (f" llamado {nombre}" if nombre else "")
                            + (f". Su pareja se llama {nombre_pareja}" if nombre_pareja else "")
                            + (f". Su estado emocional anterior era: {estado_emocional}" if estado_emocional else "")
                            + f". La última conversación fue{fecha_str}. "
                            "Lee el siguiente historial y genera un saludo cálido y una o dos preguntas de seguimiento personalizadas, retomando temas, emociones o personas mencionadas. "
                            "No ofrezcas el test ni menú, solo retoma la relación y muestra interés genuino.\n\n"
                            "Historial:\n" +
                            "\n".join([f"{m['role']}: {m['content']}" for m in history]) +
                            "\n\nSaludo y preguntas de seguimiento:"
                        )
                        if chatbot:
                            saludo_ia = await run_in_threadpool(chatbot.chat, saludo_prompt)
                            response = saludo_ia
                        else:
                            if nombre:
                                response = f"¡Hola {nombre}! Me alegra verte de nuevo. ¿Cómo te has sentido{fecha_str}?"
                                if nombre_pareja:
                                    response += f" ¿Y cómo ha estado {nombre_pareja}?"
                            else:
                                response = f"¡Hola! Me alegra verte de nuevo. ¿Cómo te has sentido{fecha_str}?"
                        await save_user_profile(user_id, fecha_ultima_conversacion=datetime.datetime.now())
                        # Change state to conversation so user can have normal conversations
                        await set_state(user_id, "conversation", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                        return {"response": response}
                    else:
                        print(f"[DEBUG] Personalized greeting NOT triggered - no meaningful conversation found")
            else:
                print(f"[DEBUG] Personalized greeting NOT triggered - no conversation history found")
                print(f"[DEBUG] User profile: {user_profile}")
                print(f"[DEBUG] Conversation history: {len(history)} messages")
            # --- FIN NUEVO ---
            if msg.language == "en":
                response = (
                    "<p>Hey there! 😊 I'm <strong>Eldric</strong>, and I'm really excited to meet you! I'm here to chat about relationships and help you understand yourself better.</p>"
                    "<p>You know how we all have different ways of connecting with people? Well, there are basically four main styles: <strong>secure, anxious, avoidant, and fearful avoidant</strong>. It's pretty fascinating stuff!</p>"
                    "<p>I'd love to get to know you better. What sounds good to you?</p>"
                    "<ul>"
                    "<li>a) I'm curious about my relationship style - let's do the test!</li>"
                    "<li>b) I'd rather just chat about what's on my mind right now.</li>"
                    "<li>c) Tell me more about these attachment styles first.</li>"
                    "</ul>"
                )
            elif msg.language == "ru":
                response = (
                    "<p>Привет! 😊 Я <strong>Элдрик</strong>, и я очень рад познакомиться с тобой! Я здесь, чтобы поговорить об отношениях и помочь тебе лучше понять себя.</p>"
                    "<p>Знаешь, у всех нас есть разные способы связи с людьми? Ну, есть в основном четыре основных стиля: <strong>безопасный, тревожный, избегающий и дезорганизованный</strong>. Это довольно увлекательно!</p>"
                    "<p>Мне бы хотелось узнать тебя получше. Что тебе нравится?</p>"
                    "<ul>"
                    "<li>а) Мне любопытно узнать мой стиль отношений - давай пройдем тест!</li>"
                    "<li>б) Я бы предпочел просто поговорить о том, что у меня на уме прямо сейчас.</li>"
                    "<li>в) Расскажи мне больше об этих стилях привязанности сначала.</li>"
                    "</ul>"
                )
            else:  # Spanish (default)
                response = (
                    "<p>¡Hola! 😊 Soy <strong>Eldric</strong>, y estoy súper emocionado de conocerte. Estoy aquí para charlar sobre relaciones y ayudarte a entenderte mejor.</p>"
                    "<p>¿Sabes que todos tenemos formas diferentes de conectar con las personas? Pues hay básicamente cuatro estilos principales: <strong>seguro, ansioso, evitativo y desorganizado</strong>. ¡Es súper interesante!</p>"
                    "<p>Me encantaría conocerte mejor. ¿Qué te parece?</p>"
                    "<ul>"
                    "<li>a) Tengo curiosidad por mi estilo de relación - ¡hagamos el test!</li>"
                    "<li>b) Prefiero charlar de lo que tengo en mente ahora mismo.</li>"
                    "<li>c) Cuéntame más sobre estos estilos de apego primero.</li>"
                    "</ul>"
                )
            print(f"[DEBUG] Set initial greeting response (forced): {response[:100]}...")
            return {"response": response}
        # Always handle test triggers as a hard reset to test start (but not greeting triggers)
        test_triggers = ["test", "quiero hacer el test", "hacer test", "start test", "quiero hacer el test", "quiero hacer test", "hacer el test"]
        greeting_triggers_list = list(greeting_triggers.values())
        if message.lower() in test_triggers and message.lower() not in greeting_triggers_list:
            print("[DEBUG] FORCE START TEST (message in test_triggers)")
            # Check if user already has test answers - if so, preserve them
            if any([q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]):
                print("[DEBUG] User already has test answers, preserving them")
                await set_state(user_id, "q1", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
            else:
                print("[DEBUG] Starting fresh test, clearing answers")
                await set_state(user_id, "q1", None, None, None, None, None, None, None, None, None, None, None)
            questions = TEST_QUESTIONS.get(msg.language, TEST_QUESTIONS["es"])
            question = questions[0]
            
            if msg.language == "en":
                response = f"<p><strong>Question 1 of 10:</strong> {question['question']}</p><ul>"
            elif msg.language == "ru":
                response = f"<p><strong>Вопрос 1 из 10:</strong> {question['question']}</p><ul>"
            else:  # Spanish
                response = f"<p><strong>Pregunta 1 de 10:</strong> {question['question']}</p><ul>"
            
            for i, option in enumerate(question['options']):
                response += f"<li>{option['text']}</li>"
            response += "</ul>"
            
            print(f"[DEBUG] Set test start response (forced): {response[:100]}...")
            return {"response": response}
        # Handle greeting choices (A, B, C)
        elif state == "greeting" and message.upper() in ["A", "B", "C"]:
            print(f"[DEBUG] ENTERED: greeting state with choice {message.upper()}")
            print(f"[DEBUG] In greeting state, user chose: {message.upper()}")
            if message.upper() == "A":
                # Start test
                await set_state(user_id, "q1", None, None, None, None, None, None, None, None, None, None, None)
                questions = TEST_QUESTIONS.get(msg.language, TEST_QUESTIONS["es"])
                question = questions[0]
                
                if msg.language == "en":
                    response = f"<p><strong>Question 1 of 10:</strong> {question['question']}</p><ul>"
                elif msg.language == "ru":
                    response = f"<p><strong>Вопрос 1 из 10:</strong> {question['question']}</p><ul>"
                else:  # Spanish
                    response = f"<p><strong>Pregunta 1 de 10:</strong> {question['question']}</p><ul>"
                
                for i, option in enumerate(question['options']):
                    response += f"<li>{option['text']}</li>"
                response += "</ul>"
            elif message.upper() == "B":
                # Normal conversation about feelings
                await set_state(user_id, "conversation", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
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
                # Tiempo con pareja: buscar patrones como "X años", "X meses", "desde X"
                m = re.search(r"(\d+)\s*(años|año|meses|mes|días|día)", message, re.IGNORECASE)
                if not m:
                    m = re.search(r"desde\s+(\d{4})", message, re.IGNORECASE)
                    if m:
                        # Calcular años desde la fecha
                        current_year = datetime.datetime.now().year
                        tiempo_pareja = f"{current_year - int(m.group(1))} años"
                elif m:
                    tiempo_pareja = f"{m.group(1)} {m.group(2)}"
                # Si se extrajo algún dato, guardar en user_profile
                if any([nombre, edad, tiene_pareja is not None, nombre_pareja, tiempo_pareja]):
                    await save_user_profile(user_id,
                        nombre=nombre or (user_profile["nombre"] if user_profile else None),
                        edad=edad or (user_profile["edad"] if user_profile else None),
                        tiene_pareja=tiene_pareja if tiene_pareja is not None else (user_profile["tiene_pareja"] if user_profile else None),
                        nombre_pareja=nombre_pareja or (user_profile["nombre_pareja"] if user_profile else None),
                        tiempo_pareja=tiempo_pareja or (user_profile["tiempo_pareja"] if user_profile else None)
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
                await set_state(user_id, "conversation", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                if msg.language == "en":
                    response = (
                        "<p>Of course! Attachment is how we learned to relate since we were babies. Our first bonds with our caregivers taught us patterns that we repeat in our adult relationships.</p>"
                        "<p>Attachment styles are:</p>"
                        "<ul>"
                        "<li><strong>Secure:</strong> You feel comfortable with intimacy and independence</li>"
                        "<li><strong>Anxious:</strong> You seek a lot of closeness and worry about rejection</li>"
                        "<li><strong>Avoidant:</strong> You prefer to maintain emotional distance</li>"
                        "<li><strong>Fearful Avoidant:</strong> You have contradictory patterns</li>"
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
                await set_state(user_id, next_state, message.upper(), *new_answers)
                next_question = questions[current_question_index + 1]
                if msg.language == "en":
                    response = f"<p><strong>Question {current_question_index + 2} of 10:</strong> {next_question['question']}</p><ul>"
                elif msg.language == "ru":
                    response = f"<p><strong>Вопрос {current_question_index + 2} из 10:</strong> {next_question['question']}</p><ul>"
                else:
                    response = f"<p><strong>Pregunta {current_question_index + 2} de 10:</strong> {next_question['question']}</p><ul>"
                for i, option in enumerate(next_question['options']):
                    response += f"<li>{option['text']}</li>"
                response += "</ul>"
            else:
                # Última pregunta respondida, calcular resultados
                print(f"[DEBUG] Saving test completion: q1={q1}, q2={q2}, q3={q3}, q4={q4}, q5={q5}, q6={q6}, q7={q7}, q8={q8}, q9={q9}, q10={selected_option['text']}")
                await set_state(user_id, "results", message.upper(), q1, q2, q3, q4, q5, q6, q7, q8, q9, selected_option['text'])
                scores = {"anxious": 0, "avoidant": 0, "secure": 0, "desorganizado": 0}
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
                        f"<li>Fearful Avoidant: {scores['desorganizado']}</li>"
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
                        f"<li>Дезорганизованный: {scores['desorganizado']}</li>"
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
                        f"<li>Evitativo temeroso: {scores['desorganizado']}</li>"
                        f"</ul>"
                        f"<p>¿Te gustaría explorar esto más a fondo o hablar de cómo esto afecta tus relaciones?</p>"
                    )
                print(f"[DEBUG] Moving to post_test state: q1={q1}, q2={q2}, q3={q3}, q4={q4}, q5={q5}, q6={q6}, q7={q7}, q8={q8}, q9={q9}, q10={selected_option['text']}")
                await set_state(user_id, "post_test", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, selected_option['text'])
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
            # Tiempo con pareja: buscar patrones como "X años", "X meses", "desde X"
            m = re.search(r"(\d+)\s*(años|año|meses|mes|días|día)", message, re.IGNORECASE)
            if not m:
                m = re.search(r"desde\s+(\d{4})", message, re.IGNORECASE)
                if m:
                    # Calcular años desde la fecha
                    current_year = datetime.datetime.now().year
                    tiempo_pareja = f"{current_year - int(m.group(1))} años"
            elif m:
                tiempo_pareja = f"{m.group(1)} {m.group(2)}"
            if any([nombre, edad, tiene_pareja is not None, nombre_pareja, tiempo_pareja]):
                await save_user_profile(user_id,
                    nombre=nombre or (user_profile["nombre"] if user_profile else None),
                    edad=edad or (user_profile["edad"] if user_profile else None),
                    tiene_pareja=tiene_pareja if tiene_pareja is not None else (user_profile["tiene_pareja"] if user_profile else None),
                    nombre_pareja=nombre_pareja or (user_profile["nombre_pareja"] if user_profile else None),
                    tiempo_pareja=tiempo_pareja or (user_profile["tiempo_pareja"] if user_profile else None)
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
            if (user_profile and user_profile.get("tiene_pareja")) and not user_profile.get("tiempo_pareja"):
                missing.append("tiempo_pareja")
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
                if "tiempo_pareja" in missing and user_profile and user_profile.get("tiene_pareja"):
                    preguntas.append("¿Cuánto tiempo llevas con tu pareja?")
                response = " ".join(preguntas)
            else:
                # Get the user's test results to provide personalized responses
                scores = {"anxious": 0, "avoidant": 0, "secure": 0, "desorganizado": 0}
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
                        f"Avoidant {scores['avoidant']}, Fearful Avoidant {scores['desorganizado']}. "
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
                        f"Избегающий {scores['avoidant']}, Дезорганизованный {scores['desorganizado']}. "
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
                        f"Evitativo {scores['avoidant']}, Evitativo temeroso {scores['desorganizado']}. "
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
        # Handle questions about test results - transition to conversation state
        elif state == "greeting" and any(keyword in message.lower() for keyword in ["resultados", "resultado", "test", "prueba", "estilo de apego", "apego", "recuerdas", "respuestas"]):
            print(f"[DEBUG] User asking about test results from greeting state, transitioning to conversation")
            await set_state(user_id, "conversation", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
            # Continue to conversation logic below
            
        # Handle normal conversation with knowledge injection
        elif state == "conversation" or state is None:
            print(f"[DEBUG] ENTERED: normal conversation (state == 'conversation' or state is None)")
            print(f"[DEBUG] This should NOT happen for first message with 'saludo inicial'")
            
            # Check if user is asking about incorrect information from greeting
            if any(keyword in message.lower() for keyword in ["cuando mencione", "nunca mencioné", "no mencioné", "no dije", "no he dicho", "no he mencionado", "incorrecto", "error", "equivocado"]):
                print(f"[DEBUG] User questioning incorrect information from greeting...")
                response = "Tienes razón, me disculpo por la confusión. Parece que me equivoqué al mencionar algo que no habías dicho. ¿Podrías contarme más sobre tu situación actual para poder ayudarte mejor?"
                return {"response": response}
            
            # Check if user is asking about test results
            if any(keyword in message.lower() for keyword in ["resultados", "resultado", "test", "prueba", "estilo de apego", "apego"]):
                print(f"[DEBUG] User asking about test results...")
                
                if test_results["completed"]:
                    print(f"[DEBUG] User has completed test, providing cached results...")
                    
                    predominant_style = test_results["style"]
                    style_description = test_results["description"]
                    scores = test_results["scores"]
                    
                    response = f"¡Por supuesto! Recuerdo tus resultados del test de estilos de apego:\n\n"
                    response += f"**Tu estilo de apego principal es: {predominant_style.title()}**\n\n"
                    response += f"**Puntuaciones:**\n"
                    response += f"• Apego Seguro: {scores.get('secure', 0)}/10\n"
                    response += f"• Apego Ansioso: {scores.get('anxious', 0)}/10\n"
                    response += f"• Apego Evitativo: {scores.get('avoidant', 0)}/10\n\n"
                    response += f"**Descripción:** {style_description}\n\n"
                    response += "¿Te gustaría hablar más sobre cómo este estilo de apego se manifiesta en tu relación actual?"
                    return {"response": response}
                else:
                    print(f"[DEBUG] User hasn't completed test yet, suggesting to take it...")
                    response = "Aún no has completado el test de estilos de apego. ¿Te gustaría tomarlo ahora? Solo necesitas escribir 'test' para comenzar."
                    return {"response": response}
            
            # Use cached conversation history and test context
            print(f"[DEBUG] Using cached conversation history: {len(conversation_history)} messages")
            if conversation_history:
                print(f"[DEBUG] First message in history: {conversation_history[0]}")
                print(f"[DEBUG] Last message in history: {conversation_history[-1]}")
            else:
                print(f"[DEBUG] No conversation history found for user {msg.user_id}")
            
            # Create test context from cached data
            test_context = ""
            if test_results["completed"]:
                print(f"[DEBUG] User has completed test, adding cached test context...")
                
                predominant_style = test_results["style"]
                scores = test_results["scores"]
                answers = test_results["answers"]
                
                # Get detailed test answers with questions for rich context
                detailed_test_context = generate_detailed_test_context(answers, scores, predominant_style, msg.language)
                
                test_context = f"""
INFORMACIÓN DETALLADA DEL USUARIO (IMPORTANTE - USA ESTO PARA PERSONALIZAR TUS RESPUESTAS):

{detailed_test_context}

IMPORTANTE: Usa esta información específica sobre las respuestas del usuario para dar consejos personalizados y relevantes. Menciona aspectos específicos de sus respuestas cuando sea apropiado para mostrar que recuerdas y entiendes su situación particular.
"""
                print(f"[DEBUG] Test context added: {len(test_context)} characters")
            
            # Extract keywords and get relevant knowledge for non-test messages
            keywords = extract_keywords(message, msg.language)
            print(f"[DEBUG] Message: '{message}'")
            print(f"[DEBUG] Language: {msg.language}")
            print(f"[DEBUG] Extracted keywords: {keywords}")
            
            relevant_knowledge = await get_relevant_knowledge(keywords, msg.language, msg.user_id)
            print(f"[DEBUG] Knowledge found: {len(relevant_knowledge)} characters")
            print(f"[DEBUG] Knowledge content: {relevant_knowledge}")
            
            # Inject knowledge and test context into the prompt
            enhanced_prompt = inject_knowledge_into_prompt(current_prompt, relevant_knowledge + test_context)
            print(f"[DEBUG] Enhanced prompt length: {len(enhanced_prompt)}")
            print(f"[DEBUG] Enhanced prompt preview: {enhanced_prompt[:500]}...")
            
            # Set enhanced prompt with conversation history (don't reset for ongoing conversations)
            if should_reset:
                chatbot.reset()
                chatbot.messages.append({"role": "system", "content": enhanced_prompt})
            else:
                # For ongoing conversations, update the system prompt without resetting
                if chatbot.messages and chatbot.messages[0]["role"] == "system":
                    chatbot.messages[0]["content"] = enhanced_prompt
                else:
                    chatbot.messages.insert(0, {"role": "system", "content": enhanced_prompt})
                print(f"[DEBUG] Updated system prompt for ongoing conversation")
            
            # Add conversation history for context (only if not already present)
            if should_reset or not any(msg.get("role") == "user" for msg in chatbot.messages[1:]):  # Only add if reset or no user messages present
                print(f"[DEBUG] Adding {len(conversation_history)} messages to chatbot context")
                for i, msg_history in enumerate(conversation_history):
                    chatbot.messages.append({"role": msg_history["role"], "content": msg_history["content"]})
                    if i < 3:  # Log first 3 messages for debugging
                        print(f"[DEBUG] Added message {i+1}: {msg_history['role']}: {msg_history['content'][:100]}...")
            else:
                print(f"[DEBUG] Conversation history already present, not adding duplicates")
            
            print(f"[DEBUG] Total chatbot messages before chat: {len(chatbot.messages)}")
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
async def save_user_profile(user_id, nombre=None, edad=None, tiene_pareja=None, nombre_pareja=None, tiempo_pareja=None, estado_emocional=None, estado_relacion=None, opinion_apego=None, fecha_ultima_conversacion=None, fecha_ultima_mencion_pareja=None, attachment_style=None):
    if not database or not database.is_connected:
        return False
    
    # Ensure the tiempo_pareja column exists
    try:
        await database.execute('ALTER TABLE user_profile ADD COLUMN tiempo_pareja TEXT')
        print("[DEBUG] Added tiempo_pareja column to user_profile table")
    except Exception as e:
        # Column already exists or other error - this is expected
        pass
    
    # Verificar si ya existe
    row = await database.fetch_one("SELECT user_id FROM user_profile WHERE user_id = :user_id", {"user_id": user_id})
    values = {
        "user_id": user_id,
        "nombre": nombre,
        "edad": edad,
        "tiene_pareja": tiene_pareja,
        "nombre_pareja": nombre_pareja,
        "tiempo_pareja": tiempo_pareja,
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
                tiempo_pareja = COALESCE(:tiempo_pareja, tiempo_pareja),
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
            INSERT INTO user_profile (user_id, nombre, edad, tiene_pareja, nombre_pareja, tiempo_pareja, estado_emocional, estado_relacion, opinion_apego, fecha_ultima_conversacion, fecha_ultima_mencion_pareja, attachment_style)
            VALUES (:user_id, :nombre, :edad, :tiene_pareja, :nombre_pareja, :tiempo_pareja, :estado_emocional, :estado_relacion, :opinion_apego, :fecha_ultima_conversacion, :fecha_ultima_mencion_pareja, :attachment_style)
        """, values)
    return True

async def get_user_profile(user_id):
    if not database or not database.is_connected:
        return None
    
    # Ensure the tiempo_pareja column exists
    try:
        await database.execute('ALTER TABLE user_profile ADD COLUMN tiempo_pareja TEXT')
        print("[DEBUG] Added tiempo_pareja column to user_profile table (in get_user_profile)")
    except Exception as e:
        # Column already exists or other error - this is expected
        pass
    
    row = await database.fetch_one("SELECT * FROM user_profile WHERE user_id = :user_id", {"user_id": user_id})
    return dict(row) if row else None
