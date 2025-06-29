# Telegram Bot Deployment Guide

## 🚀 **Deploy to Render**

### **1. Create New Render Service**

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the repository with the Telegram bot code

### **2. Configure Service Settings**

**Name:** `svetlana-telegram-bot`
**Environment:** `Python 3`
**Build Command:** `pip install -r telegram_requirements.txt`
**Start Command:** `python telegram_bot.py`

### **3. Environment Variables**

Add these environment variables in Render:

```
SVETLANA_API_URL=https://svetlana-api-ak3a.onrender.com
WEBHOOK_URL=https://your-telegram-bot-service.onrender.com/webhook
```

### **4. Deploy and Get URL**

1. Click "Create Web Service"
2. Wait for deployment to complete
3. Copy your service URL (e.g., `https://svetlana-telegram-bot.onrender.com`)

### **5. Set Webhook**

Once deployed, visit:
```
https://your-telegram-bot-service.onrender.com/set-webhook
```

This will configure Telegram to send messages to your bot.

### **6. Test the Bot**

1. Find your bot on Telegram: `@your_bot_username`
2. Send `/start` to begin
3. Test with `saludo inicial` to start the attachment test

## 🔧 **Features**

### **Commands:**
- `/start` - Welcome message and instructions
- `/help` - Show available commands
- `/test` - Direct link to attachment test

### **Message Handling:**
- ✅ **HTML to Markdown conversion** for Telegram formatting
- ✅ **Typing indicators** for better UX
- ✅ **Language detection** (Spanish, English, Russian)
- ✅ **Full Svetlana API integration** with all features:
  - Knowledge quoting with citations
  - Conversation history
  - Personalization based on test results
  - Attachment style awareness

### **Error Handling:**
- ✅ **Graceful API failures**
- ✅ **User-friendly error messages**
- ✅ **Comprehensive logging**

## 📱 **User Experience**

1. **User sends message** → Telegram Bot receives webhook
2. **Bot calls Svetlana API** → Gets personalized response
3. **Format for Telegram** → Convert HTML to Markdown
4. **Send response** → User receives formatted message

## 🔍 **Monitoring**

Check logs in Render dashboard for:
- Webhook reception
- API calls to Svetlana
- Message sending status
- Error handling

## 🛠️ **Troubleshooting**

### **Webhook not working:**
1. Check if service is deployed and running
2. Verify webhook URL is correct
3. Check Telegram bot token
4. Visit `/set-webhook` endpoint

### **Messages not sending:**
1. Check Svetlana API URL
2. Verify API is responding
3. Check logs for errors

### **Formatting issues:**
1. Check HTML to Markdown conversion
2. Verify Telegram parse_mode settings 