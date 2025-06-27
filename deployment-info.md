# 🚀 DEPLOYMENT INFORMATION

## Architecture
- **Frontend**: Vercel (HTML, CSS, JS)
- **Backend**: Render (Python, FastAPI, Database)

## URLs
- Frontend: https://svetlana-frontend.vercel.app
- Backend: https://svetlana-api-ak3a.onrender.com
- Status: https://svetlana-api-ak3a.onrender.com/status

## Troubleshooting Guide

### Frontend Issues (Vercel)
- 404 errors on resources
- Page not loading
- CSS/JS not working
- Check: Vercel dashboard

### Backend Issues (Render)
- API not responding
- Database errors
- Chatbot not working
- Check: Render dashboard logs

## Development Flow
1. Edit files in `C:\wrapper` (backend)
2. `git add . && git commit -m "msg" && git push`
3. Render auto-deploys
4. Test at status endpoint
5. Check logs if issues

## Quick Commands
```bash
# Check backend status
curl https://svetlana-api-ak3a.onrender.com/status

# Check if backend is responding
curl https://svetlana-api-ak3a.onrender.com/

# Test chat endpoint
curl -X POST https://svetlana-api-ak3a.onrender.com/message \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"saludo inicial","language":"es"}'
``` 