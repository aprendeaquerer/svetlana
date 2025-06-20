from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from databases import Database
from chatgpt_wrapper import ChatGPT
from pydantic import BaseModel
import uuid
from passlib.context import CryptContext
import os
from typing import Dict

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

class User(BaseModel):
    user_id: str
    password: str

chatbot = ChatGPT(api_key=os.getenv('CHATGPT_API_KEY'))

eldric_prompt = (
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
)

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
    await database.execute("""
        CREATE TABLE IF NOT EXISTS test_state (
            user_id TEXT PRIMARY KEY,
            state TEXT,
            last_choice TEXT,
            q1 TEXT,
            q2 TEXT
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
    user_id = msg.user_id
    message = msg.message.strip()

    # Get or initialize test state
    state_row = await database.fetch_one("SELECT state, last_choice, q1, q2 FROM test_state WHERE user_id = :user_id", values={"user_id": user_id})
    state = state_row["state"] if state_row else None
    last_choice = state_row["last_choice"] if state_row else None
    q1 = state_row["q1"] if state_row else None
    q2 = state_row["q2"] if state_row else None

    async def set_state(new_state, choice=None, q1_val=None, q2_val=None):
        if state_row:
            return await database.execute("UPDATE test_state SET state = :state, last_choice = :choice, q1 = :q1, q2 = :q2 WHERE user_id = :user_id", values={"state": new_state, "choice": choice, "q1": q1_val, "q2": q2_val, "user_id": user_id})
        else:
            return await database.execute("INSERT INTO test_state (user_id, state, last_choice, q1, q2) VALUES (:user_id, :state, :choice, :q1, :q2)", values={"user_id": user_id, "state": new_state, "choice": choice, "q1": q1_val, "q2": q2_val})

    chatbot.reset()
    chatbot.messages.append({"role": "system", "content": eldric_prompt})

    # Test flow logic
    if state is None or message.lower() == "saludo inicial":
        await set_state("greeting", None, None, None)
        response = (
            "<p><strong>Hola, soy Eldric</strong>, tu coach emocional. Estoy aquí para acompañarte a entenderte mejor desde la teoría del apego.</p>"
            "<p>En psicología del apego, solemos hablar de cuatro estilos: <strong>seguro, ansioso, evitativo y desorganizado</strong>. Cada uno influye en cómo te vinculas emocionalmente.</p>"
            "<p>Para comenzar, ¿quieres hacer un pequeño test que te ayude a descubrir tu estilo predominante?</p>"
            "<ul>"
            "<li>a) Sí, quiero entender mi forma de querer.</li>"
            "<li>b) Prefiero hablar de cómo me siento ahora.</li>"
            "<li>c) Cuentame mas sobre el apego.</li>"
            "</ul>"
        )
    elif state == "greeting" and message.upper() in ["A", "B", "C"]:
        if message.upper() == "A":
            await set_state("q1", None, None, None)
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
            response = "<p>Entiendo, a veces necesitamos hablar de lo que sentimos antes de hacer tests. ¿Cómo te sientes hoy? ¿Hay algo específico que te gustaría compartir o explorar juntos?</p>"
        elif message.upper() == "C":
            await set_state(None, None, None, None)
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
    elif state == "q1" and message.upper() in ["A", "B", "C", "D"]:
        await set_state("q2", None, message.upper(), None)
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
        response = f"<p><strong>Basándome en tus respuestas, tu estilo de apego predominante parece ser {result}.</strong></p><p>{desc}</p><p>¿Te gustaría que exploremos más sobre este estilo o que te ayude a trabajar en áreas específicas?</p>"
    else:
        await set_state(None, None, None, None)
        response = chatbot.chat(message)

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

    return {"response": response}