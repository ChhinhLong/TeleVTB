# YouTube Channel Monitor Telegram Bot

## Overview

This project is a Telegram bot that automatically monitors YouTube channels and notifies Telegram groups when new videos are published. The bot allows group administrators to add/remove YouTube channels for monitoring and automatically posts notifications with video details when new content is detected. Built with Python using the Telegram Bot API and YouTube Data API v3, it features SQLite database storage for persistent channel tracking and group management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Architecture
The application follows a modular design with clear separation of concerns:
- **Main Bot Controller**: `YouTubeBot` class handles all Telegram interactions, command processing, and orchestrates the monitoring workflow
- **Database Layer**: `Database` class provides abstraction for SQLite operations with dedicated methods for channel and group management
- **YouTube Integration**: `YouTubeMonitor` class handles YouTube API interactions, channel resolution, and video data fetching
- **Configuration Management**: Centralized configuration using environment variables with validation

### Command System
The bot implements a command-based interface for group administrators:
- `/addytc <URL>` - Add YouTube channels for monitoring (admin-only)
- `/removeytc <URL>` - Remove channels from monitoring (admin-only)
- `/listytc` - Display all monitored channels in the group
- `/group` - Bot permission management
- `/help` - Display usage instructions

### Data Storage
SQLite database with two main tables:
- **channels**: Stores monitored YouTube channels with group associations, last video tracking, and metadata
- **groups**: Manages Telegram group configurations and bot status
- Unique constraints prevent duplicate channel-group combinations

### Monitoring System
Asynchronous polling mechanism:
- Configurable polling intervals (default: 15 minutes) to respect API rate limits
- Batch processing with configurable limits for new video detection
- Last video ID tracking to prevent duplicate notifications
- Graceful error handling for API failures and network issues

### YouTube Integration
Flexible channel URL parsing supporting multiple YouTube URL formats:
- Direct channel IDs (UC prefix)
- Custom channel URLs (@username)
- Legacy user URLs (/user/)
- Channel URLs (/c/)
Automatic channel ID resolution for non-standard URL formats

### Message Formatting
Rich notification messages including:
- Video title and channel name
- Direct video links
- Optional thumbnail images
- Formatted text with proper escaping for Telegram markdown

## External Dependencies

### APIs and Services
- **Telegram Bot API**: Core bot functionality, message handling, and group management
- **YouTube Data API v3**: Channel monitoring, video metadata retrieval, and channel resolution
- **Google API Client**: YouTube API interaction library

### Database
- **SQLite**: Local database storage for channel configurations, group settings, and monitoring state

### Python Libraries
- **python-telegram-bot**: Telegram Bot API wrapper with async support
- **google-api-python-client**: Google APIs client library for YouTube integration
- **requests**: HTTP client for additional API calls and URL resolution

### Environment Configuration
Required environment variables:
- `TELEGRAM_BOT_TOKEN`: Bot authentication token from BotFather
- `YOUTUBE_API_KEY`: Google Cloud Console API key with YouTube Data API access
- Optional: `BOT_USERNAME`, `ADMIN_USER_ID` for enhanced bot management