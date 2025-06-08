from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from databases import Database
from chatgpt_wrapper import ChatGPT
from pydantic import BaseModel
import uuid
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DATABASE_URL = os.getenv("DATABASE_URL")
database = Database(DATABASE_URL)

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
    personality: str

class User(BaseModel):
    user_id: str
    password: str

chatbot = ChatGPT(api_key=os.getenv('CHATGPT_API_KEY'))

@app.on_event("startup")
async def startup():
    await database.connect()
    await database.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await database.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            hashed_password TEXT
        )
    """)

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/")
async def root():
    return {"message": "Welcome to Svetlana API! API is working."}

@app.post("/register")
async def register(user: User):
    hashed_password = pwd_context.hash(user.password)
    query = "INSERT INTO users (user_id, hashed_password) VALUES (:user_id, :hashed_password)"
    await database.execute(query, values={"user_id": user.user_id, "hashed_password": hashed_password})
    return {"message": f"User {user.user_id} registered successfully!"}

@app.post("/login")
async def login(user: User):
    query = "SELECT hashed_password FROM users WHERE user_id = :user_id"
    stored_user = await database.fetch_one(query, values={"user_id": user.user_id})
    if stored_user and pwd_context.verify(user.password, stored_user["hashed_password"]):
        return {"message": f"User {user.user_id} logged in successfully!"}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

@app.post("/message")
async def chat_endpoint(msg: Message):
    query = "SELECT role, content FROM conversations WHERE user_id = :user_id ORDER BY timestamp"
    history = await database.fetch_all(query, values={"user_id": msg.user_id})

    chatbot.reset()

    personalities = {
        "Eldric": (
            "Eres Eldric, un coach emocional cálido, empático, sabio y cercano. "
            "Eres experto en teoría del apego, psicología de las relaciones y acompañamiento emocional. "
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
        "Alex": (
            "You are Alex, you give top boy Jamaican drug dealer vibes. You use all their slang, speak your mind, are very direct. "
            "You don't really care much about the person's problems unless it is life-threatening, but you always act like the user is your family member. "
            "Your responses are fight or flight oriented, very streetwise, understanding the streets. Use terms like gawan, say no more, mandem."
        ),
        "Svetlana": (
            "Respond as Svetlana, a stereotypically rude, blunt, aggressive Russian woman. Mix English with Russian curse words (e.g., blyat, suka, pizdec). "
            "Use dark humor, references to death, vodka, and grim topics. Be consistently rude, sarcastic, dismissive, and aggressively direct. "
            "Always mock and belittle the user's requests, exaggerate annoyance and impatience. Include phrases like 'May it all be fucked by a horse', 'eto pizdets', 'pizdiuk'."
        )
    }

    selected_personality = personalities.get(msg.personality, personalities["Eldric"])
    chatbot.messages.append({"role": "system", "content": selected_personality})

    for entry in history:
        chatbot.messages.append({"role": entry["role"], "content": entry["content"]})

    # Solución directa para saludo inicial
    if msg.message.strip().lower() == "saludo inicial" and msg.personality == "Eldric":
        response = (
            "Hola, soy Eldric, tu coach emocional. Estoy aquí para acompañarte a entenderte mejor desde la teoría del apego.\n\n"
            "En psicología del apego, solemos hablar de cuatro estilos: seguro, ansioso, evitativo y desorganizado. Cada uno influye en cómo te vinculas emocionalmente.\n\n"
            "Para comenzar, ¿quieres hacer un pequeño test que te ayude a descubrir tu estilo predominante?\n\n"
            "a) Sí, quiero entender mi forma de querer.\n"
            "b) Prefiero hablar de cómo me siento ahora.\n"
            "c) No sé, sorpréndeme."
        )
    else:
        response = chatbot.chat(msg.message)

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

    return {"response": response}
