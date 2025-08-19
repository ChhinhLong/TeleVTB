"""
Database management for the YouTube monitoring bot.
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

class Database:
    """Database manager for the YouTube bot."""
    
    def __init__(self, db_file: str):
        """Initialize database connection and create tables."""
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Table for storing monitored YouTube channels
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS channels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_id INTEGER NOT NULL,
                        channel_url TEXT NOT NULL,
                        channel_id TEXT NOT NULL,
                        channel_name TEXT NOT NULL,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_video_id TEXT,
                        last_checked TIMESTAMP,
                        UNIQUE(group_id, channel_id)
                    )
                ''')
                
                # Table for storing group configurations
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS groups (
                        group_id INTEGER PRIMARY KEY,
                        group_title TEXT,
                        bot_added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                # Table for storing processed videos to avoid duplicates
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS processed_videos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        video_id TEXT NOT NULL,
                        channel_id TEXT NOT NULL,
                        group_id INTEGER NOT NULL,
                        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(video_id, group_id)
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def add_group(self, group_id: int, group_title: Optional[str] = None):
        """Add a group to the database."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO groups (group_id, group_title, bot_added_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (group_id, group_title))
                conn.commit()
                logger.info(f"Added group {group_id} to database")
                
        except sqlite3.Error as e:
            logger.error(f"Error adding group to database: {e}")
            raise
    
    def add_channel(self, group_id: int, channel_url: str, channel_id: str, channel_name: str) -> bool:
        """Add a YouTube channel to monitor for a specific group."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO channels (group_id, channel_url, channel_id, channel_name)
                    VALUES (?, ?, ?, ?)
                ''', (group_id, channel_url, channel_id, channel_name))
                conn.commit()
                logger.info(f"Added channel {channel_name} for group {group_id}")
                return True
                
        except sqlite3.IntegrityError:
            logger.warning(f"Channel {channel_id} already exists for group {group_id}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Error adding channel to database: {e}")
            raise
    
    def remove_channel(self, group_id: int, channel_url: str) -> bool:
        """Remove a YouTube channel from monitoring for a specific group."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM channels 
                    WHERE group_id = ? AND channel_url = ?
                ''', (group_id, channel_url))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Removed channel {channel_url} from group {group_id}")
                    return True
                else:
                    logger.warning(f"Channel {channel_url} not found for group {group_id}")
                    return False
                    
        except sqlite3.Error as e:
            logger.error(f"Error removing channel from database: {e}")
            raise
    
    def get_channels_for_group(self, group_id: int) -> List[Tuple]:
        """Get all monitored channels for a specific group."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT channel_url, channel_id, channel_name, last_video_id, last_checked
                    FROM channels 
                    WHERE group_id = ?
                    ORDER BY channel_name
                ''', (group_id,))
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            logger.error(f"Error getting channels for group: {e}")
            return []
    
    def get_all_channels(self) -> List[Tuple]:
        """Get all monitored channels across all groups."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT group_id, channel_id, channel_name, last_video_id, last_checked
                    FROM channels
                    WHERE group_id IN (SELECT group_id FROM groups WHERE is_active = 1)
                    ORDER BY last_checked ASC NULLS FIRST
                ''')
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            logger.error(f"Error getting all channels: {e}")
            return []
    
    def update_channel_last_video(self, group_id: int, channel_id: str, video_id: str):
        """Update the last video ID for a channel."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE channels 
                    SET last_video_id = ?, last_checked = CURRENT_TIMESTAMP
                    WHERE group_id = ? AND channel_id = ?
                ''', (video_id, group_id, channel_id))
                conn.commit()
                
        except sqlite3.Error as e:
            logger.error(f"Error updating channel last video: {e}")
            raise
    
    def is_video_processed(self, video_id: str, group_id: int) -> bool:
        """Check if a video has already been processed for a group."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 1 FROM processed_videos 
                    WHERE video_id = ? AND group_id = ?
                ''', (video_id, group_id))
                return cursor.fetchone() is not None
                
        except sqlite3.Error as e:
            logger.error(f"Error checking processed video: {e}")
            return False
    
    def mark_video_processed(self, video_id: str, channel_id: str, group_id: int):
        """Mark a video as processed for a group."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO processed_videos (video_id, channel_id, group_id)
                    VALUES (?, ?, ?)
                ''', (video_id, channel_id, group_id))
                conn.commit()
                
        except sqlite3.Error as e:
            logger.error(f"Error marking video as processed: {e}")
            raise
    
    def cleanup_old_processed_videos(self, days: int = 30):
        """Clean up old processed video records to prevent database bloat."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM processed_videos 
                    WHERE processed_at < datetime('now', '-{} days')
                '''.format(days))
                deleted = cursor.rowcount
                conn.commit()
                if deleted > 0:
                    logger.info(f"Cleaned up {deleted} old processed video records")
                
        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old records: {e}")
