# Deployment Guide

This guide explains how to deploy your YouTube Telegram Bot to various platforms.

## Quick Deploy to Render

### Option 1: One-Click Deploy
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/yourusername/youtube-telegram-bot)

### Option 2: Manual Deploy

1. **Fork this repository** to your GitHub account

2. **Create a Render account** at [render.com](https://render.com)

3. **Connect your GitHub account** to Render

4. **Create a new Web Service**:
   - Click "New +" → "Web Service"
   - Connect your forked repository
   - Use these settings:
     - **Name**: `youtube-telegram-bot`
     - **Environment**: `Docker`
     - **Region**: Choose closest to your users
     - **Branch**: `main`
     - **Build Command**: (leave empty)
     - **Start Command**: `python main.py`

5. **Set Environment Variables**:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   YOUTUBE_API_KEY=your_youtube_api_key_here
   PORT=10000
   ```

6. **Deploy**: Click "Create Web Service"

## GitHub Setup for Auto-Deploy

### 1. Repository Setup
```bash
# Initialize git repository
git init
git add .
git commit -m "Initial commit: YouTube Telegram Bot"

# Add GitHub remote (replace with your repository URL)
git remote add origin https://github.com/yourusername/youtube-telegram-bot.git
git branch -M main
git push -u origin main
```

### 2. GitHub Secrets Configuration

Go to your repository settings → Secrets and variables → Actions, and add:

- `RENDER_SERVICE_ID`: Your Render service ID (found in service URL)
- `RENDER_API_KEY`: Your Render API key (from account settings)

### 3. Automatic Deployment

Once configured, the bot will automatically deploy to Render when you push to the main branch.

## Alternative Deployment Options

### Deploy to Railway

1. Fork this repository
2. Connect to [Railway](https://railway.app)
3. Add environment variables:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   YOUTUBE_API_KEY=your_api_key
   ```
4. Deploy automatically

### Deploy to Heroku

1. Install Heroku CLI
2. Create Heroku app:
   ```bash
   heroku create your-bot-name
   ```
3. Set environment variables:
   ```bash
   heroku config:set TELEGRAM_BOT_TOKEN=your_token
   heroku config:set YOUTUBE_API_KEY=your_api_key
   ```
4. Deploy:
   ```bash
   git push heroku main
   ```

### Deploy to DigitalOcean App Platform

1. Fork this repository
2. Connect to DigitalOcean App Platform
3. Configure environment variables
4. Deploy with one click

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Bot token from @BotFather | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `YOUTUBE_API_KEY` | ✅ | YouTube Data API v3 key | `AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw` |
| `BOT_USERNAME` | ❌ | Bot username (without @) | `my_youtube_bot` |
| `ADMIN_USER_ID` | ❌ | Admin user ID for extra controls | `123456789` |
| `PORT` | ❌ | Port for health checks | `10000` |

## Getting API Keys

### Telegram Bot Token
1. Open Telegram and message @BotFather
2. Send `/newbot` command
3. Choose a name and username for your bot
4. Save the provided token securely

### YouTube API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "YouTube Data API v3"
4. Go to Credentials → Create Credentials → API Key
5. Restrict the key to YouTube Data API v3 (recommended)
6. Copy the API key

## Troubleshooting

### Common Issues

**Bot not responding**:
- Check if TELEGRAM_BOT_TOKEN is correct
- Ensure bot is added to group as admin
- Verify environment variables are set

**YouTube monitoring not working**:
- Verify YOUTUBE_API_KEY is valid
- Check API quotas in Google Cloud Console
- Ensure YouTube Data API v3 is enabled

**Deployment fails**:
- Check build logs for specific errors
- Verify all required files are in repository
- Ensure Docker configuration is correct

### Health Check Endpoint

The bot includes a health check endpoint at `/health` for deployment platforms:
- **URL**: `https://your-app.onrender.com/health`
- **Response**: `200 OK` with body `OK`

## Monitoring and Logs

### Render Logs
- Go to your service dashboard
- Click "Logs" tab to view real-time logs
- Monitor for errors or connection issues

### Bot Status Commands
- Use `/group` command to check bot permissions
- Use `/listytc` to verify monitored channels
- Check logs for YouTube API responses

## Scaling and Maintenance

### Database Backup
The bot uses SQLite stored in `/app/data/`. For production:
- Consider upgrading to PostgreSQL
- Implement regular database backups
- Monitor storage usage

### API Rate Limits
- YouTube API: 10,000 requests/day (default)
- Telegram API: 30 messages/second
- Monitor usage in respective dashboards

### Updates and Maintenance
- Bot automatically restarts on deployment
- Database migrations handled automatically
- Monitor logs for any issues after updates