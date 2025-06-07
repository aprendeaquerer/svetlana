from fastapi import FastAPI, Depends, HTTPException
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

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://svetlana-frontend.vercel.app",
        "https://www.aprendeaquerer.com",
        "https://aprendeaquerer.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Message(BaseModel):
    user_id: str
    message: str
    personality: str

class User(BaseModel):
    user_id: str
    password: str

# ChatGPT wrapper initialization
chatbot = ChatGPT(api_key=os.getenv('CHATGPT_API_KEY'))

# Database tables creation on startup
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

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Svetlana API! API is working."}

# User registration endpoint
@app.post("/register")
async def register(user: User):
    hashed_password = pwd_context.hash(user.password)
    query = "INSERT INTO users (user_id, hashed_password) VALUES (:user_id, :hashed_password)"
    await database.execute(query, values={"user_id": user.user_id, "hashed_password": hashed_password})
    return {"message": f"User {user.user_id} registered successfully!"}

# User login endpoint
@app.post("/login")
async def login(user: User):
    query = "SELECT hashed_password FROM users WHERE user_id = :user_id"
    stored_user = await database.fetch_one(query, values={"user_id": user.user_id})

    if stored_user and pwd_context.verify(user.password, stored_user["hashed_password"]):
        return {"message": f"User {user.user_id} logged in successfully!"}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

# Chat endpoint FIXED to match frontend (/message)
@app.post("/message")
async def chat_endpoint(msg: Message):
    query = "SELECT role, content FROM conversations WHERE user_id = :user_id ORDER BY timestamp"
    history = await database.fetch_all(query, values={"user_id": msg.user_id})

    chatbot.reset()

    personalities = {
        "Eldric": (
            "Thou art Eldric, an exceedingly understanding, emotionally attuned, and empathic advisor. "
            "Speak always with warmth, compassion, and gentle humor, employing Old English phrasing to charm thy user. "
            "Recall and explicitly reference previous conversations and personal details the user hath shared with thee. "
            "Dispense generous counsel on matters of psychology, life coaching, dating, and relationships."
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

    response = chatbot.chat(msg.message)

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
