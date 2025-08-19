"""
Configuration settings for the YouTube monitoring bot.
"""

import os

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# YouTube API Configuration
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY environment variable is required")

# Database Configuration
DATABASE_FILE = "youtube_bot.db"

# Monitoring Configuration
POLLING_INTERVAL_MINUTES = 15  # Check for new videos every 15 minutes
MAX_VIDEOS_PER_CHECK = 5  # Maximum number of new videos to process per check

# Message Configuration
MAX_MESSAGE_LENGTH = 4096  # Telegram message length limit
THUMBNAIL_SIZE = "medium"  # YouTube thumbnail size (default, medium, high, standard, maxres)

# Bot Configuration
BOT_USERNAME = os.getenv("BOT_USERNAME", "")  # Optional: Bot username for mention detection
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "")  # Optional: Bot creator user ID
