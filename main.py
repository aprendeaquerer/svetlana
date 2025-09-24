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
from typing import Dict, List, Any
import re
import datetime

# Try to import test questions, fallback to simple version if import fails
try:
    from test_questions import TEST_QUESTIONS, PARTNER_TEST_QUESTIONS, calculate_attachment_style, get_style_description, calculate_relationship_status, get_relationship_description
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
    
    # Fallback partner test questions
    PARTNER_TEST_QUESTIONS = {
        "es": [
            {
                "question": "1. Cuando sale el tema de planes a futuro…",
                "options": [
                    {"text": "A) Habla de futuro conmigo de forma natural", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                    {"text": "B) Hace mil preguntas y necesita respuestas rápido", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                    {"text": "C) Intenta cambiar la conversación", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}},
                    {"text": "D) Sus respuestas me confunden", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}}
                ]
            }
        ]
    }
    
    def calculate_relationship_status(user_style, partner_style):
        if not user_style or not partner_style:
            return "unknown"
        styles = sorted([user_style, partner_style])
        combination = f"{styles[0]}_and_{styles[1]}"
        relationship_dynamics = {
            "secure_and_secure": "secure_secure",
            "secure_and_anxious": "secure_anxious", 
            "secure_and_avoidant": "secure_avoidant",
            "secure_and_desorganizado": "secure_disorganized",
            "anxious_and_anxious": "anxious_anxious",
            "anxious_and_avoidant": "anxious_avoidant",
            "anxious_and_desorganizado": "anxious_disorganized", 
            "avoidant_and_avoidant": "avoidant_avoidant",
            "avoidant_and_desorganizado": "avoidant_disorganized",
            "desorganizado_and_desorganizado": "disorganized_disorganized"
        }
        return relationship_dynamics.get(combination, "unknown")
    
    def get_relationship_description(relationship_status, language="es"):
        descriptions = {
            "es": {
                "secure_secure": "Relación segura-segura: Ambos manejan bien la intimidad y la independencia.",
                "secure_anxious": "Relación segura-ansiosa: El estilo seguro puede proporcionar estabilidad al ansioso.",
                "secure_avoidant": "Relación segura-evitativa: El estilo seguro respeta la necesidad de espacio del evitativo.",
                "secure_disorganized": "Relación segura-desorganizada: El estilo seguro puede proporcionar consistencia.",
                "anxious_anxious": "Relación ansiosa-ansiosa: Alta intensidad emocional, pero pueden reforzarse mutuamente las inseguridades.",
                "anxious_avoidant": "Relación ansiosa-evitativa: Dinámica clásica de persecución-evitación.",
                "anxious_disorganized": "Relación ansiosa-desorganizada: Patrones impredecibles y alta intensidad emocional.",
                "avoidant_avoidant": "Relación evitativa-evitativa: Ambos mantienen distancia emocional.",
                "avoidant_disorganized": "Relación evitativa-desorganizada: Patrones contradictorios.",
                "disorganized_disorganized": "Relación desorganizada-desorganizada: Patrones muy impredecibles y caóticos.",
                "unknown": "Estado de relación no determinado"
            }
        }
        return descriptions.get(language, descriptions["es"]).get(relationship_status, "Estado de relación no determinado")

# Daily affirmations are now stored in the database (affirmations table)

# --- Lightweight translation layer for testing (es <-> en/ru) ---
_translator_available = False
try:
    from deep_translator import GoogleTranslator  # type: ignore
    _translator_available = True
    print("[DEBUG] Deep Translator successfully imported and available")
except Exception as e:
    print(f"[DEBUG] Deep Translator not available: {e}")
    print("[DEBUG] Translation will be disabled - install with: pip install deep-translator")

async def translate_text(text: str, target_lang: str) -> str:
    if not text or target_lang == "es":
        return text
    if not _translator_available:
        print(f"[DEBUG] Translation requested but deep-translator not available. Returning original text.")
        return text
    try:
        # Map our language codes to Google Translate codes
        lang_map = {"en": "en", "ru": "ru", "es": "es"}
        target_code = lang_map.get(target_lang, target_lang)
        
        result = GoogleTranslator(source='es', target=target_code).translate(text)
        print(f"[DEBUG] Translated to {target_lang}: '{text[:50]}...' -> '{result[:50]}...'")
        return result
    except Exception as e:
        print(f"[DEBUG] Translation error: {e}")
        return text

async def translate_to_es(text: str, source_lang: str) -> str:
    if not text or source_lang == "es":
        return text
    if not _translator_available:
        print(f"[DEBUG] Translation requested but deep-translator not available. Returning original text.")
        return text
    try:
        # Map our language codes to Google Translate codes
        lang_map = {"en": "en", "ru": "ru", "es": "es"}
        source_code = lang_map.get(source_lang, source_lang)
        
        result = GoogleTranslator(source=source_code, target='es').translate(text)
        print(f"[DEBUG] Translated to ES: '{text[:50]}...' -> '{result[:50]}...'")
        return result
    except Exception as e:
        print(f"[DEBUG] Translation error: {e}")
        return text

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

class EmailRegistration(BaseModel):
    email: str
    password: str = None
    nombre: str = None
    edad: int = None
    tiene_pareja: bool = None
    nombre_pareja: str = None

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

@app.post("/register-email")
async def register_with_email_endpoint(registration: EmailRegistration):
    """Register user with email and optional personal information"""
    if database is None:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    
    # Validate email format
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, registration.email):
        raise HTTPException(status_code=400, detail="Formato de email inválido")
    
    # Check if email already exists
    existing_user = await database.fetch_one(
        "SELECT user_id FROM users WHERE email = :email", 
        values={"email": registration.email}
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="Este email ya está registrado")
    
    # Use email as user_id
    user_id = registration.email
    
    # Hash password if provided
    hashed_password = None
    if registration.password:
        hashed_password = pwd_context.hash(registration.password)
    
    try:
        # Insert user into users table
        await database.execute(
            "INSERT INTO users (user_id, hashed_password, email) VALUES (:user_id, :hashed_password, :email)",
            values={
                "user_id": user_id, 
                "hashed_password": hashed_password, 
                "email": registration.email
            }
        )
        
        # Insert personal information into user_profile table if provided
        if any([registration.nombre, registration.edad is not None, registration.tiene_pareja is not None, registration.nombre_pareja]):
            await save_user_profile(
                user_id=user_id,
                nombre=registration.nombre,
                edad=registration.edad,
                tiene_pareja=registration.tiene_pareja,
                nombre_pareja=registration.nombre_pareja
            )
        
        # Generate and send verification code
        code = await generate_verification_code()
        await store_verification_code(user_id, code)
        await send_verification_email(registration.email, code)
        
        return {
            "message": f"Usuario registrado correctamente con email {registration.email}. Se ha enviado un código de verificación.",
            "user_id": user_id,
            "email": registration.email,
            "verification_sent": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al registrar usuario: {str(e)}")

@app.get("/user-by-email/{email}")
async def get_user_by_email(email: str):
    """Get user information by email"""
    if database is None:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    
    try:
        # Get user from users table
        user = await database.fetch_one(
            "SELECT user_id, email FROM users WHERE email = :email",
            values={"email": email}
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Get user profile information
        user_profile = await get_user_profile(user["user_id"])
        
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "profile": user_profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuario: {str(e)}")

@app.put("/update-profile/{email}")
async def update_user_profile(email: str, profile_data: EmailRegistration):
    """Update user profile information by email"""
    if database is None:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    
    try:
        # Get user_id from email
        user = await database.fetch_one(
            "SELECT user_id FROM users WHERE email = :email",
            values={"email": email}
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user_id = user["user_id"]
        
        # Update profile information
        await save_user_profile(
            user_id=user_id,
            nombre=profile_data.nombre,
            edad=profile_data.edad,
            tiene_pareja=profile_data.tiene_pareja,
            nombre_pareja=profile_data.nombre_pareja
        )
        
        return {
            "message": "Perfil actualizado correctamente",
            "user_id": user_id,
            "email": email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar perfil: {str(e)}")

@app.post("/send-verification/{email}")
async def send_verification_code_endpoint(email: str):
    """Send verification code to user's email"""
    if database is None:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    
    try:
        # Check if user exists
        user = await database.fetch_one(
            "SELECT user_id FROM users WHERE email = :email",
            values={"email": email}
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user_id = user["user_id"]
        
        # Generate and store verification code
        code = await generate_verification_code()
        await store_verification_code(user_id, code)
        
        # Send verification email
        await send_verification_email(email, code)
        
        return {
            "message": f"Código de verificación enviado a {email}",
            "email": email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al enviar código: {str(e)}")

@app.post("/verify-email/{email}")
async def verify_email_endpoint(email: str, code: str):
    """Verify email with verification code"""
    if database is None:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    
    try:
        # Get user_id from email
        user = await database.fetch_one(
            "SELECT user_id FROM users WHERE email = :email",
            values={"email": email}
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user_id = user["user_id"]
        
        # Verify the code
        if await verify_email_code(user_id, code):
            return {
                "message": "Email verificado correctamente",
                "email": email,
                "verified": True
            }
        else:
            raise HTTPException(status_code=400, detail="Código inválido o expirado")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar email: {str(e)}")

@app.get("/verification-status/{email}")
async def get_verification_status_endpoint(email: str):
    """Get email verification status"""
    if database is None:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    
    try:
        # Get user verification status
        user = await database.fetch_one(
            "SELECT user_id, email_verified FROM users WHERE email = :email",
            values={"email": email}
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {
            "email": email,
            "verified": user["email_verified"] == True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estado: {str(e)}")

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
        # If no answer rows, but profile has a stored attachment style, treat as completed
        if user_profile and user_profile.get("attachment_style"):
            predominant_style = user_profile.get("attachment_style")
            style_description = get_style_description(predominant_style, "es")
            test_results = {
                "completed": True,
                "style": predominant_style,
                "description": style_description,
                "scores": {"anxious": 0, "avoidant": 0, "secure": 0, "desorganizado": 0},
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
        # Get user's preferred language or use the one from the message
        user_preferred_language = await get_user_language_preference(user_id)
        original_language = (msg.language or user_preferred_language or "es").lower()
        incoming_raw = msg.message.strip()
        print(f"[DEBUG] user_id: {user_id}")
        print(f"[DEBUG] incoming_raw: '{incoming_raw}'")
        print(f"[DEBUG] msg.language: '{msg.language}'")
        print(f"[DEBUG] user_preferred_language: '{user_preferred_language}'")
        print(f"[DEBUG] original_language: '{original_language}'")
        print(f"[DEBUG] _translator_available: {_translator_available}")
        
        # Check for language switching requests
        incoming_lower = incoming_raw.lower()
        language_switch_detected = False
        if any(phrase in incoming_lower for phrase in ["can we speak in english", "speak in english", "talk in english", "english please", "en inglés"]):
            original_language = "en"
            language_switch_detected = True
            print(f"[DEBUG] Language switch detected: switching to English")
            # Save the language preference
            await save_user_language_preference(user_id, "en")
        elif any(phrase in incoming_lower for phrase in ["can we speak in russian", "speak in russian", "talk in russian", "russian please", "en ruso", "по-русски"]):
            original_language = "ru"
            language_switch_detected = True
            print(f"[DEBUG] Language switch detected: switching to Russian")
            # Save the language preference
            await save_user_language_preference(user_id, "ru")
        elif msg.language and msg.language != user_preferred_language:
            # Frontend language selector changed
            original_language = msg.language.lower()
            print(f"[DEBUG] Frontend language selector changed to: {original_language}")
            # Save the language preference
            await save_user_language_preference(user_id, original_language)
        
        # Pre-translation trigger detection using the user's selected language
        greeting_triggers_map = {
            "es": ["saludo inicial", "hola"],
            "en": ["initial greeting", "hi", "hello"],
            "ru": ["начальное приветствие", "привет", "здравствуйте"],
        }
        test_triggers_map = {
            "es": ["test", "quiero hacer el test", "hacer test", "hacer el test"],
            "en": ["test", "start test"],
            "ru": ["тест", "начать тест"],
        }
        selected_lang_for_triggers = original_language if original_language in ["es", "en", "ru"] else "es"
        pre_greeting_trigger = any(t == incoming_lower for t in greeting_triggers_map.get(selected_lang_for_triggers, ["saludo inicial"]))
        pre_test_trigger = any(incoming_lower == t for t in test_triggers_map.get(selected_lang_for_triggers, ["test"]))

        if original_language in ["en", "ru"]:
            message = await translate_to_es(incoming_raw, original_language)
        else:
            message = incoming_raw
        print(f"[DEBUG] message (normalized to es): '{message}'")
        
        # Handle language switch requests with immediate response
        if language_switch_detected:
            if original_language == "en":
                response = "¡Por supuesto! I'll speak to you in English from now on. How are you doing today?"
            elif original_language == "ru":
                response = "¡Por supuesto! Я буду говорить с вами по-русски отныне. Как дела?"
            else:
                response = "¡Por supuesto! I'll speak to you in English from now on. How are you doing today?"
            
            # Translate the response to the requested language
            if original_language in ["en", "ru"]:
                response = await translate_text(response, original_language)
            return {"response": response}

        # Load full snapshot and user context
        full_snapshot = await load_full_user_snapshot(user_id)
        # Load user context (includes computed test_results and history)
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
                    
                    # Check if user should be offered a daily affirmation
                    affirmation_response = ""
                    if await should_offer_affirmation(user_id):
                        print(f"[DEBUG] Offering daily affirmation in personalized greeting to user {user_id}")
                        affirmation = await get_daily_affirmation(user_id)
                        if affirmation:
                            affirmation_response = f"<br><br>💝 <strong>Afirmación del día para ti:</strong><br><br>\"{affirmation}\""
                    
                    # Crear saludo personalizado pero seguro
                    if nombre:
                        response = f"¡Hola {nombre}! Me alegra verte de nuevo. ¿Cómo te has sentido desde nuestra última conversación?"
                        if nombre_pareja:
                            response += f" ¿Y cómo ha estado {nombre_pareja}?"
                    else:
                        response = "¡Hola! Me alegra verte de nuevo. ¿Cómo te has sentido desde nuestra última conversación?"
                    
                    response += affirmation_response
                    
                    # Actualizar la fecha de última conversación
                    await save_user_profile(user_id, fecha_ultima_conversacion=datetime.datetime.now())
                    # Translate outbound if needed
                    if original_language in ["en", "ru"]:
                        response = await translate_text(response, original_language)
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
                out_err = "Lo siento, hay problemas de conexión con la base de datos. Por favor, intenta de nuevo en unos momentos."
                if original_language in ["en", "ru"]:
                    out_err = await translate_text(out_err, original_language)
                return {"response": out_err}
            
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
            
            # Si es auto-greeting, usar la nueva lógica para visitas posteriores
            if auto_greeting:
                try:
                    print("[DEBUG] Auto-greeting detected, using new subsequent visit logic...")
                    
                    # Get user profile for personalized greeting
                    user_profile = await get_user_profile(user_id)
                    test_completed = test_results.get("completed", False)
                    attachment_style = test_results.get("style") if test_completed else None
                    
                    # If user has completed test, check if they're premium
                    if test_completed and attachment_style:
                        is_premium = await is_premium_user(user_id)
                        print(f"[DEBUG] User has completed test, is_premium: {is_premium}")
                        
                        # Add daily affirmation
                        affirmation_response = ""
                        if await should_offer_affirmation(user_id):
                            affirmation = await get_daily_affirmation(user_id)
                            if affirmation:
                                affirmation_response = f"<br><br>💝 <strong>Afirmación del día para ti:</strong><br><br>\"{affirmation}\""
                        
                        if is_premium:
                            # Premium user - offer partner test directly
                            partner_offer = await generate_partner_test_offer(user_id, msg.language)
                            await set_state(user_id, "partner_test_offer", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                            response = affirmation_response + "<br><br>" + partner_offer
                        else:
                            # Non-premium user - show paywall
                            paywall_message = await generate_paywall_message(user_id, msg.language)
                            await set_state(user_id, "paywall", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                            response = affirmation_response + "<br><br>" + paywall_message
                        
                        await save_user_profile(user_id, fecha_ultima_conversacion=datetime.datetime.now())
                        
                        # Apply translation if needed
                        if original_language in ["en", "ru"]:
                            response = await translate_text(response, original_language)
                        return {"response": response}
                    
                    # If user hasn't completed test, show basic greeting
                    # Generate personalized greeting with daily affirmation
                    nombre = user_profile.get("nombre") if user_profile else None
                    nombre_pareja = user_profile.get("nombre_pareja") if user_profile else None
                    
                    if msg.language == "en":
                        greeting = f"<p>Hey{f' {nombre}' if nombre else ''}! 😊 Great to see you again!</p>"
                        if nombre_pareja:
                            greeting += f"<p>How are you and {nombre_pareja} doing today?</p>"
                        else:
                            greeting += f"<p>How are you feeling today?</p>"
                    else:  # Spanish
                        greeting = f"<p>¡Hola{f' {nombre}' if nombre else ''}! 😊 ¡Qué gusto verte de nuevo!</p>"
                        if nombre_pareja:
                            greeting += f"<p>¿Cómo están tú y {nombre_pareja} hoy?</p>"
                        else:
                            greeting += f"<p>¿Cómo te sientes hoy?</p>"
                    
                    # Add daily affirmation based on attachment style
                    affirmation_response = ""
                    if attachment_style and await should_offer_affirmation(user_id):
                        print(f"[DEBUG] Offering daily affirmation in auto-greeting to user {user_id}")
                        affirmation = await get_daily_affirmation(user_id)
                        if affirmation:
                            affirmation_response = f"<br><br>💝 <strong>Afirmación del día para ti:</strong><br><br>\"{affirmation}\""
                    
                    # Add follow-up question based on previous conversation
                    follow_up_question = ""
                    if nombre_pareja:
                        if msg.language == "en":
                            follow_up_question = f"<p>How has your relationship with {nombre_pareja} been since we last talked?</p>"
                        else:
                            follow_up_question = f"<p>¿Cómo ha estado tu relación con {nombre_pareja} desde la última vez que hablamos?</p>"
                    else:
                        if msg.language == "en":
                            follow_up_question = "<p>What's been on your mind lately regarding relationships or personal growth?</p>"
                        else:
                            follow_up_question = "<p>¿Qué has estado pensando últimamente sobre relaciones o crecimiento personal?</p>"
                    
                    response = greeting + affirmation_response + follow_up_question
                    
                    await save_user_profile(user_id, fecha_ultima_conversacion=datetime.datetime.now())
                    # Change state to conversation so user can have normal conversations
                    await set_state(user_id, "conversation", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                    
                    # Apply translation if needed
                    if original_language in ["en", "ru"]:
                        response = await translate_text(response, original_language)
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

        # Use pre-translation detection to avoid language mismatches
        if pre_greeting_trigger:
            print(f"[DEBUG] GREETING TRIGGER MATCHED!")
            print(f"[DEBUG] FORCE SHOW INITIAL GREETING (message == '{message}') - resetting state to 'greeting'")
            # Preserve existing test answers when resetting to greeting state
            await set_state(user_id, "greeting", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
            
            # Check if this is first visit, but also check if user completed partner test
            is_first = await is_first_visit(user_id)
            has_completed_partner_test = q1 and q2 and q3 and q4 and q5 and q6 and q7 and q8 and q9 and q10
            
            if is_first and not has_completed_partner_test:
                print(f"[DEBUG] First visit detected - showing new greeting flow")
                response = await generate_first_visit_greeting(user_id, msg.language)
                await save_user_profile(user_id, fecha_ultima_conversacion=datetime.datetime.now())
                if original_language in ["en", "ru"]:
                    response = await translate_text(response, original_language)
                return {"response": response}
            elif has_completed_partner_test:
                print(f"[DEBUG] User completed partner test, moving to conversation")
                await set_state(user_id, "conversation", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                response = "¡Hola! Ya completaste el test de pareja. ¿Sobre qué te gustaría hablar hoy?"
                if original_language in ["en", "ru"]:
                    response = await translate_text(response, original_language)
                return {"response": response}
            
            # Get user context to determine appropriate greeting for returning users
            user_profile = await get_user_profile(user_id)
            history = await load_conversation_history(user_id, limit=20)
            test_completed = test_results.get("completed", False)
            attachment_style = test_results.get("style") if test_completed else None
            
            print(f"[DEBUG] User context - Profile: {bool(user_profile)}, History: {len(history)} messages, Test completed: {test_completed}, Style: {attachment_style}")
            
            # Determine greeting type based on actual user state
            if test_completed and attachment_style:
                # User has completed test - offer insights about their results
                print(f"[DEBUG] User has completed test with style: {attachment_style}")
                style_description = test_results.get("description", "")
                
                # Check if user should be offered a daily affirmation
                affirmation_response = ""
                if await should_offer_affirmation(user_id):
                    print(f"[DEBUG] Offering daily affirmation in test results greeting to user {user_id}")
                    affirmation = await get_daily_affirmation(user_id)
                    if affirmation:
                        affirmation_response = f"<br><br>💝 <strong>Afirmación del día para ti:</strong><br><br>\"{affirmation}\""
                
                if msg.language == "en":
                    if attachment_style == "secure":
                        response = (
                            f"<p>Hey there! 😊 I'm <strong>Eldric</strong>, your emotional coach!</p>"
                            f"<p>I see you've already taken the attachment style test and discovered you have a <strong>{attachment_style}</strong> style. {style_description}</p>"
                            f"<p>This is really valuable insight! Understanding your attachment style can help you navigate relationships more effectively.</p>"
                            f"{affirmation_response}"
                            f"<p><strong>To help you better:</strong> If you tell me more about your age, gender, and relationship status, I'll be able to provide more tailored content and advice for your specific situation.</p>"
                            f"<p>What would you like to explore today? We could dive deeper into your attachment style, chat about your relationships, or work on anything else that's on your mind.</p>"
                        )
                    else:  # avoidant, anxious, or disorganized
                        response = (
                            f"<p>Hey there! 😊 I'm <strong>Eldric</strong>, your emotional coach!</p>"
                            f"<p>I see you've already taken the attachment style test and discovered you have a <strong>{attachment_style}</strong> style. {style_description}</p>"
                            f"<p>This is really valuable insight! Understanding your attachment style can help you navigate relationships more effectively.</p>"
                            f"<p><strong>Here's something important to know:</strong> Attachment styles are fluid and can change with awareness and work. The goal is to develop what we call 'earned secure attachment' - where you can maintain the healthy aspects of your current style while developing more secure patterns.</p>"
                            f"<p>The first step is acknowledging your current patterns, which you've already done by taking the test. Now we can start working together to help you move toward more secure attachment.</p>"
                            f"{affirmation_response}"
                            f"<p><strong>To help you better:</strong> If you tell me more about your age, gender, and relationship status, I'll be able to provide more tailored content and advice for your specific situation.</p>"
                            f"<p>What would you like to explore today? We could dive deeper into your attachment style, work on developing more secure patterns, chat about your relationships, or work on anything else that's on your mind.</p>"
                        )
                else:  # Spanish
                    if attachment_style == "secure":
                        response = (
                            f"<p>¡Hola! 😊 Soy <strong>Eldric</strong>, tu coach emocional.</p>"
                            f"<p>Veo que ya has hecho el test de estilos de apego y descubriste que tienes un estilo <strong>{attachment_style}</strong>. {style_description}</p>"
                            f"<p>¡Esto es muy valioso! Entender tu estilo de apego puede ayudarte a navegar las relaciones de manera más efectiva.</p>"
                            f"{affirmation_response}"
                            f"<p><strong>Para ayudarte mejor:</strong> Si me cuentas más sobre tu edad, género y estado de relación, podré ofrecerte contenido y consejos más personalizados para tu situación específica.</p>"
                            f"<p>¿Qué te gustaría explorar hoy? Podríamos profundizar en tu estilo de apego, charlar sobre tus relaciones, o trabajar en cualquier otra cosa que tengas en mente.</p>"
                        )
                    else:  # avoidant, anxious, or disorganized
                        response = (
                            f"<p>¡Hola! 😊 Soy <strong>Eldric</strong>, tu coach emocional.</p>"
                            f"<p>Veo que ya has hecho el test de estilos de apego y descubriste que tienes un estilo <strong>{attachment_style}</strong>. {style_description}</p>"
                            f"<p>¡Esto es muy valioso! Entender tu estilo de apego puede ayudarte a navegar las relaciones de manera más efectiva.</p>"
                            f"<p><strong>Algo importante que debes saber:</strong> Los estilos de apego son fluidos y pueden cambiar con conciencia y trabajo. El objetivo es desarrollar lo que llamamos 'apego seguro ganado' - donde puedes mantener los aspectos saludables de tu estilo actual mientras desarrollas patrones más seguros.</p>"
                            f"<p>El primer paso es reconocer tus patrones actuales, lo cual ya has hecho al tomar el test. Ahora podemos empezar a trabajar juntos para ayudarte a avanzar hacia un apego más seguro.</p>"
                            f"{affirmation_response}"
                            f"<p><strong>Para ayudarte mejor:</strong> Si me cuentas más sobre tu edad, género y estado de relación, podré ofrecerte contenido y consejos más personalizados para tu situación específica.</p>"
                            f"<p>¿Qué te gustaría explorar hoy? Podríamos profundizar en tu estilo de apego, trabajar en desarrollar patrones más seguros, charlar sobre tus relaciones, o trabajar en cualquier otra cosa que tengas en mente.</p>"
                        )
                
            elif history and len(history) > 2:
                # User has conversation history but no test - check for meaningful conversation
                has_meaningful_conversation = any(
                    msg.get('content', '').lower() not in ['saludo inicial', 'hola', 'hi', 'hello', 'initial greeting'] 
                    for msg in history
                )
                
                if has_meaningful_conversation:
                    print(f"[DEBUG] User has meaningful conversation history but no test")
                    nombre = user_profile.get("nombre") if user_profile else None
                    
                    if msg.language == "en":
                        response = (
                            f"<p>Hey{f' {nombre}' if nombre else ''}! 😊 Great to see you again!</p>"
                            f"<p>I remember we've chatted before, and I'd love to continue our conversation. How have you been feeling lately?</p>"
                            f"<p>If you're interested, I could also guide you through the attachment style test to help you understand your relationship patterns better.</p>"
                        )
                    else:  # Spanish
                        response = (
                            f"<p>¡Hola{f' {nombre}' if nombre else ''}! 😊 ¡Qué gusto verte de nuevo!</p>"
                            f"<p>Recuerdo que hemos charlado antes, y me encantaría continuar nuestra conversación. ¿Cómo te has sentido últimamente?</p>"
                            f"<p>Si te interesa, también podría guiarte a través del test de estilos de apego para ayudarte a entender mejor tus patrones de relación.</p>"
                        )
                else:
                    # User has history but only greetings - treat as new user
                    print(f"[DEBUG] User has history but only greetings - treating as new user")
                    if msg.language == "en":
                        response = (
                            "<p>Hey there! 😊 I'm <strong>Eldric</strong>, and I'm really excited to meet you! I'm here to chat about relationships and help you understand yourself better.</p>"
                            "<p>You know how we all have different ways of connecting with people? Well, there are basically four main styles: <strong>secure, anxious, avoidant, and fearful avoidant</strong>. It's pretty fascinating stuff!</p>"
                            "<p>I'd love to get to know you better. What sounds good to you?</p>"
                            "<ul>"
                            "<li>a) I'm curious about my relationship style - let's do the test!</li>"
                            "<li>b) I'd rather chat about what's on my mind right now.</li>"
                            "<li>c) Tell me more about these attachment styles first.</li>"
                            "</ul>"
                        )
                    else:  # Spanish
                        response = (
                            "<p>¡Hola! 😊 Soy <strong>Eldric</strong>, y estoy muy emocionado de conocerte. Estoy aquí para charlar sobre relaciones y ayudarte a entenderte mejor.</p>"
                            "<p>¿Sabes cómo todos tenemos diferentes formas de conectarnos con las personas? Bueno, básicamente hay cuatro estilos principales: <strong>seguro, ansioso, evitativo y desorganizado</strong>. ¡Es algo bastante fascinante!</p>"
                            "<p>Me encantaría conocerte mejor. ¿Qué te parece bien?</p>"
                            "<ul>"
                            "<li>a) Tengo curiosidad por mi estilo de relación - ¡hagamos el test!</li>"
                            "<li>b) Prefiero charlar de lo que tengo en mente ahora mismo.</li>"
                            "<li>c) Cuéntame más sobre estos estilos de apego primero.</li>"
                            "</ul>"
                        )
            else:
                # New user - no history, no test
                print(f"[DEBUG] New user - no history, no test")
                if msg.language == "en":
                    response = (
                        "<p>Hey there! 😊 I'm <strong>Eldric</strong>, and I'm really excited to meet you! I'm here to chat about relationships and help you understand yourself better.</p>"
                        "<p>You know how we all have different ways of connecting with people? Well, there are basically four main styles: <strong>secure, anxious, avoidant, and fearful avoidant</strong>. It's pretty fascinating stuff!</p>"
                        "<p>I'd love to get to know you better. What sounds good to you?</p>"
                        "<ul>"
                        "<li>a) I'm curious about my relationship style - let's do the test!</li>"
                        "<li>b) I'd rather chat about what's on my mind right now.</li>"
                        "<li>c) Tell me more about these attachment styles first.</li>"
                        "</ul>"
                    )
                else:  # Spanish
                    response = (
                        "<p>¡Hola! 😊 Soy <strong>Eldric</strong>, y estoy muy emocionado de conocerte. Estoy aquí para charlar sobre relaciones y ayudarte a entenderte mejor.</p>"
                        "<p>¿Sabes cómo todos tenemos diferentes formas de conectarnos con las personas? Bueno, básicamente hay cuatro estilos principales: <strong>seguro, ansioso, evitativo y desorganizado</strong>. ¡Es algo bastante fascinante!</p>"
                        "<p>Me encantaría conocerte mejor. ¿Qué te parece bien?</p>"
                        "<ul>"
                        "<li>a) Tengo curiosidad por mi estilo de relación - ¡hagamos el test!</li>"
                        "<li>b) Prefiero charlar de lo que tengo en mente ahora mismo.</li>"
                        "<li>c) Cuéntame más sobre estos estilos de apego primero.</li>"
                        "</ul>"
                    )
            
            # Update conversation date for returning users
            if history and len(history) > 0:
                await save_user_profile(user_id, fecha_ultima_conversacion=datetime.datetime.now())
            
            print(f"[DEBUG] Set initial greeting response (accurate): {response[:100]}...")
            if original_language in ["en", "ru"]:
                response = await translate_text(response, original_language)
            return {"response": response}
        # Always handle test triggers as a hard reset to test start (but not greeting triggers)
        test_triggers = ["test", "quiero hacer el test", "hacer test", "start test", "quiero hacer el test", "quiero hacer test", "hacer el test"]
        greeting_triggers_list = list(greeting_triggers.values())
        # Prefer pre-detected test trigger (before translation) to avoid mismatches
        if pre_test_trigger and not pre_greeting_trigger:
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
            if original_language in ["en", "ru"]:
                response = await translate_text(response, original_language)
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
                # Start conversation and ask for personal information
                await set_state(user_id, "collecting_personal_info", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                response = await generate_personal_questions_prompt(user_id, msg.language)
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
                # Immediately append PDF notification and paywall after results
                pdf_notification = await generate_pdf_notification(user_id, msg.language)
                paywall_message = await generate_paywall_message(user_id, msg.language)
                full_response = response + pdf_notification + "<br><br>" + paywall_message

                # Move directly to paywall state to capture A/B choice
                print(f"[DEBUG] Moving to paywall state immediately after results")
                await set_state(user_id, "paywall", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, selected_option['text'])

                if original_language in ["en", "ru"]:
                    full_response = await translate_text(full_response, original_language)
                return {"response": full_response}
        
        # Handle partner test questions (partner_q1, partner_q2, etc.)
        elif state in [f"partner_q{i}" for i in range(1, 11)] and message.upper() in ["A", "B", "C", "D"]:
            print(f"[DEBUG] ENTERED: partner test question state {state} with choice {message.upper()}")
            
            questions = PARTNER_TEST_QUESTIONS.get(msg.language, PARTNER_TEST_QUESTIONS["es"])
            current_question_index = int(state.split("_")[1][1:]) - 1  # partner_q1 -> 0, partner_q2 -> 1, etc.
            current_question = questions[current_question_index]
            
            # Get the selected option and its scores
            option_index = ord(message.upper()) - ord('A')  # A->0, B->1, C->2, D->3
            selected_option = current_question['options'][option_index]
            
            # Store partner answer in the state (we'll use q1-q10 to store partner answers)
            partner_answers = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]
            partner_answers[current_question_index] = selected_option['text']
            
            next_state = f"partner_q{current_question_index + 2}"
            if current_question_index < len(questions) - 1:
                # Continue to next question
                if msg.language == "en":
                    response = f"<p><strong>Partner Test - Question {current_question_index + 2} of 10:</strong> {questions[current_question_index + 1]['question']}</p><ul>"
                else:  # Spanish
                    response = f"<p><strong>Test de Pareja - Pregunta {current_question_index + 2} de 10:</strong> {questions[current_question_index + 1]['question']}</p><ul>"
                
                for i, option in enumerate(questions[current_question_index + 1]['options']):
                    response += f"<li>{option['text']}</li>"
                response += "</ul>"
                
                await set_state(user_id, next_state, None, partner_answers[0], partner_answers[1], partner_answers[2], partner_answers[3], partner_answers[4], partner_answers[5], partner_answers[6], partner_answers[7], partner_answers[8], partner_answers[9])
            else:
                # Partner test completed - calculate partner's style from all answers
                partner_scores = {"anxious": 0, "avoidant": 0, "secure": 0, "desorganizado": 0}
                
                # Calculate scores from all partner answers
                for i, answer_text in enumerate(partner_answers):
                    if answer_text:  # Make sure we have an answer
                        # Find the matching option and add its scores
                        for option in questions[i]['options']:
                            if option['text'] == answer_text:
                                for style, score in option['scores'].items():
                                    partner_scores[style] += score
                                break
                
                # Calculate partner's attachment style
                partner_style = calculate_attachment_style(partner_scores)
                
                print(f"[DEBUG] Partner test completed - Partner scores: {partner_scores}")
                print(f"[DEBUG] Partner style calculated: {partner_style}")
                
                # Get user's style
                user_profile = await get_user_profile(user_id)
                user_style = user_profile.get("attachment_style") if user_profile else None
                
                # Calculate relationship status
                print(f"[DEBUG] Calculating relationship status - User style: '{user_style}', Partner style: '{partner_style}'")
                relationship_status = calculate_relationship_status(user_style, partner_style)
                print(f"[DEBUG] Relationship status calculated: '{relationship_status}'")
                relationship_description = get_relationship_description(relationship_status, msg.language)
                print(f"[DEBUG] Relationship description: '{relationship_description}'")
                
                # Save partner information
                await save_user_profile(user_id, 
                    partner_attachment_style=partner_style,
                    relationship_status=relationship_status
                )
                
                # Generate response with partner test results
                if msg.language == "en":
                    response = (
                        f"<p>Great! I've analyzed your partner's responses. Based on the patterns I observed, your partner appears to have a <strong>{partner_style}</strong> attachment style.</p>"
                        f"<p><strong>Your relationship dynamic:</strong> {relationship_description}</p>"
                        f"<p>This combination can help us understand how you both interact and what might be causing any challenges in your relationship.</p>"
                    )
                else:  # Spanish
                    response = (
                        f"<p>¡Excelente! He analizado las respuestas de tu pareja. Basándome en los patrones que observé, tu pareja parece tener un estilo de apego <strong>{partner_style}</strong>.</p>"
                        f"<p><strong>La dinámica de tu relación:</strong> {relationship_description}</p>"
                        f"<p>Esta combinación puede ayudarnos a entender cómo interactúan ambos y qué podría estar causando desafíos en tu relación.</p>"
                    )
                
                # Add PDF notification and daily affirmation
                pdf_notification = await generate_pdf_notification(user_id, msg.language)
                affirmation_response = ""
                if await should_offer_affirmation(user_id):
                    affirmation = await get_daily_affirmation(user_id)
                    if affirmation:
                        affirmation_response = f"<br><br>💝 <strong>Afirmación del día para ti:</strong><br><br>\"{affirmation}\""
                
                response += pdf_notification + affirmation_response
                
                # Move to conversation state
                await set_state(user_id, "conversation", None, partner_answers[0], partner_answers[1], partner_answers[2], partner_answers[3], partner_answers[4], partner_answers[5], partner_answers[6], partner_answers[7], partner_answers[8], partner_answers[9])
            
            if original_language in ["en", "ru"]:
                response = await translate_text(response, original_language)
            return {"response": response}
        # Handle collecting personal information
        elif state == "collecting_personal_info":
            print(f"[DEBUG] ENTERED: collecting_personal_info state")
            print(f"[DEBUG] User message: '{message}'")
            
            # Parse personal information from user message
            user_profile = await get_user_profile(user_id)
            nombre, edad, tiene_pareja, nombre_pareja = None, None, None, None
            
            # Extract name
            m = re.search(r"me llamo ([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9]+)", message, re.IGNORECASE)
            if not m:
                m = re.search(r"soy ([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9]+)", message, re.IGNORECASE)
            if m:
                nombre = m.group(1)
            
            # Extract age
            m = re.search(r"tengo (\d+)", message, re.IGNORECASE)
            if not m:
                m = re.search(r"(\d+) años", message, re.IGNORECASE)
            if m:
                edad = int(m.group(1))
            
            # Extract partner information
            if re.search(r"tengo pareja|estoy en una relación|tengo novio|tengo novia", message, re.IGNORECASE):
                tiene_pareja = True
                # Try to extract partner name
                m = re.search(r"se llama ([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9]+)", message, re.IGNORECASE)
                if m:
                    nombre_pareja = m.group(1)
            elif re.search(r"no tengo pareja|no estoy en una relación|soltero|soltera", message, re.IGNORECASE):
                tiene_pareja = False
            
            # Save personal information
            if nombre or edad is not None or tiene_pareja is not None or nombre_pareja:
                await save_user_profile(user_id, nombre=nombre, edad=edad, tiene_pareja=tiene_pareja, nombre_pareja=nombre_pareja)
                print(f"[DEBUG] Saved personal info: nombre={nombre}, edad={edad}, tiene_pareja={tiene_pareja}, nombre_pareja={nombre_pareja}")
            
            # Check if we have enough information or if user wants to continue
            if nombre and edad is not None and tiene_pareja is not None:
                # We have all basic info, move to conversation
                await set_state(user_id, "conversation", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                response = "¡Perfecto! Ya tengo toda la información que necesito. ¿Sobre qué te gustaría hablar hoy?"
            else:
                # Still need more information
                response = await generate_personal_questions_prompt(user_id, msg.language)
            
            if original_language in ["en", "ru"]:
                response = await translate_text(response, original_language)
            return {"response": response}
        
        # Handle paywall
        elif state == "paywall" and message.upper() in ["A", "B"]:
            print(f"[DEBUG] ENTERED: paywall state with choice {message.upper()}")
            if message.upper() == "A":
                # User wants to pay - mark as premium and continue to partner test offer
                # TODO: Integrate with Stripe or payment processor
                await set_premium_user(user_id, True)
                partner_offer = await generate_partner_test_offer(user_id, msg.language)
                await set_state(user_id, "partner_test_offer", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                response = "¡Perfecto! Ahora tienes acceso a todas las funciones premium. " + partner_offer
            else:  # B - Skip payment
                # Move to basic conversation without premium features
                await set_state(user_id, "conversation", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                response = "Entendido. Puedes continuar con el chat básico. Si cambias de opinión, siempre puedes acceder a las funciones premium más tarde. ¿Sobre qué te gustaría hablar?"
            
            if original_language in ["en", "ru"]:
                response = await translate_text(response, original_language)
            return {"response": response}
        
        # Handle partner test offer
        elif state == "partner_test_offer":
            # Check if user already completed partner test (all q1-q10 have answers)
            if q1 and q2 and q3 and q4 and q5 and q6 and q7 and q8 and q9 and q10:
                print(f"[DEBUG] User already completed partner test, moving to conversation")
                await set_state(user_id, "conversation", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                response = "¡Perfecto! Ya completaste el test de pareja. ¿Sobre qué te gustaría hablar?"
                if original_language in ["en", "ru"]:
                    response = await translate_text(response, original_language)
                return {"response": response}
            
            # Handle partner test offer choices
            if message.upper() in ["A", "B", "C"]:
                print(f"[DEBUG] ENTERED: partner_test_offer state with choice {message.upper()}")
                if message.upper() == "A":
                    # Start partner test
                    await set_state(user_id, "partner_q1", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                    questions = PARTNER_TEST_QUESTIONS.get(msg.language, PARTNER_TEST_QUESTIONS["es"])
                    question = questions[0]
                    
                    if msg.language == "en":
                        response = f"<p><strong>Partner Test - Question 1 of 10:</strong> {question['question']}</p><ul>"
                    else:  # Spanish
                        response = f"<p><strong>Test de Pareja - Pregunta 1 de 10:</strong> {question['question']}</p><ul>"
                    
                    for i, option in enumerate(question['options']):
                        response += f"<li>{option['text']}</li>"
                    response += "</ul>"
                elif message.upper() == "B":
                    # Has partner but skip test, save info and move to personal questions
                    await save_user_profile(user_id, tiene_pareja=True)
                    await set_state(user_id, "collecting_personal_info", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                    personal_prompt = await generate_personal_questions_prompt(user_id, msg.language)
                    response = "Entendido. " + personal_prompt
                else:  # C - No partner
                    # No partner, save info and move to personal questions
                    await save_user_profile(user_id, tiene_pareja=False)
                    await set_state(user_id, "collecting_personal_info", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                    personal_prompt = await generate_personal_questions_prompt(user_id, msg.language)
                    response = "Entendido. " + personal_prompt
                
                if original_language in ["en", "ru"]:
                    response = await translate_text(response, original_language)
                return {"response": response}
            else:
                # User sent text message instead of A/B/C choice
                print(f"[DEBUG] User sent text message in partner_test_offer state: '{message}'")
                # Move to conversation state to handle the text message
                await set_state(user_id, "conversation", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
                # Continue to conversation logic below
        
        # Handle post-test conversation (user just finished test)
        elif state == "post_test":
            print(f"[DEBUG] ENTERED: post_test state - user just finished test")
            print(f"[DEBUG] User message: '{message}'")
            
            # Add daily affirmation and PDF notification
            affirmation_response = ""
            if await should_offer_affirmation(user_id):
                affirmation = await get_daily_affirmation(user_id)
                if affirmation:
                    affirmation_response = f"<br><br>💝 <strong>Afirmación del día para ti:</strong><br><br>\"{affirmation}\""
            
            pdf_notification = await generate_pdf_notification(user_id, msg.language)
            
            # Show paywall before offering partner test
            paywall_message = await generate_paywall_message(user_id, msg.language)
            await set_state(user_id, "paywall", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
            response = pdf_notification + affirmation_response + "<br><br>" + paywall_message
            
            if original_language in ["en", "ru"]:
                response = await translate_text(response, original_language)
            return {"response": response}
        # Handle questions about test results - transition to conversation state
        elif state == "greeting" and any(keyword in message.lower() for keyword in ["resultados", "resultado", "test", "prueba", "estilo de apego", "apego", "recuerdas", "respuestas"]):
            print(f"[DEBUG] User asking about test results from greeting state, transitioning to conversation")
            await set_state(user_id, "conversation", None, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10)
            # Continue to conversation logic below
            
        # Handle normal conversation with knowledge injection
        elif state == "conversation" or state is None:
            print(f"[DEBUG] ENTERED: normal conversation (state == 'conversation' or state is None)")
            print(f"[DEBUG] This should NOT happen for first message with 'saludo inicial'")
            
            # Check if user should be offered a daily affirmation
            if await should_offer_affirmation(user_id):
                print(f"[DEBUG] Offering daily affirmation to user {user_id}")
                affirmation = await get_daily_affirmation(user_id)
                if affirmation:
                    response = f"💝 <strong>Afirmación del día para ti:</strong><br><br>\"{affirmation}\"<br><br>¿Te gustaría reflexionar sobre esta afirmación o prefieres que hablemos de otra cosa?"
            if original_language in ["en", "ru"]:
                response = await translate_text(response, original_language)
            return {"response": response}
            
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
            # Always include self and partner results in prompt context
            user_profile = await get_user_profile(user_id)
            partner_style = user_profile.get("partner_attachment_style") if user_profile else None
            relationship_status = user_profile.get("relationship_status") if user_profile else None
            relationship_description = get_relationship_description(relationship_status, msg.language) if relationship_status else ""

            results_summary = ""
            if test_results.get("completed"):
                results_summary += f"\n\n[RESULTADOS USUARIO]\nEstilo: {test_results['style']}\nDescripcion: {test_results.get('description','')}\n"
            if partner_style:
                results_summary += f"\n\n[RESULTADOS PAREJA]\nEstilo pareja: {partner_style}\nEstado relacion: {relationship_status}\nDescripcion: {relationship_description}\n"

            keywords = extract_keywords(message, msg.language)
            print(f"[DEBUG] Message: '{message}'")
            print(f"[DEBUG] Language: {msg.language}")
            print(f"[DEBUG] Extracted keywords: {keywords}")
            
            relevant_knowledge = await get_relevant_knowledge(keywords, msg.language, msg.user_id)
            print(f"[DEBUG] Knowledge found: {len(relevant_knowledge)} characters")
            print(f"[DEBUG] Knowledge content: {relevant_knowledge}")
            
            # Inject knowledge, results, and full snapshot into the prompt
            snapshot_str = "\n\n[USER SNAPSHOT]\n" + json.dumps(full_snapshot, default=str)[:4000]
            enhanced_prompt = inject_knowledge_into_prompt(current_prompt, relevant_knowledge + test_context + results_summary + snapshot_str)
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
        if original_language in ["en", "ru"]:
            response = await translate_text(response, original_language)
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
            content_length = len(content) if content else 0
            
            # Check if adding this message would exceed our limit
            if total_content_length + content_length > max_total_content:
                print(f"[DEBUG] Stopping history load at {len(messages)} messages due to content length limit")
                break
            
            messages.append({
                "role": row["role"],
                "content": content or ""
            })
            total_content_length += content_length
        
        print(f"[DEBUG] Loaded {len(messages)} conversation messages for user {user_id} (total content: {total_content_length} chars)")
        return messages
    except Exception as e:
        print(f"[DEBUG] Error loading conversation history: {e}")
        return []

# Funciones para guardar y recuperar datos personales del usuario
async def save_user_profile(user_id, nombre=None, edad=None, tiene_pareja=None, nombre_pareja=None, tiempo_pareja=None, estado_emocional=None, estado_relacion=None, opinion_apego=None, fecha_ultima_conversacion=None, fecha_ultima_mencion_pareja=None, attachment_style=None, partner_attachment_style=None, relationship_status=None, fecha_ultima_afirmacion=None, afirmacion_anxious=None, afirmacion_avoidant=None, afirmacion_secure=None, afirmacion_disorganized=None):
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
        "attachment_style": attachment_style,
        "partner_attachment_style": partner_attachment_style,
        "relationship_status": relationship_status,
        "fecha_ultima_afirmacion": fecha_ultima_afirmacion,
        "afirmacion_anxious": afirmacion_anxious,
        "afirmacion_avoidant": afirmacion_avoidant,
        "afirmacion_secure": afirmacion_secure,
        "afirmacion_disorganized": afirmacion_disorganized
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
                attachment_style = COALESCE(:attachment_style, attachment_style),
                partner_attachment_style = COALESCE(:partner_attachment_style, partner_attachment_style),
                relationship_status = COALESCE(:relationship_status, relationship_status),
                fecha_ultima_afirmacion = COALESCE(:fecha_ultima_afirmacion, fecha_ultima_afirmacion),
                afirmacion_anxious = COALESCE(:afirmacion_anxious, afirmacion_anxious),
                afirmacion_avoidant = COALESCE(:afirmacion_avoidant, afirmacion_avoidant),
                afirmacion_secure = COALESCE(:afirmacion_secure, afirmacion_secure),
                afirmacion_disorganized = COALESCE(:afirmacion_disorganized, afirmacion_disorganized)
            WHERE user_id = :user_id
        """, values)
    else:
        # Insert
        await database.execute("""
            INSERT INTO user_profile (user_id, nombre, edad, tiene_pareja, nombre_pareja, tiempo_pareja, estado_emocional, estado_relacion, opinion_apego, fecha_ultima_conversacion, fecha_ultima_mencion_pareja, attachment_style, partner_attachment_style, relationship_status, fecha_ultima_afirmacion, afirmacion_anxious, afirmacion_avoidant, afirmacion_secure, afirmacion_disorganized)
            VALUES (:user_id, :nombre, :edad, :tiene_pareja, :nombre_pareja, :tiempo_pareja, :estado_emocional, :estado_relacion, :opinion_apego, :fecha_ultima_conversacion, :fecha_ultima_mencion_pareja, :attachment_style, :partner_attachment_style, :relationship_status, :fecha_ultima_afirmacion, :afirmacion_anxious, :afirmacion_avoidant, :afirmacion_secure, :afirmacion_disorganized)
        """, values)
    return True

async def generate_first_visit_greeting(user_id, language="es"):
    """Generate greeting for first visit with test/chat options and daily affirmation for secure"""
    if language == "en":
        greeting = (
            "<p>Hey there! 😊 Welcome! I'm Eldric, your emotional coach and relationship expert.</p>"
            "<p>I'm here to help you understand your attachment style and improve your relationships. I can offer you two ways to get started:</p>"
            "<p><strong>A) Take the attachment style test</strong> - Discover your relationship patterns and get personalized insights</p>"
            "<p><strong>B) Just chat</strong> - Tell me what's on your mind and we can talk about anything relationship-related</p>"
            "<p>What would you like to do?</p>"
        )
        
        # Add daily affirmation for secure attachment style
        affirmation = "You are worthy of love and connection. Your feelings matter and you deserve to be heard and understood."
        greeting += f"<br><br>💝 <strong>Daily affirmation for you:</strong><br><br>\"{affirmation}\""
        
    else:  # Spanish
        greeting = (
            "<p>¡Hola! 😊 ¡Bienvenido/a! Soy Eldric, tu coach emocional y experto en relaciones.</p>"
            "<p>Estoy aquí para ayudarte a entender tu estilo de apego y mejorar tus relaciones. Te puedo ofrecer dos formas de empezar:</p>"
            "<p><strong>A) Hacer el test de estilos de apego</strong> - Descubre tus patrones de relación y obtén insights personalizados</p>"
            "<p><strong>B) Solo charlar</strong> - Cuéntame qué tienes en mente y podemos hablar de cualquier cosa relacionada con relaciones</p>"
            "<p>¿Qué te gustaría hacer?</p>"
        )
        
        # Add daily affirmation for secure attachment style
        affirmation = "Eres digno/a de amor y conexión. Tus sentimientos importan y mereces ser escuchado/a y comprendido/a."
        greeting += f"<br><br>💝 <strong>Afirmación del día para ti:</strong><br><br>\"{affirmation}\""
    
    return greeting

async def generate_personal_questions_prompt(user_id, language="es"):
    """Generate prompt to collect personal information after test or chat"""
    user_profile = await get_user_profile(user_id)
    
    # Check what information we already have
    has_name = bool(user_profile and user_profile.get("nombre"))
    has_age = bool(user_profile and user_profile.get("edad"))
    has_partner_info = bool(user_profile and user_profile.get("tiene_pareja") is not None)
    
    if language == "en":
        prompt = "<p>Great! Now I'd love to get to know you better so I can provide more personalized support. Could you tell me:</p>"
        
        if not has_name:
            prompt += "<p>• What's your name?</p>"
        if not has_age:
            prompt += "<p>• How old are you?</p>"
        if not has_partner_info:
            prompt += "<p>• Do you have a partner or are you in a relationship?</p>"
        
        prompt += "<p>This information helps me tailor my advice to your specific situation. Feel free to share as much or as little as you're comfortable with!</p>"
        
    else:  # Spanish
        prompt = "<p>¡Perfecto! Ahora me gustaría conocerte mejor para poder ofrecerte un apoyo más personalizado. ¿Podrías contarme:</p>"
        
        if not has_name:
            prompt += "<p>• ¿Cómo te llamas?</p>"
        if not has_age:
            prompt += "<p>• ¿Cuántos años tienes?</p>"
        if not has_partner_info:
            prompt += "<p>• ¿Tienes pareja o estás en una relación?</p>"
        
        prompt += "<p>Esta información me ayuda a adaptar mis consejos a tu situación específica. ¡Comparte lo que te sientas cómodo/a compartiendo!</p>"
    
    return prompt

async def generate_paywall_message(user_id, language="es"):
    """Generate paywall message to unlock partner test and premium features"""
    if language == "en":
        message = (
            "<p>🎉 <strong>Congratulations on completing your attachment style test!</strong></p>"
            "<p>You've just unlocked valuable insights about yourself. Now, would you like to take your relationship understanding to the next level?</p>"
            "<p><strong>💎 Premium Features Available:</strong></p>"
            "<ul>"
            "<li>🔍 <strong>Partner Attachment Test</strong> - Understand your partner's style and relationship dynamics</li>"
            "<li>📊 <strong>Detailed Relationship Analysis</strong> - Get personalized insights for your specific combination</li>"
            "<li>💝 <strong>Daily Personalized Affirmations</strong> - Tailored to your attachment style</li>"
            "<li>📧 <strong>PDF Reports</strong> - Downloadable insights you can reference anytime</li>"
            "<li>💬 <strong>Unlimited Chat</strong> - Get personalized advice whenever you need it</li>"
            "</ul>"
            "<p><strong>💰 Special Launch Price: Only $9.99 (Regular $19.99)</strong></p>"
            "<p><strong>A) Yes, I want to unlock premium features - $9.99</strong></p>"
            "<p><strong>B) Maybe later, let's continue with basic chat</strong></p>"
            "<p>What would you like to do?</p>"
        )
    else:  # Spanish
        message = (
            "<p>🎉 <strong>¡Felicidades por completar tu test de estilo de apego!</strong></p>"
            "<p>Acabas de desbloquear información valiosa sobre ti mismo/a. ¿Te gustaría llevar tu comprensión de las relaciones al siguiente nivel?</p>"
            "<p><strong>💎 Funciones Premium Disponibles:</strong></p>"
            "<ul>"
            "<li>🔍 <strong>Test de Apego de Pareja</strong> - Entiende el estilo de tu pareja y las dinámicas de relación</li>"
            "<li>📊 <strong>Análisis Detallado de Relación</strong> - Obtén insights personalizados para tu combinación específica</li>"
            "<li>💝 <strong>Afirmaciones Diarias Personalizadas</strong> - Adaptadas a tu estilo de apego</li>"
            "<li>📧 <strong>Reportes PDF</strong> - Insights descargables que puedes consultar cuando quieras</li>"
            "<li>💬 <strong>Chat Ilimitado</strong> - Recibe consejos personalizados cuando los necesites</li>"
            "</ul>"
            "<p><strong>💰 Precio de Lanzamiento Especial: Solo $9.99 (Precio Regular $19.99)</strong></p>"
            "<p><strong>A) Sí, quiero desbloquear las funciones premium - $9.99</strong></p>"
            "<p><strong>B) Tal vez después, sigamos con el chat básico</strong></p>"
            "<p>¿Qué te gustaría hacer?</p>"
        )
    
    return message

async def generate_partner_test_offer(user_id, language="es"):
    """Generate offer for partner test - ask if user has a partner"""
    if language == "en":
        offer = (
            "<p>Now that we understand your attachment style, I'd like to ask: <strong>Do you currently have a romantic partner?</strong></p>"
            "<p>If you do, I can offer you a test to understand your partner's attachment style as well. This can help us understand your relationship dynamics better and provide more targeted advice for both of you.</p>"
            "<p><strong>A) Yes, I have a partner and would like to take the partner test</strong></p>"
            "<p><strong>B) I have a partner but don't want to take the test right now</strong></p>"
            "<p><strong>C) I don't have a partner currently</strong></p>"
            "<p>What would you prefer?</p>"
        )
    else:  # Spanish
        offer = (
            "<p>Ahora que entendemos tu estilo de apego, me gustaría preguntarte: <strong>¿Tienes actualmente una pareja romántica?</strong></p>"
            "<p>Si la tienes, puedo ofrecerte un test para entender también el estilo de apego de tu pareja. Esto puede ayudarnos a entender mejor las dinámicas de tu relación y ofrecer consejos más específicos para ambos.</p>"
            "<p><strong>A) Sí, tengo pareja y me gustaría hacer el test de pareja</strong></p>"
            "<p><strong>B) Tengo pareja pero no quiero hacer el test ahora</strong></p>"
            "<p><strong>C) No tengo pareja actualmente</strong></p>"
            "<p>¿Qué prefieres?</p>"
        )
    
    return offer

async def generate_pdf_notification(user_id, language="es"):
    """Generate notification about PDF being sent to email"""
    # Check if user's email is verified
    email_verified = await is_email_verified(user_id)
    
    if not email_verified:
        if language == "en":
            notification = (
                "<p>📧 <strong>To receive your PDF report:</strong> Please verify your email address first.</p>"
                "<p>I'll send you a detailed report with your test results and personalized insights once your email is verified.</p>"
                "<p>This helps ensure the report reaches the right person and maintains your privacy.</p>"
            )
        else:  # Spanish
            notification = (
                "<p>📧 <strong>Para recibir tu reporte PDF:</strong> Por favor verifica tu dirección de email primero.</p>"
                "<p>Te enviaré un reporte detallado con tus resultados del test e insights personalizados una vez que verifiques tu email.</p>"
                "<p>Esto ayuda a asegurar que el reporte llegue a la persona correcta y mantenga tu privacidad.</p>"
            )
    else:
        # Actually send the PDF email
        pdf_sent = await send_pdf_by_email(user_id, language=language)
        
        if pdf_sent:
            if language == "en":
                notification = (
                    "<p>📧 <strong>Great news!</strong> I've sent a detailed PDF report with your test results and personalized insights to your email address.</p>"
                    "<p>This report includes your attachment style analysis, relationship dynamics (if you took the partner test), and actionable tips for improving your relationships.</p>"
                    "<p>You can refer to it anytime for guidance and share it with your partner if you'd like!</p>"
                )
            else:  # Spanish
                notification = (
                    "<p>📧 <strong>¡Excelentes noticias!</strong> He enviado un reporte PDF detallado con tus resultados del test e insights personalizados a tu dirección de email.</p>"
                    "<p>Este reporte incluye tu análisis de estilo de apego, dinámicas de relación (si hiciste el test de pareja), y consejos prácticos para mejorar tus relaciones.</p>"
                    "<p>¡Puedes consultarlo cuando quieras para orientación y compartirlo con tu pareja si te apetece!</p>"
                )
        else:
            if language == "en":
                notification = (
                    "<p>📧 <strong>I tried to send your PDF report</strong> but encountered a technical issue.</p>"
                    "<p>Don't worry! Your results are saved and I can try sending it again later. You can also access your information anytime through our chat.</p>"
                )
            else:  # Spanish
                notification = (
                    "<p>📧 <strong>Intenté enviar tu reporte PDF</strong> pero encontré un problema técnico.</p>"
                    "<p>¡No te preocupes! Tus resultados están guardados y puedo intentar enviarlo de nuevo más tarde. También puedes acceder a tu información en cualquier momento a través de nuestro chat.</p>"
                )
    
    return notification

async def generate_verification_code():
    """Generate a 6-digit verification code"""
    import random
    return str(random.randint(100000, 999999))

async def send_verification_email(email: str, code: str, language: str = "es"):
    """Send verification code to email"""
    try:
        from email_config import send_verification_email as send_email
        return send_email(email, code, language)
    except ImportError:
        print(f"[DEBUG] Email module not available. Verification code for {email}: {code}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send verification email: {e}")
        return False

async def store_verification_code(user_id: str, code: str):
    """Store verification code with expiration time"""
    if not database or not database.is_connected:
        return False
    
    # Set expiration time to 15 minutes from now
    expires_at = datetime.datetime.now() + datetime.timedelta(minutes=15)
    
    try:
        await database.execute("""
            UPDATE users 
            SET verification_code = :code, verification_code_expires = :expires
            WHERE user_id = :user_id
        """, values={"code": code, "expires": expires_at, "user_id": user_id})
        return True
    except Exception as e:
        print(f"[DEBUG] Error storing verification code: {e}")
        return False

async def verify_email_code(user_id: str, code: str):
    """Verify email code and mark email as verified"""
    if not database or not database.is_connected:
        return False
    
    try:
        # Get stored code and expiration
        user = await database.fetch_one("""
            SELECT verification_code, verification_code_expires 
            FROM users 
            WHERE user_id = :user_id
        """, values={"user_id": user_id})
        
        if not user:
            return False
        
        stored_code = user["verification_code"]
        expires_at = user["verification_code_expires"]
        
        # Check if code matches and hasn't expired
        if stored_code == code and expires_at > datetime.datetime.now():
            # Mark email as verified and clear verification code
            await database.execute("""
                UPDATE users 
                SET email_verified = TRUE, verification_code = NULL, verification_code_expires = NULL
                WHERE user_id = :user_id
            """, values={"user_id": user_id})
            return True
        
        return False
        
    except Exception as e:
        print(f"[DEBUG] Error verifying email code: {e}")
        return False

async def is_email_verified(user_id: str):
    """Check if user's email is verified"""
    if not database or not database.is_connected:
        return False
    
    try:
        user = await database.fetch_one("""
            SELECT email_verified FROM users WHERE user_id = :user_id
        """, values={"user_id": user_id})
        
        return user and user["email_verified"] == True
    except Exception as e:
        print(f"[DEBUG] Error checking email verification: {e}")
        return False

async def is_premium_user(user_id: str):
    """Check if user has premium access"""
    if not database or not database.is_connected:
        return False
    
    try:
        user = await database.fetch_one("""
            SELECT is_premium FROM users WHERE user_id = :user_id
        """, values={"user_id": user_id})
        
        return user and user["is_premium"] == True
    except Exception as e:
        print(f"[DEBUG] Error checking premium status: {e}")
        return False

async def set_premium_user(user_id: str, is_premium: bool = True):
    """Set user's premium status"""
    if not database or not database.is_connected:
        return False
    
    try:
        await database.execute("""
            UPDATE users SET is_premium = :is_premium WHERE user_id = :user_id
        """, values={"user_id": user_id, "is_premium": is_premium})
        return True
    except Exception as e:
        print(f"[DEBUG] Error setting premium status: {e}")
        return False

async def send_pdf_by_email(user_id: str, pdf_path: str = None, language: str = "es"):
    """Send PDF report by email to verified users"""
    if not database or not database.is_connected:
        return False
    
    try:
        # Get user email
        user = await database.fetch_one("""
            SELECT email FROM users WHERE user_id = :user_id
        """, values={"user_id": user_id})
        
        if not user:
            return False
        
        email = user["email"]
        
        # Check if email is verified
        if not await is_email_verified(user_id):
            print(f"[DEBUG] Email {email} not verified, cannot send PDF")
            return False
        
        # Get user profile for personalization
        user_profile = await get_user_profile(user_id)
        user_name = user_profile.get("nombre") if user_profile else None
        
        # Send PDF email
        try:
            from email_config import send_pdf_email
            return send_pdf_email(email, pdf_path, user_name, language)
        except ImportError:
            print(f"[DEBUG] Email module not available. PDF would be sent to {email}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send PDF email: {e}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error in send_pdf_by_email: {e}")
        return False

async def is_first_visit(user_id):
    """Check if this is the user's first visit (no conversation history)"""
    if not database or not database.is_connected:
        return True
    
    # Check if user has any conversation history
    history = await load_conversation_history(user_id, limit=1)
    return len(history) == 0

async def should_offer_affirmation(user_id):
    """Check if user should be offered a daily affirmation"""
    if not database or not database.is_connected:
        return False
    
    user_profile = await get_user_profile(user_id)
    if not user_profile or not user_profile.get("attachment_style"):
        return False
    
    # Check if user has already received an affirmation today
    fecha_ultima_afirmacion = user_profile.get("fecha_ultima_afirmacion")
    if fecha_ultima_afirmacion:
        try:
            if isinstance(fecha_ultima_afirmacion, str):
                fecha_ultima_afirmacion = datetime.datetime.fromisoformat(fecha_ultima_afirmacion)
            hoy = datetime.date.today()
            if fecha_ultima_afirmacion.date() >= hoy:
                return False  # Already received affirmation today
        except Exception as e:
            print(f"[DEBUG] Error parsing fecha_ultima_afirmacion: {e}")
    
    return True

async def get_daily_affirmation(user_id):
    """Get the next sequential daily affirmation for the user's attachment style"""
    if not database or not database.is_connected:
        return None
        
    user_profile = await get_user_profile(user_id)
    if not user_profile:
        return None
    
    attachment_style = user_profile.get("attachment_style")
    if not attachment_style:
        return None
    
    # Get the last affirmation for this style to determine the next one
    last_affirmation = user_profile.get(f"afirmacion_{attachment_style}")
    
    if last_affirmation:
        # Find the index of the last affirmation in database
        last_affirmation_row = await database.fetch_one("""
            SELECT order_index FROM affirmations 
            WHERE attachment_style = :style AND text = :text AND language = 'es'
        """, {"style": attachment_style, "text": last_affirmation})
        
        if last_affirmation_row:
            last_index = last_affirmation_row["order_index"]
            # Get total count of affirmations for this style
            total_count = await database.fetch_val("""
                SELECT COUNT(*) FROM affirmations 
                WHERE attachment_style = :style AND language = 'es'
            """, {"style": attachment_style})
            next_index = (last_index + 1) % total_count
        else:
            next_index = 0
    else:
        # First time, start with index 0
        next_index = 0
    
    # Get the next affirmation from database
    next_affirmation_row = await database.fetch_one("""
        SELECT text FROM affirmations 
        WHERE attachment_style = :style AND order_index = :index AND language = 'es'
    """, {"style": attachment_style, "index": next_index})
    
    if not next_affirmation_row:
        return None
    
    selected_affirmation = next_affirmation_row["text"]
    
    # Save the affirmation and update the date
    await save_user_profile(
        user_id, 
        fecha_ultima_afirmacion=datetime.datetime.now(),
        **{f"afirmacion_{attachment_style}": selected_affirmation}
    )
    
    return selected_affirmation

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

async def load_full_user_snapshot(user_id: str) -> Dict[str, Any]:
    """Load a comprehensive, current snapshot of all user-related DB variables."""
    snapshot: Dict[str, Any] = {"user_id": user_id}
    if not database or not database.is_connected:
        return snapshot

    # Users table (auth + prefs)
    user_row = await database.fetch_one("SELECT user_id, email, email_verified, is_premium, preferred_language FROM users WHERE user_id = :user_id", {"user_id": user_id})
    snapshot["user"] = dict(user_row) if user_row else None

    # Profile (personal + relationship info)
    profile_row = await database.fetch_one("SELECT * FROM user_profile WHERE user_id = :user_id", {"user_id": user_id})
    snapshot["profile"] = dict(profile_row) if profile_row else None

    # Test state (flow + answers)
    test_row = await database.fetch_one(
        """
        SELECT state, last_choice, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10
        FROM test_state WHERE user_id = :user_id
        """,
        {"user_id": user_id},
    )
    snapshot["test_state"] = dict(test_row) if test_row else None

    return snapshot

async def get_user_language_preference(user_id):
    """Get user's preferred language from the users table"""
    if not database or not database.is_connected:
        return "es"  # Default to Spanish
    
    try:
        row = await database.fetch_one("SELECT preferred_language FROM users WHERE user_id = :user_id", {"user_id": user_id})
        return row["preferred_language"] if row and row["preferred_language"] else "es"
    except Exception as e:
        print(f"[DEBUG] Error getting user language preference: {e}")
        return "es"

async def save_user_language_preference(user_id, language):
    """Save user's preferred language to the users table"""
    if not database or not database.is_connected:
        return False
    
    try:
        await database.execute("""
            UPDATE users 
            SET preferred_language = :language 
            WHERE user_id = :user_id
        """, {"user_id": user_id, "language": language})
        print(f"[DEBUG] Saved language preference '{language}' for user {user_id}")
        return True
    except Exception as e:
        print(f"[DEBUG] Error saving user language preference: {e}")
        return False
