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
    response = None  # Always initialize response
    try:
        user_id = msg.user_id
        message = msg.message.strip()
        
        print(f"[DEBUG] === CHAT ENDPOINT START ===")
        print(f"[DEBUG] user_id: {user_id}")
        print(f"[DEBUG] message: '{message}'")
        print(f"[DEBUG] language: {msg.language}")

        # Get or initialize test state
        try:
            if database is None:
                return {"response": "Lo siento, hay problemas de conexión con la base de datos. Por favor, intenta de nuevo en unos momentos."}
            
            state_row = await database.fetch_one("SELECT state, last_choice, q1, q2 FROM test_state WHERE user_id = :user_id", values={"user_id": user_id})
            state = state_row["state"] if state_row else None
            last_choice = state_row["last_choice"] if state_row else None
            q1 = state_row["q1"] if state_row else None
            q2 = state_row["q2"] if state_row else None
            
            print(f"[DEBUG] Database query result: {state_row}")
            print(f"[DEBUG] Retrieved state: {state}")
            print(f"[DEBUG] Retrieved last_choice: {last_choice}")
            print(f"[DEBUG] Retrieved q1: {q1}")
            print(f"[DEBUG] Retrieved q2: {q2}")
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
        
        print(f"[DEBUG] === STATE EVALUATION START ===")
        print(f"[DEBUG] Current state: {state}")
        print(f"[DEBUG] Message: '{message}'")
        print(f"[DEBUG] Message in test_triggers: {message.lower() in test_triggers}")
        
        # Initial greeting ONLY for the very first message
        if state is None:
            print("[DEBUG] ENTERED: state is None (first message) - SHOULD SHOW INITIAL GREETING")
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
            print(f"[DEBUG] Set initial greeting response: {response[:100]}...")
            return {"response": response}
        # Handle greeting choices (A, B, C)
        elif state == "greeting" and message.upper() in ["A", "B", "C"]:
            print(f"[DEBUG] ENTERED: greeting state with choice {message.upper()}")
            print(f"[DEBUG] In greeting state, user chose: {message.upper()}")
            if message.upper() == "A":
                # Start test
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
                # Normal conversation about feelings
                await set_state("conversation", None, None, None)
                if msg.language == "en":
                    response = "<p>I understand, sometimes we need to talk about what we feel before taking tests. How do you feel today? Is there something specific you'd like to share or explore together?</p>"
                elif msg.language == "ru":
                    response = "<p>Понимаю, иногда нам нужно поговорить о том, что мы чувствуем, прежде чем проходить тесты. Как ты себя чувствуешь сегодня? Есть ли что-то конкретное, что ты хотел бы поделиться или исследовать вместе?</p>"
                else:  # Spanish
                    response = "<p>Entiendo, a veces necesitamos hablar de lo que sentimos antes de hacer tests. ¿Cómo te sientes hoy? ¿Hay algo específico que te gustaría compartir o explorar juntos?</p>"
            elif message.upper() == "C":
                # Normal conversation about attachment
                await set_state("conversation", None, None, None)
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
        # Handle test restart requests during normal conversation
        elif state is None and message.lower() in test_triggers:
            print(f"[DEBUG] ENTERED: test restart request (state is None and message in triggers)")
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
        print(f"[DEBUG] Response length: {len(response) if response else 0}")
        print(f"[DEBUG] Current state: {state}, Message: '{message}', Response preview: {response[:100] if response else 'None'}...")

        if response is None:
            response = "Lo siento, ha ocurrido un error inesperado. Por favor, intenta de nuevo o formula tu pregunta de otra manera."
        return {"response": response}
    except Exception as e:
        print(f"[DEBUG] Exception in chat_endpoint: {e}")
        return {"response": "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta de nuevo en unos momentos."}
