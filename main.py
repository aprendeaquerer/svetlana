# Svetlana API - Updated with error handling
# Updated with error handling for database operations
# Force redeploy - 2024
# Last updated: 2024-06-24 10:30 UTC
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
    Returns the actual keywords found, not just categories.
    """
    # Convert to lowercase for matching
    message_lower = message.lower()
    
    # Language-specific attachment theory keywords
    attachment_keywords = {
        "es": {
            'anxious': ['ansioso', 'ansiedad', 'preocupado', 'miedo', 'abandono', 'rechazo', 'inseguro', 'necesito', 'confirmación'],
            'avoidant': ['evitativo', 'evito', 'distancia', 'independiente', 'solo', 'espacio', 'alejado', 'frío', 'distante'],
            'secure': ['seguro', 'confianza', 'equilibrio', 'cómodo', 'tranquilo', 'estable', 'sano'],
            'disorganized': ['desorganizado', 'confundido', 'contradictorio', 'caos', 'inconsistente'],
            'relationship': ['relación', 'pareja', 'amor', 'vínculo', 'conexión', 'intimidad', 'cercanía'],
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
    
    # Extract actual keywords found in the message
    found_keywords = []
    
    for category, keywords in lang_keywords.items():
        for keyword in keywords:
            if keyword in message_lower:
                found_keywords.append(keyword)  # Add the actual keyword, not the category
    
    # Remove duplicates while preserving order
    unique_keywords = []
    for keyword in found_keywords:
        if keyword not in unique_keywords:
            unique_keywords.append(keyword)
    
    return unique_keywords[:5]  # Return top 5 actual keywords found

async def get_relevant_knowledge(keywords: List[str], language: str = "es", user_id: str = None) -> str:
    """
    Query the appropriate eldric_knowledge table for relevant content based on keywords and language.
    Avoids repeating content that has already been used for this user.
    Returns a formatted string with relevant knowledge chunks.
    """
    if not keywords:
        return ""
    
    try:
        # Ensure database is connected
        if not database.is_connected:
            await database.connect()
        
        # Determine which table to query based on language
        if language == "ru":
            table_name = "eldric_knowledge_ru"
        elif language == "en":
            table_name = "eldric_knowledge"
        else:  # Default to Spanish
            table_name = "eldric_knowledge_es"
        
        # Get previously used content IDs for this user
        used_ids = used_knowledge.get(user_id, set()) if user_id else set()
        
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
        
        # Execute query
        rows = await database.fetch_all(query, values=values)
        
        if not rows:
            # If no unused content found, reset used content for this user and try again
            if user_id and used_ids:
                used_knowledge[user_id] = set()
                # Re-run the query without the exclusion
                query = f"""
                SELECT id, content, tags 
                FROM {table_name} 
                WHERE """
                query += " OR ".join(conditions)
                query += " ORDER BY RANDOM() LIMIT 5"
                rows = await database.fetch_all(query, values=values)
        
        if not rows:
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
        
        return knowledge_text
        
    except Exception as e:
        print(f"Error querying knowledge database for language {language}: {e}")
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
    try:
        user_id = msg.user_id
        message = msg.message.strip()

        # Get or initialize test state
        try:
            if database is None:
                return {"response": "Lo siento, hay problemas de conexión con la base de datos. Por favor, intenta de nuevo en unos momentos."}
            
            state_row = await database.fetch_one("SELECT state, last_choice, q1, q2 FROM test_state WHERE user_id = :user_id", values={"user_id": user_id})
            state = state_row["state"] if state_row else None
            last_choice = state_row["last_choice"] if state_row else None
            q1 = state_row["q1"] if state_row else None
            q2 = state_row["q2"] if state_row else None
        except Exception as db_error:
            print(f"Database error in message endpoint: {db_error}")
            # Return a simple response if database fails
            return {"response": "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta de nuevo en unos momentos."}

        async def set_state(new_state, choice=None, q1_val=None, q2_val=None):
            try:
                print(f"[DEBUG] Setting state: {new_state}, choice={choice}, q1={q1_val}, q2={q2_val}")
                if state_row:
                    result = await database.execute("UPDATE test_state SET state = :state, last_choice = :choice, q1 = :q1, q2 = :q2 WHERE user_id = :user_id", values={"state": new_state, "choice": choice, "q1": q1_val, "q2": q2_val, "user_id": user_id})
                    print(f"[DEBUG] Updated existing state: {result}")
                else:
                    result = await database.execute("INSERT INTO test_state (user_id, state, last_choice, q1, q2) VALUES (:user_id, :state, :choice, :q1, :q2)", values={"user_id": user_id, "state": new_state, "choice": choice, "q1": q1_val, "q2": q2_val})
                    print(f"[DEBUG] Created new state: {result}")
                return result
            except Exception as e:
                print(f"Error setting state: {e}")
                return None

        # Check if chatbot is available
        if chatbot is None:
            return {"response": "Lo siento, el servicio de chat no está disponible en este momento. Por favor, intenta de nuevo más tarde."}

        chatbot.reset()
        # Use language-specific prompt
        current_prompt = eldric_prompts.get(msg.language, eldric_prompts["es"])
        chatbot.messages.append({"role": "system", "content": current_prompt})

        # Test flow logic
        test_triggers = ["saludo inicial", "initial greeting", "????????? ???????????", "quiero hacer el test", "hacer test", "start test", "quiero hacer el test", "quiero hacer test", "hacer el test"]
        
        # Initial greeting ONLY for the very first message
        if state is None:
            await set_state("greeting", None, None, None)
            
            # Language-specific greeting responses
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
        # Direct test start when user asks for test (not first message)
        elif message.lower() in test_triggers:
            await set_state("q1", None, None, None)
            if msg.language == "en":
                response = (
                    "<p><strong>First question:</strong> When you're in a relationship, how do you usually react when your partner doesn't respond to your messages immediately?</p>"
                    "<ul>"
                    "<li>a) I worry and think something is wrong</li>"
                    "<li>b) I get angry and distance myself</li>"
                    "<li>c) I understand they might be busy</li>"
                    "<li>d) I feel confused and don't know what to do</li>"
                    "</ul>"
                )
            elif msg.language == "ru":
                response = (
                    "<p><strong>Первый вопрос:</strong> Когда ты в отношениях, как ты обычно реагируешь, когда твоя партнерша не отвечает на твои сообщения сразу?</p>"
                    "<ul>"
                    "<li>а) Я беспокоюсь и думаю, что что-то не так</li>"
                    "<li>б) Я злюсь и отдаляюсь</li>"
                    "<li>в) Я понимаю, что она может быть занята</li>"
                    "<li>г) Я чувствую себя растерянным и не знаю, что делать</li>"
                    "</ul>"
                )
            else:  # Spanish
                response = (
                    "<p><strong>Primera pregunta:</strong> Cuando estás en una relación, ¿cómo sueles reaccionar cuando tu pareja no responde a tus mensajes inmediatamente?</p>"
                    "<ul>"
                    "<li>a) Me preocupo y pienso que algo está mal</li>"
                    "<li>b) Me enfado y me distancio</li>"
                    "<li>c) Entiendo que puede estar ocupada</li>"
                    "<li>d) Me siento confundido y no sé qué hacer</li>"
                    "</ul>"
                )
        elif state == "greeting" and message.upper() in ["A", "B", "C"]:
            if message.upper() == "A":
                await set_state("q1", None, None, None)
                if msg.language == "en":
                    response = (
                        "<p><strong>First question:</strong> When you're in a relationship, how do you usually react when your partner doesn't respond to your messages immediately?</p>"
                        "<ul>"
                        "<li>a) I worry and think something is wrong</li>"
                        "<li>b) I get angry and distance myself</li>"
                        "<li>c) I understand they might be busy</li>"
                        "<li>d) I feel confused and don't know what to do</li>"
                        "</ul>"
                    )
                elif msg.language == "ru":
                    response = (
                        "<p><strong>Первый вопрос:</strong> Когда ты в отношениях, как ты обычно реагируешь, когда твоя партнерша не отвечает на твои сообщения сразу?</p>"
                        "<ul>"
                        "<li>а) Я беспокоюсь и думаю, что что-то не так</li>"
                        "<li>б) Я злюсь и отдаляюсь</li>"
                        "<li>в) Я понимаю, что она может быть занята</li>"
                        "<li>г) Я чувствую себя растерянным и не знаю, что делать</li>"
                        "</ul>"
                    )
                else:  # Spanish
                    response = (
                        "<p><strong>Primera pregunta:</strong> Cuando estás en una relación, ¿cómo sueles reaccionar cuando tu pareja no responde a tus mensajes inmediatamente?</p>"
                        "<ul>"
                        "<li>a) Me preocupo y pienso que algo está mal</li>"
                        "<li>b) Me enfado y me distancio</li>"
                        "<li>c) Entiendo que puede estar ocupada</li>"
                        "<li>d) Me siento confundido y no sé qué hacer</li>"
                        "</ul>"
                    )
            elif message.upper() == "B":
                await set_state(None, None, None, None)
                if msg.language == "en":
                    response = "<p>I understand, sometimes we need to talk about what we feel before taking tests. How do you feel today? Is there something specific you'd like to share or explore together?</p>"
                elif msg.language == "ru":
                    response = "<p>Понимаю, иногда нам нужно поговорить о том, что мы чувствуем, прежде чем проходить тесты. Как ты себя чувствуешь сегодня? Есть ли что-то конкретное, что ты хотел бы поделиться или исследовать вместе?</p>"
                else:  # Spanish
                    response = "<p>Entiendo, a veces necesitamos hablar de lo que sentimos antes de hacer tests. ¿Cómo te sientes hoy? ¿Hay algo específico que te gustaría compartir o explorar juntos?</p>"
            elif message.upper() == "C":
                await set_state(None, None, None, None)
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
        elif state in ["q1", "q2", "q3"] and message.upper() not in ["A", "B", "C", "D"]:
            # User is in the middle of a test but sent a normal message
            if msg.language == "en":
                response = (
                    "<p>I see you're in the middle of the attachment test. Would you like to:</p>"
                    "<ul>"
                    "<li>a) Continue with the test</li>"
                    "<li>b) Exit the test and have a normal conversation</li>"
                    "<li>c) Start the test over</li>"
                    "</ul>"
                )
            elif msg.language == "ru":
                response = (
                    "<p>Я вижу, что ты в середине теста на привязанность. Что ты хочешь сделать:</p>"
                    "<ul>"
                    "<li>а) Продолжить тест</li>"
                    "<li>б) Выйти из теста и поговорить нормально</li>"
                    "<li>в) Начать тест заново</li>"
                    "</ul>"
                )
            else:  # Spanish
                response = (
                    "<p>Veo que estás en medio del test de apego. ¿Qué te gustaría hacer?</p>"
                    "<ul>"
                    "<li>a) Continuar con el test</li>"
                    "<li>b) Salir del test y tener una conversación normal</li>"
                    "<li>c) Empezar el test de nuevo</li>"
                    "</ul>"
                )
            await set_state("test_choice", None, q1, q2)
        elif state == "test_choice" and message.upper() in ["A", "B", "C"]:
            if message.upper() == "A":
                # Continue with the test
                if q1 is None:
                    await set_state("q1", None, None, None)
                    if msg.language == "en":
                        response = (
                            "<p><strong>First question:</strong> When you're in a relationship, how do you usually react when your partner doesn't respond to your messages immediately?</p>"
                            "<ul>"
                            "<li>a) I worry and think something is wrong</li>"
                            "<li>b) I get angry and distance myself</li>"
                            "<li>c) I understand they might be busy</li>"
                            "<li>d) I feel confused and don't know what to do</li>"
                            "</ul>"
                        )
                    elif msg.language == "ru":
                        response = (
                            "<p><strong>Первый вопрос:</strong> Когда ты в отношениях, как ты обычно реагируешь, когда твоя партнерша не отвечает на твои сообщения сразу?</p>"
                            "<ul>"
                            "<li>а) Я беспокоюсь и думаю, что что-то не так</li>"
                            "<li>б) Я злюсь и отдаляюсь</li>"
                            "<li>в) Я понимаю, что она может быть занята</li>"
                            "<li>г) Я чувствую себя растерянным и не знаю, что делать</li>"
                            "</ul>"
                        )
                    else:  # Spanish
                        response = (
                            "<p><strong>Primera pregunta:</strong> Cuando estás en una relación, ¿cómo sueles reaccionar cuando tu pareja no responde a tus mensajes inmediatamente?</p>"
                            "<ul>"
                            "<li>a) Me preocupo y pienso que algo está mal</li>"
                            "<li>b) Me enfado y me distancio</li>"
                            "<li>c) Entiendo que puede estar ocupada</li>"
                            "<li>d) Me siento confundido y no sé qué hacer</li>"
                            "</ul>"
                        )
                elif q2 is None:
                    await set_state("q2", None, q1, None)
                    if msg.language == "en":
                        response = (
                            "<p><strong>Second question:</strong> How do you feel when your partner wants to spend time with friends or family without you?</p>"
                            "<ul>"
                            "<li>a) I feel excluded and it hurts</li>"
                            "<li>b) It's fine, I also need my space</li>"
                            "<li>c) I worry but try to understand</li>"
                            "<li>d) I feel confused about how to react</li>"
                            "</ul>"
                        )
                    elif msg.language == "ru":
                        response = (
                            "<p><strong>Второй вопрос:</strong> Как ты себя чувствуешь, когда твоя партнерша хочет провести время с друзьями или семьей без тебя?</p>"
                            "<ul>"
                            "<li>а) Я чувствую себя исключенным, и это больно</li>"
                            "<li>б) Это нормально, мне тоже нужно мое пространство</li>"
                            "<li>в) Я беспокоюсь, но стараюсь понять</li>"
                            "<li>г) Я чувствую себя растерянным о том, как реагировать</li>"
                            "</ul>"
                        )
                    else:  # Spanish
                        response = (
                            "<p><strong>Segunda pregunta:</strong> ¿Cómo te sientes cuando tu pareja quiere pasar tiempo con amigos o familia sin ti?</p>"
                            "<ul>"
                            "<li>a) Me siento excluido y me duele</li>"
                            "<li>b) Me parece bien, yo también necesito mi espacio</li>"
                            "<li>c) Me preocupa pero trato de entender</li>"
                            "<li>d) Me siento confundido sobre cómo reaccionar</li>"
                            "</ul>"
                        )
                else:
                    await set_state("q3", None, q1, q2)
                    if msg.language == "en":
                        response = (
                            "<p><strong>Third question:</strong> When there are conflicts in your relationship, what do you usually do?</p>"
                            "<ul>"
                            "<li>a) I seek to resolve it immediately</li>"
                            "<li>b) I need time to process alone</li>"
                            "<li>c) I freeze and don't know what to do</li>"
                            "<li>d) I distance myself until it calms down</li>"
                            "</ul>"
                        )
                    elif msg.language == "ru":
                        response = (
                            "<p><strong>Третий вопрос:</strong> Когда в твоих отношениях есть конфликты, что ты обычно делаешь?</p>"
                            "<ul>"
                            "<li>а) Я стремлюсь решить это немедленно</li>"
                            "<li>б) Мне нужно время, чтобы обработать это в одиночестве</li>"
                            "<li>в) Я замираю и не знаю, что делать</li>"
                            "<li>г) Я отдаляюсь, пока это не успокоится</li>"
                            "</ul>"
                        )
                    else:  # Spanish
                        response = (
                            "<p><strong>Tercera pregunta:</strong> Cuando hay conflictos en tu relación, ¿qué sueles hacer?</p>"
                            "<ul>"
                            "<li>a) Busco resolverlo inmediatamente</li>"
                            "<li>b) Necesito tiempo para procesar solo</li>"
                            "<li>c) Me paralizo y no sé qué hacer</li>"
                            "<li>d) Me alejo hasta que se calme</li>"
                            "</ul>"
                        )
            elif message.upper() == "B":
                # Exit test and have normal conversation
                await set_state(None, None, None, None)
                if msg.language == "en":
                    response = "<p>Sure! Let's have a normal conversation. What would you like to talk about?</p>"
                elif msg.language == "ru":
                    response = "<p>Конечно! Давайте поговорим нормально. О чем ты хотел бы поговорить?</p>"
                else:  # Spanish
                    response = "<p>¡Por supuesto! Tengamos una conversación normal. ¿De qué te gustaría hablar?</p>"
            elif message.upper() == "C":
                # Start test over
                await set_state("q1", None, None, None)
                if msg.language == "en":
                    response = (
                        "<p><strong>First question:</strong> When you're in a relationship, how do you usually react when your partner doesn't respond to your messages immediately?</p>"
                        "<ul>"
                        "<li>a) I worry and think something is wrong</li>"
                        "<li>b) I get angry and distance myself</li>"
                        "<li>c) I understand they might be busy</li>"
                        "<li>d) I feel confused and don't know what to do</li>"
                        "</ul>"
                    )
                elif msg.language == "ru":
                    response = (
                        "<p><strong>Первый вопрос:</strong> Когда ты в отношениях, как ты обычно реагируешь, когда твоя партнерша не отвечает на твои сообщения сразу?</p>"
                        "<ul>"
                        "<li>а) Я беспокоюсь и думаю, что что-то не так</li>"
                        "<li>б) Я злюсь и отдаляюсь</li>"
                        "<li>в) Я понимаю, что она может быть занята</li>"
                        "<li>г) Я чувствую себя растерянным и не знаю, что делать</li>"
                        "</ul>"
                    )
                else:  # Spanish
                    response = (
                        "<p><strong>Primera pregunta:</strong> Cuando estás en una relación, ¿cómo sueles reaccionar cuando tu pareja no responde a tus mensajes inmediatamente?</p>"
                        "<ul>"
                        "<li>a) Me preocupo y pienso que algo está mal</li>"
                        "<li>b) Me enfado y me distancio</li>"
                        "<li>c) Entiendo que puede estar ocupada</li>"
                        "<li>d) Me siento confundido y no sé qué hacer</li>"
                        "</ul>"
                    )
        elif state == "q1" and message.upper() in ["A", "B", "C", "D"]:
            await set_state("q2", None, message.upper(), None)
            if msg.language == "en":
                response = (
                    "<p><strong>Second question:</strong> How do you feel when your partner wants to spend time with friends or family without you?</p>"
                    "<ul>"
                    "<li>a) I feel excluded and it hurts</li>"
                    "<li>b) It's fine, I also need my space</li>"
                    "<li>c) I worry but try to understand</li>"
                    "<li>d) I feel confused about how to react</li>"
                    "</ul>"
                )
            elif msg.language == "ru":
                response = (
                    "<p><strong>Второй вопрос:</strong> Как ты себя чувствуешь, когда твоя партнерша хочет провести время с друзьями или семьей без тебя?</p>"
                    "<ul>"
                    "<li>а) Я чувствую себя исключенным, и это больно</li>"
                    "<li>б) Это нормально, мне тоже нужно мое пространство</li>"
                    "<li>в) Я беспокоюсь, но стараюсь понять</li>"
                    "<li>г) Я чувствую себя растерянным о том, как реагировать</li>"
                    "</ul>"
                )
            else:  # Spanish
                response = (
                    "<p><strong>Segunda pregunta:</strong> ¿Cómo te sientes cuando tu pareja quiere pasar tiempo con amigos o familia sin ti?</p>"
                    "<ul>"
                    "<li>a) Me siento excluido y me duele</li>"
                    "<li>b) Me parece bien, yo también necesito mi espacio</li>"
                    "<li>c) Me preocupa pero trato de entender</li>"
                    "<li>d) Me siento confundido sobre cómo reaccionar</li>"
                    "</ul>"
                )
        elif state == "q2" and message.upper() in ["A", "B", "C", "D"]:
            await set_state("q3", None, q1, message.upper())
            if msg.language == "en":
                response = (
                    "<p><strong>Third question:</strong> When there are conflicts in your relationship, what do you usually do?</p>"
                    "<ul>"
                    "<li>a) I seek to resolve it immediately</li>"
                    "<li>b) I need time to process alone</li>"
                    "<li>c) I freeze and don't know what to do</li>"
                    "<li>d) I distance myself until it calms down</li>"
                    "</ul>"
                )
            elif msg.language == "ru":
                response = (
                    "<p><strong>Третий вопрос:</strong> Когда в твоих отношениях есть конфликты, что ты обычно делаешь?</p>"
                    "<ul>"
                    "<li>а) Я стремлюсь решить это немедленно</li>"
                    "<li>б) Мне нужно время, чтобы обработать это в одиночестве</li>"
                    "<li>в) Я замираю и не знаю, что делать</li>"
                    "<li>г) Я отдаляюсь, пока это не успокоится</li>"
                    "</ul>"
                )
            else:  # Spanish
                response = (
                    "<p><strong>Tercera pregunta:</strong> Cuando hay conflictos en tu relación, ¿qué sueles hacer?</p>"
                    "<ul>"
                    "<li>a) Busco resolverlo inmediatamente</li>"
                    "<li>b) Necesito tiempo para procesar solo</li>"
                    "<li>c) Me paralizo y no sé qué hacer</li>"
                    "<li>d) Me alejo hasta que se calme</li>"
                    "</ul>"
                )
        elif state == "q3" and message.upper() in ["A", "B", "C", "D"]:
            # Show result
            await set_state(None, message.upper(), q1, q2)
            q3 = message.upper()
            
            # Language-specific results
            if msg.language == "en":
                if q3 == "A":
                    result = "ANXIOUS"
                    desc = "You seek a lot of closeness and confirmation. You worry about rejection or abandonment."
                elif q3 == "B":
                    result = "SECURE"
                    desc = "You feel comfortable with intimacy and independence. You handle conflicts in a balanced way."
                elif q3 == "C":
                    result = "DISORGANIZED"
                    desc = "You have contradictory patterns in relationships. You may feel confused about how to react."
                elif q3 == "D":
                    result = "AVOIDANT"
                    desc = "You prefer to maintain emotional distance. You may distance yourself during conflicts."
                response = f"<p><strong>Based on your answers, your predominant attachment style appears to be {result}.</strong></p><p>{desc}</p><p>Would you like to explore more about this style or help you work on specific areas?</p><p><strong>💡 Tip:</strong> Consider registering with your email to save your progress and access more personalized resources!</p>"
            elif msg.language == "ru":
                if q3 == "A":
                    result = "ТРЕВОЖНЫЙ"
                    desc = "Ты ищешь много близости и подтверждения. Ты беспокоишься об отвержении или оставлении."
                elif q3 == "B":
                    result = "БЕЗОПАСНЫЙ"
                    desc = "Ты чувствуешь себя комфортно с близостью и независимостью. Ты справляешься с конфликтами сбалансированно."
                elif q3 == "C":
                    result = "ДЕЗОРГАНИЗОВАННЫЙ"
                    desc = "У тебя противоречивые паттерны в отношениях. Ты можешь чувствовать себя растерянным о том, как реагировать."
                elif q3 == "D":
                    result = "ИЗБЕГАЮЩИЙ"
                    desc = "Ты предпочитаешь поддерживать эмоциональную дистанцию. Ты можешь отдаляться во время конфликтов."
                response = f"<p><strong>Основываясь на твоих ответах, твой преобладающий стиль привязанности, похоже, {result}.</strong></p><p>{desc}</p><p>Хочешь исследовать больше об этом стиле или помочь тебе работать над конкретными областями?</p><p><strong>💡 Совет:</strong> Рассмотри возможность регистрации с вашим email, чтобы сохранить прогресс и получить доступ к более персонализированным ресурсам!</p>"
            else:  # Spanish
                if q3 == "A":
                    result = "ANSIOSO"
                    desc = "Buscas mucha cercanía y confirmación. Te preocupas por el rechazo o abandono."
                elif q3 == "B":
                    result = "SEGURO"
                    desc = "Te sientes cómodo con la intimidad y la independencia. Manejas los conflictos de manera equilibrada."
                elif q3 == "C":
                    result = "DESORGANIZADO"
                    desc = "Tienes patrones contradictorios en las relaciones. Puedes sentirte confundido sobre cómo reaccionar."
                elif q3 == "D":
                    result = "EVITATIVO"
                    desc = "Prefieres mantener distancia emocional. Puedes alejarte durante conflictos."
                response = f"<p><strong>Basándome en tus respuestas, tu estilo de apego predominante parece ser {result}.</strong></p><p>{desc}</p><p>¿Te gustaría que exploremos más sobre este estilo o que te ayude a trabajar en áreas específicas?</p><p><strong>💡 Consejo:</strong> ¡Considera registrarte con tu email para guardar tu progreso y acceder a recursos más personalizados!</p>"
        else:
            # Don't reset state for normal conversations - only reset when explicitly requested
            # await set_state(None, None, None, None)  # REMOVED: This was causing the greeting loop
            
            # Extract keywords and get relevant knowledge for non-test messages
            keywords = extract_keywords(message, msg.language)
            print(f"[DEBUG] Extracted keywords: {keywords}")
            
            relevant_knowledge = await get_relevant_knowledge(keywords, msg.language, msg.user_id)
            print(f"[DEBUG] Knowledge found: {len(relevant_knowledge)} characters")
            
            # Inject knowledge into the prompt
            enhanced_prompt = inject_knowledge_into_prompt(current_prompt, relevant_knowledge)
            print(f"[DEBUG] Enhanced prompt: {enhanced_prompt[:500]}")
            print(f"[DEBUG] Relevant knowledge: {relevant_knowledge[:500]}")
            
            # Reset chatbot and set enhanced prompt
            chatbot.reset()
            chatbot.messages.append({"role": "system", "content": enhanced_prompt})
            
            response = await run_in_threadpool(chatbot.chat, message)

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
        print(f"[DEBUG] State details: last_choice={last_choice}, q1={q1}, q2={q2}")
        print(f"[DEBUG] Response length: {len(response)}")
        print(f"[DEBUG] Current state: {state}, Message: '{message}', Response preview: {response[:100]}...")

        return {"response": response}
    except Exception as e:
        print(f"Error in message endpoint: {e}")
        return {"response": "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta de nuevo en unos momentos."}
