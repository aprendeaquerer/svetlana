# Aprende a Querer - Chatbot Project

## 🚀 DEPLOYMENT ARCHITECTURE

**IMPORTANTE**: Este proyecto usa una arquitectura separada:
- **Frontend**: Vercel (https://svetlana-frontend.vercel.app)
- **Backend**: Render (https://svetlana-api-ak3a.onrender.com)

### Frontend (Vercel)
- **Location**: `C:\frontend`
- **Deployment**: Vercel (https://svetlana-frontend.vercel.app)
- **Main files**:
  - `index.html` - Landing page with chatbot iframe
  - `chat.html` - Chatbot interface with mobile auto-scroll
  - `login.html` - User login page
  - `register.html` - User registration page
  - `assets/` - CSS, JS, images, fonts

### Backend (Render)
- **Location**: `C:\wrapper`
- **Deployment**: Render (https://svetlana-api-ak3a.onrender.com)
- **Main files**:
  - `main.py` - FastAPI app with chat endpoint and test flow
  - `svetlana_personality.py` - Chatbot personality configuration
  - `chatgpt_wrapper.py` - ChatGPT integration
  - `requirements.txt` - Python dependencies

## Project Structure

## Key Features

### Chatbot Functionality
- **Eldric**: Emotional coach with attachment theory expertise
- **A/B/C Test Flow**: Interactive attachment style assessment
- **One-by-one Questions**: Progressive test with state tracking
- **Session Management**: Persistent state for both registered users and guests
- **Mobile Optimized**: Auto-scroll and responsive design
- **Knowledge Injection**: Context-aware responses using curated book knowledge

### User Management
- **Guest Users**: Session ID stored in localStorage for persistent state
- **Registered Users**: Database-backed user accounts and conversation history
- **Authentication**: Login/register system with bcrypt password hashing

## Development Workflow

### Frontend Development
```bash
cd C:\frontend
# Edit HTML/CSS/JS files
git add .
git commit -m "description"
git push
# Auto-deploys to Vercel
```

### Backend Development
```bash
cd C:\wrapper
# Edit Python files
git add .
git commit -m "description"
git push
# Auto-deploys to Render
```

## API Endpoints

- `GET /` - Health check
- `POST /message` - Chat endpoint
- `POST /register` - User registration
- `POST /login` - User authentication

## Database Schema

### Tables
- `conversations` - Chat history
- `users` - User accounts
- `test_state` - Attachment test progress
- `eldric_knowledge` - Curated knowledge chunks from books

## Recent Updates

### Conversation Flow Fix (Latest)
- Fixed greeting loop issue where Eldric kept offering the test repeatedly
- Test now only starts when explicitly requested ("saludo inicial", "hacer test", etc.)
- Normal conversations flow naturally without test interruptions
- Added simple greeting for new users without pushing test

### Knowledge Injection System
- Keyword extraction from user messages
- Database queries for relevant knowledge chunks
- Context-aware responses using curated book content
- Support for multiple books: "Attached" and additional titles

### Mobile Auto-Scroll
- Fixed auto-scroll functionality for mobile devices
- Improved CSS with `-webkit-overflow-scrolling: touch`
- Fixed input positioning on mobile
- Multiple scroll methods for better compatibility

### Test Flow
- A/B/C/D answer detection working
- Questions sent one by one
- Persistent state tracking
- Session ID management for guests

## Deployment URLs

- **Frontend**: https://svetlana-frontend.vercel.app
- **Backend API**: https://svetlana-api-ak3a.onrender.com
- **Production Site**: https://www.aprendeaquerer.com

## Notes for Future Development

- Always edit frontend files in `C:\frontend`
- Always edit backend files in `C:\wrapper`
- Test A/B/C functionality after changes
- Verify mobile auto-scroll works
- Check session persistence for guest users
- Knowledge base is automatically queried for relevant responses

## Populating the Knowledge Base for Eldric

To populate the eldric_knowledge table with curated knowledge from the book "Attached":

1. Make sure you have the files `attached_knowledge.json` and `seed_from_json.py` in your `c:/scripts` directory.
2. Run the following command in your terminal:

```bash
cd c:/scripts
python seed_from_json.py
```

This will load the knowledge chunks into the database, making them available for Eldric's context-aware responses.

## ⚠️ NOTAS IMPORTANTES PARA DESARROLLO

**ARQUITECTURA DE DEPLOYMENT:**
- **Frontend**: Vercel maneja el frontend (HTML, CSS, JS)
- **Backend**: Render maneja el backend (Python, FastAPI, Database)

**CUANDO HAY PROBLEMAS:**
- Si el frontend no carga → Revisar Vercel
- Si el chatbot no responde → Revisar Render
- Si hay errores 404 en recursos → Revisar Vercel
- Si hay errores de API → Revisar Render

**FLUJO DE DESARROLLO:**
1. Editar archivos en `C:\wrapper` (backend)
2. `git add . && git commit -m "descripción" && git push`
3. Render detecta cambios y hace auto-deploy
4. Probar en https://svetlana-api-ak3a.onrender.com/status
5. Si hay problemas, revisar logs en Render dashboard

**URLS IMPORTANTES:**
- Frontend: https://svetlana-frontend.vercel.app
- Backend: https://svetlana-api-ak3a.onrender.com
- Status endpoint: https://svetlana-api-ak3a.onrender.com/status
