# YouTube Channel Monitor Telegram Bot

A Telegram bot that automatically monitors YouTube channels and notifies groups when new videos are published. Features admin-only channel management, rich message formatting, and support for multiple languages including Khmer.

## Features

- 🎥 **Automatic YouTube Monitoring**: Checks for new videos every 15 minutes
- 🔒 **Admin Controls**: Only group admins can add/remove channels
- 🌐 **Multi-language Support**: Includes Khmer language support
- 📱 **Rich Messages**: Formatted notifications with video titles, thumbnails, and direct links
- 💾 **Persistent Storage**: SQLite database for channel tracking
- 🔄 **Live Stream Detection**: Monitors both regular videos and live streams

## Bot Commands

| Command | Description | Permission |
|---------|-------------|------------|
| `/addytc <URL>` | Add YouTube channel for monitoring | Admin only |
| `/removeytc <URL>` | Remove channel from monitoring | Admin only |
| `/listytc` | Show all monitored channels | All users |
| `/help` | Display usage instructions | All users |
| `/group` | Check bot permissions | All users |

## Supported YouTube URL Formats

- `https://www.youtube.com/channel/UC...`
- `https://www.youtube.com/@username`
- `https://www.youtube.com/c/channelname`
- `https://www.youtube.com/user/username`

## Setup Instructions

### Environment Variables

Set these required environment variables:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
YOUTUBE_API_KEY=your_youtube_api_key
```

Optional environment variables:
```
BOT_USERNAME=your_bot_username
ADMIN_USER_ID=your_admin_user_id
```

### Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -e .
   ```
3. Set environment variables
4. Run the bot:
   ```bash
   python main.py
   ```

### Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t youtube-telegram-bot .
   ```

2. Run the container:
   ```bash
   docker run -d \
     -e TELEGRAM_BOT_TOKEN=your_token \
     -e YOUTUBE_API_KEY=your_api_key \
     -v $(pwd)/data:/app/data \
     youtube-telegram-bot
   ```

### Deploy on Render

1. Fork this repository to your GitHub account
2. Connect your GitHub account to Render
3. Create a new Web Service on Render
4. Connect your repository
5. Configure environment variables:
   - `TELEGRAM_BOT_TOKEN`: Your bot token from BotFather
   - `YOUTUBE_API_KEY`: Your YouTube Data API v3 key
6. Deploy!

## Getting API Keys

### Telegram Bot Token
1. Open Telegram and search for @BotFather
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Save the provided token

### YouTube API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Restrict the key to YouTube Data API v3

## Usage

1. Add the bot to your Telegram group
2. Make the bot an admin with basic permissions
3. Use `/addytc` followed by a YouTube channel URL to start monitoring
4. The bot will automatically share new videos to the group

## Architecture

- **Main Bot Controller**: Handles Telegram interactions and commands
- **Database Layer**: SQLite for persistent channel and group management
- **YouTube Monitor**: Manages YouTube API interactions and video detection
- **Configuration**: Environment-based configuration management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.