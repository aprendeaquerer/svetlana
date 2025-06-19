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

    # Always use Eldric's prompt
    chatbot.messages.append({"role": "system", "content": eldric_prompt})

    for entry in history:
        chatbot.messages.append({"role": entry["role"], "content": entry["content"]})

    if msg.message.strip().lower() == "saludo inicial":
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
    elif msg.message.strip().upper() in ['A', 'B', 'C', 'D']:
        # Handle A/B/C/D choices based on context
        choice = msg.message.strip().upper()
        
        # Check conversation history to determine which question this is answering
        user_messages = [entry["content"] for entry in history if entry["role"] == "user"]
        bot_messages = [entry["content"] for entry in history if entry["role"] == "assistant"]
        
        # Determine the current question based on the last bot message
        if len(bot_messages) == 0 or "saludo inicial" in bot_messages[-1]:
            # First choice (response to initial greeting)
            if choice == 'A':
                response = (
                    "<p>¡Perfecto! Vamos a explorar tu estilo de apego. Te haré algunas preguntas para entender mejor cómo te relacionas emocionalmente.</p>"
                    "<p><strong>Primera pregunta:</strong> Cuando estás en una relación, ¿cómo sueles reaccionar cuando tu pareja no responde a tus mensajes inmediatamente?</p>"
                    "<ul>"
                    "<li>a) Me preocupo y pienso que algo está mal</li>"
                    "<li>b) Me enfado y me distancio</li>"
                    "<li>c) Entiendo que puede estar ocupada</li>"
                    "<li>d) Me siento confundido y no sé qué hacer</li>"
                    "</ul>"
                )
            elif choice == 'B':
                response = (
                    "<p>Entiendo, a veces necesitamos hablar de lo que sentimos antes de hacer tests. ¿Cómo te sientes hoy? ¿Hay algo específico que te gustaría compartir o explorar juntos?</p>"
                )
            elif choice == 'C':
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
        elif "Primera pregunta" in bot_messages[-1]:
            # Second choice (response to first test question)
            if choice == 'A':
                response = (
                    "<p>Entiendo, esa preocupación es común. Vamos a la siguiente pregunta.</p>"
                    "<p><strong>Segunda pregunta:</strong> ¿Cómo te sientes cuando tu pareja quiere pasar tiempo con amigos o familia sin ti?</p>"
                    "<ul>"
                    "<li>a) Me siento excluido y me duele</li>"
                    "<li>b) Me parece bien, yo también necesito mi espacio</li>"
                    "<li>c) Me preocupa pero trato de entender</li>"
                    "<li>d) Me siento confundido sobre cómo reaccionar</li>"
                    "</ul>"
                )
            elif choice == 'B':
                response = (
                    "<p>La distancia puede ser una forma de protegerse. Continuemos.</p>"
                    "<p><strong>Segunda pregunta:</strong> ¿Cómo te sientes cuando tu pareja quiere pasar tiempo con amigos o familia sin ti?</p>"
                    "<ul>"
                    "<li>a) Me siento excluido y me duele</li>"
                    "<li>b) Me parece bien, yo también necesito mi espacio</li>"
                    "<li>c) Me preocupa pero trato de entender</li>"
                    "<li>d) Me siento confundido sobre cómo reaccionar</li>"
                    "</ul>"
                )
            elif choice == 'C':
                response = (
                    "<p>Esa comprensión es muy valiosa. Sigamos explorando.</p>"
                    "<p><strong>Segunda pregunta:</strong> ¿Cómo te sientes cuando tu pareja quiere pasar tiempo con amigos o familia sin ti?</p>"
                    "<ul>"
                    "<li>a) Me siento excluido y me duele</li>"
                    "<li>b) Me parece bien, yo también necesito mi espacio</li>"
                    "<li>c) Me preocupa pero trato de entender</li>"
                    "<li>d) Me siento confundido sobre cómo reaccionar</li>"
                    "</ul>"
                )
            elif choice == 'D':
                response = (
                    "<p>Esa confusión es natural. Vamos a la siguiente pregunta.</p>"
                    "<p><strong>Segunda pregunta:</strong> ¿Cómo te sientes cuando tu pareja quiere pasar tiempo con amigos o familia sin ti?</p>"
                    "<ul>"
                    "<li>a) Me siento excluido y me duele</li>"
                    "<li>b) Me parece bien, yo también necesito mi espacio</li>"
                    "<li>c) Me preocupa pero trato de entender</li>"
                    "<li>d) Me siento confundido sobre cómo reaccionar</li>"
                    "</ul>"
                )
        elif "Segunda pregunta" in bot_messages[-1]:
            # Third choice (response to second test question)
            if choice == 'A':
                response = (
                    "<p>Ese sentimiento de exclusión es muy real. Última pregunta.</p>"
                    "<p><strong>Tercera pregunta:</strong> Cuando hay conflictos en tu relación, ¿qué sueles hacer?</p>"
                    "<ul>"
                    "<li>a) Busco resolverlo inmediatamente</li>"
                    "<li>b) Necesito tiempo para procesar solo</li>"
                    "<li>c) Me paralizo y no sé qué hacer</li>"
                    "<li>d) Me alejo hasta que se calme</li>"
                    "</ul>"
                )
            elif choice == 'B':
                response = (
                    "<p>El espacio personal es importante para ti. Última pregunta.</p>"
                    "<p><strong>Tercera pregunta:</strong> Cuando hay conflictos en tu relación, ¿qué sueles hacer?</p>"
                    "<ul>"
                    "<li>a) Busco resolverlo inmediatamente</li>"
                    "<li>b) Necesito tiempo para procesar solo</li>"
                    "<li>c) Me paralizo y no sé qué hacer</li>"
                    "<li>d) Me alejo hasta que se calme</li>"
                    "</ul>"
                )
            elif choice == 'C':
                response = (
                    "<p>Esa preocupación equilibrada es muy sana. Última pregunta.</p>"
                    "<p><strong>Tercera pregunta:</strong> Cuando hay conflictos en tu relación, ¿qué sueles hacer?</p>"
                    "<ul>"
                    "<li>a) Busco resolverlo inmediatamente</li>"
                    "<li>b) Necesito tiempo para procesar solo</li>"
                    "<li>c) Me paralizo y no sé qué hacer</li>"
                    "<li>d) Me alejo hasta que se calme</li>"
                    "</ul>"
                )
            elif choice == 'D':
                response = (
                    "<p>Esa confusión es comprensible. Última pregunta.</p>"
                    "<p><strong>Tercera pregunta:</strong> Cuando hay conflictos en tu relación, ¿qué sueles hacer?</p>"
                    "<ul>"
                    "<li>a) Busco resolverlo inmediatamente</li>"
                    "<li>b) Necesito tiempo para procesar solo</li>"
                    "<li>c) Me paralizo y no sé qué hacer</li>"
                    "<li>d) Me alejo hasta que se calme</li>"
                    "</ul>"
                )
        elif "Tercera pregunta" in bot_messages[-1]:
            # Fourth choice (response to third test question) - Show results
            if choice == 'A':
                response = (
                    "<p><strong>Basándome en tus respuestas, tu estilo de apego predominante parece ser ANSIOSO.</strong></p>"
                    "<p>Características del apego ansioso:</p>"
                    "<ul>"
                    "<li>Buscas mucha cercanía y confirmación</li>"
                    "<li>Te preocupas por el rechazo o abandono</li>"
                    "<li>Puedes ser muy sensible a las señales de tu pareja</li>"
                    "<li>Tiendes a resolver conflictos inmediatamente</li>"
                    "</ul>"
                    "<p>¿Te gustaría que exploremos más sobre este estilo o que te ayude a trabajar en áreas específicas?</p>"
                )
            elif choice == 'B':
                response = (
                    "<p><strong>Basándome en tus respuestas, tu estilo de apego predominante parece ser SEGURO.</strong></p>"
                    "<p>Características del apego seguro:</p>"
                    "<ul>"
                    "<li>Te sientes cómodo con la intimidad y la independencia</li>"
                    "<li>Entiendes que las personas necesitan su espacio</li>"
                    "<li>Manejas los conflictos de manera equilibrada</li>"
                    "<li>Tienes una visión positiva de las relaciones</li>"
                    "</ul>"
                    "<p>¿Te gustaría que exploremos más sobre este estilo o que te ayude a mantener esta seguridad?</p>"
                )
            elif choice == 'C':
                response = (
                    "<p><strong>Basándome en tus respuestas, tu estilo de apego predominante parece ser DESORGANIZADO.</strong></p>"
                    "<p>Características del apego desorganizado:</p>"
                    "<ul>"
                    "<li>Tienes patrones contradictorios en las relaciones</li>"
                    "<li>Puedes sentirte confundido sobre cómo reaccionar</li>"
                    "<li>Necesitas más apoyo para procesar emociones</li>"
                    "<li>Los conflictos pueden paralizarte</li>"
                    "</ul>"
                    "<p>¿Te gustaría que exploremos más sobre este estilo o que te ayude a encontrar más claridad?</p>"
                )
            elif choice == 'D':
                response = (
                    "<p><strong>Basándome en tus respuestas, tu estilo de apego predominante parece ser EVITATIVO.</strong></p>"
                    "<p>Características del apego evitativo:</p>"
                    "<ul>"
                    "<li>Prefieres mantener distancia emocional</li>"
                    "<li>Valoras mucho tu independencia</li>"
                    "<li>Puedes alejarte durante conflictos</li>"
                    "<li>Te cuesta mostrar vulnerabilidad</li>"
                    "</ul>"
                    "<p>¿Te gustaría que exploremos más sobre este estilo o que te ayude a abrirte más?</p>"
                )
        else:
            # For other A/B/C/D choices, send to ChatGPT with context
            response = chatbot.chat(msg.message)
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