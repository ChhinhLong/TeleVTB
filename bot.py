"""
Main Telegram bot implementation for YouTube channel monitoring.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    ContextTypes, ChatMemberHandler
)
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.error import TelegramError

from config import (
    TELEGRAM_BOT_TOKEN, YOUTUBE_API_KEY, DATABASE_FILE,
    POLLING_INTERVAL_MINUTES, MAX_VIDEOS_PER_CHECK, MAX_MESSAGE_LENGTH
)
from database import Database
from youtube_monitor import YouTubeMonitor

logger = logging.getLogger(__name__)

class YouTubeBot:
    """Main bot class handling all Telegram interactions and YouTube monitoring."""
    
    def __init__(self):
        """Initialize the bot with database and YouTube monitor."""
        self.db = Database(DATABASE_FILE)
        self.youtube = YouTubeMonitor(YOUTUBE_API_KEY)
        self.application = None
        self.monitoring_task = None
    
    async def start(self):
        """Initialize and start the bot."""
        # Create application
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("addytc", self.add_channel_command))
        self.application.add_handler(CommandHandler("removeytc", self.remove_channel_command))
        self.application.add_handler(CommandHandler("listytc", self.list_channels_command))
        self.application.add_handler(CommandHandler("group", self.group_command))
        
        # Add chat member handler for when bot is added to groups
        self.application.add_handler(ChatMemberHandler(self.bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER))
        
        # Initialize the application
        await self.application.initialize()
        await self.application.start()
        
        # Start the monitoring task
        self.monitoring_task = asyncio.create_task(self.monitor_youtube_channels())
        
        logger.info("Bot initialized and monitoring started")
    
    async def run_forever(self):
        """Keep the bot running."""
        try:
            # Start polling
            await self.application.updater.start_polling()
            
            # Wait for the monitoring task to complete (it runs forever)
            await self.monitoring_task
            
        except Exception as e:
            logger.error(f"Error in bot main loop: {e}")
            raise
        finally:
            # Cleanup
            if self.monitoring_task and not self.monitoring_task.done():
                self.monitoring_task.cancel()
            await self.application.stop()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = (
            "🎬 **YouTube Channel Monitor Bot**\n\n"
            "I can help you monitor YouTube channels and automatically share new videos in your groups!\n\n"
            "**Available Commands:**\n"
            "• /help - Show this help message\n"
            "• /addytc <URL> - Add a YouTube channel to monitor (Admin only)\n"
            "• /removeytc <URL> - Remove a YouTube channel (Admin only)\n"
            "• /listytc - List all monitored channels\n"
            "• /group - Configure bot permissions\n\n"
            "**Note:** Only group administrators can add or remove channels."
        )
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = (
            "🤖 **YouTube Monitor Bot Help**\n\n"
            "**Commands for Group Admins:**\n"
            "• `/addytc <URL>` - Add YouTube channel\n"
            "  Example: `/addytc https://www.youtube.com/@ChannelName`\n\n"
            "• `/removeytc <URL>` - Remove YouTube channel\n"
            "  Example: `/removeytc https://www.youtube.com/@ChannelName`\n\n"
            "**Commands for All Users:**\n"
            "• `/listytc` - Show all monitored channels\n"
            "• `/help` - Show this help message\n"
            "• `/group` - Check bot permissions\n\n"
            "**Supported URL Formats:**\n"
            "• `https://www.youtube.com/@username`\n"
            "• `https://www.youtube.com/channel/UC...`\n"
            "• `https://www.youtube.com/c/channelname`\n"
            "• `https://www.youtube.com/user/username`\n\n"
            "**How it works:**\n"
            "I check for new videos every 15 minutes and automatically share them in your group with formatted messages including title, channel name, and direct links."
        )
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def add_channel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /addytc command to add a YouTube channel."""
        # Check if this is a group chat
        if update.effective_chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("❌ This command can only be used in groups.")
            return
        
        # Check if user is admin
        if not await self.is_user_admin(update, context):
            await update.message.reply_text("❌ Only group administrators can add YouTube channels.")
            return
        
        # Check if URL is provided
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a YouTube channel URL.\n"
                "Usage: `/addytc https://www.youtube.com/@ChannelName`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        url = context.args[0]
        group_id = update.effective_chat.id
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=group_id, action="typing")
        
        try:
            # Validate the channel URL
            is_valid, channel_id, channel_name = self.youtube.validate_channel_url(url)
            
            if not is_valid:
                await update.message.reply_text(f"❌ Invalid YouTube channel URL: {channel_name}")
                return
            
            # Add channel to database
            success = self.db.add_channel(group_id, url, channel_id, channel_name)
            
            if success:
                await update.message.reply_text(
                    f"✅ **YouTube Channel បានបន្ថែមដោយជោគជ័យ!**\n\n"
                    f"📺 **Channel:** {channel_name}\n"
                    f"🔗 **URL:** {url}\n\n"
                    f"I'll now monitor this channel for new videos and share them here automatically.",
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info(f"Added channel {channel_name} to group {group_id}")
            else:
                await update.message.reply_text(
                    f"⚠️ Channel **{channel_name}** is already being monitored in this group.",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        except Exception as e:
            logger.error(f"Error adding channel {url} to group {group_id}: {e}")
            await update.message.reply_text(
                "❌ An error occurred while adding the channel. Please try again later."
            )
    
    async def remove_channel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /removeytc command to remove a YouTube channel."""
        # Check if this is a group chat
        if update.effective_chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("❌ This command can only be used in groups.")
            return
        
        # Check if user is admin
        if not await self.is_user_admin(update, context):
            await update.message.reply_text("❌ Only group administrators can remove YouTube channels.")
            return
        
        # Check if URL is provided
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a YouTube channel URL.\n"
                "Usage: `/removeytc https://www.youtube.com/@ChannelName`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        url = context.args[0]
        group_id = update.effective_chat.id
        
        try:
            # Remove channel from database
            success = self.db.remove_channel(group_id, url)
            
            if success:
                await update.message.reply_text(
                    f"✅ **YouTube Channel ត្រូវបានលុបចេញហើយ!**\n\n"
                    f"🔗 **URL:** {url}\n\n"
                    f"I will no longer monitor this channel for new videos.",
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info(f"Removed channel {url} from group {group_id}")
            else:
                await update.message.reply_text(
                    "❌ Channel not found in the monitoring list for this group."
                )
        
        except Exception as e:
            logger.error(f"Error removing channel {url} from group {group_id}: {e}")
            await update.message.reply_text(
                "❌ An error occurred while removing the channel. Please try again later."
            )
    
    async def list_channels_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /listytc command to list all monitored channels."""
        # Check if this is a group chat
        if update.effective_chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("❌ This command can only be used in groups.")
            return
        
        group_id = update.effective_chat.id
        
        try:
            channels = self.db.get_channels_for_group(group_id)
            
            if not channels:
                await update.message.reply_text(
                    "📝 No YouTube channels are currently being monitored in this group.\n\n"
                    "Use `/addytc <URL>` to add a channel (Admin only).",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            message = "📺 **Monitored YouTube Channels:**\n\n"
            
            for i, (channel_url, channel_id, channel_name, last_video_id, last_checked) in enumerate(channels, 1):
                status = "🟢 Active" if last_checked else "🟡 Pending first check"
                message += f"{i}. **{channel_name}**\n"
                message += f"   🔗 {channel_url}\n"
                message += f"   📊 Status: {status}\n\n"
            
            message += f"🔄 *Checks for new videos every {POLLING_INTERVAL_MINUTES} minutes*"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        
        except Exception as e:
            logger.error(f"Error listing channels for group {group_id}: {e}")
            await update.message.reply_text(
                "❌ An error occurred while fetching the channel list. Please try again later."
            )
    
    async def group_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /group command to check bot permissions."""
        if update.effective_chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("❌ This command can only be used in groups.")
            return
        
        try:
            chat_member = await context.bot.get_chat_member(
                chat_id=update.effective_chat.id,
                user_id=context.bot.id
            )
            
            if chat_member.status == ChatMemberStatus.ADMINISTRATOR:
                permissions = []
                if chat_member.can_delete_messages:
                    permissions.append("✅ Delete messages")
                if chat_member.can_restrict_members:
                    permissions.append("✅ Restrict members")
                if chat_member.can_pin_messages:
                    permissions.append("✅ Pin messages")
                if chat_member.can_invite_users:
                    permissions.append("✅ Invite users")
                
                message = (
                    "✅ **Bot has administrator privileges**\n\n"
                    "**Permissions:**\n" + "\n".join(permissions) + "\n\n"
                    "I'm ready to monitor YouTube channels and share new videos!"
                )
            else:
                message = (
                    "⚠️ **Bot needs administrator privileges**\n\n"
                    "Please promote me to administrator to ensure I can:\n"
                    "• Send messages with links\n"
                    "• Send messages with media\n"
                    "• Access chat information\n\n"
                    "Minimal permissions are sufficient for monitoring YouTube channels."
                )
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        
        except Exception as e:
            logger.error(f"Error checking group permissions: {e}")
            await update.message.reply_text(
                "❌ Could not check bot permissions. Please ensure I'm added to the group."
            )
    
    async def bot_added_to_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle when bot is added to a new group."""
        if not update.my_chat_member:
            return
        
        new_status = update.my_chat_member.new_chat_member.status
        old_status = update.my_chat_member.old_chat_member.status
        
        # Check if bot was added to the group
        if (old_status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED] and 
            new_status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]):
            
            chat = update.effective_chat
            
            # Add group to database
            self.db.add_group(chat.id, chat.title)
            
            # Send welcome message
            welcome_message = (
                "🎬 **សួស្តី! YouTube Monitor Bot បានចូលរួម**\n\n"
                "ខ្ញុំអាចជួយអ្នកតាមដាន YouTube channels និងចែករំលែកវីដេអូថ្មីៗដោយស្វ័យប្រវត្តិ!\n\n"
                "**ដំបូងគេ:**\n"
                "1. Promote ខ្ញុំជា admin (permissions ទាបបំផុតគឺគ្រប់គ្រាន់)\n"
                "2. ប្រើ /addytc <URL> ដើម្បីបន្ថែម YouTube channel\n"
                "3. ប្រើ /help សម្រាប់ព័ត៌មានលម្អិត\n\n"
                "**ចំណាំ:** មានតែ group admins ប៉ុណ្ណោះដែលអាចបន្ថែម ឬលុប channels បាន។"
            )
            
            try:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=welcome_message,
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info(f"Bot added to group: {chat.title} (ID: {chat.id})")
            except TelegramError as e:
                logger.error(f"Could not send welcome message to group {chat.id}: {e}")
    
    async def is_user_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if the user is an administrator of the group."""
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            
            chat_member = await context.bot.get_chat_member(chat_id, user_id)
            return chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        
        except Exception as e:
            logger.error(f"Error checking user admin status: {e}")
            return False
    
    async def monitor_youtube_channels(self):
        """Background task to monitor YouTube channels for new videos."""
        logger.info(f"Starting YouTube monitoring (checking every {POLLING_INTERVAL_MINUTES} minutes)")
        
        while True:
            try:
                await self.check_all_channels()
                
                # Wait for the next check
                await asyncio.sleep(POLLING_INTERVAL_MINUTES * 60)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)
    
    async def check_all_channels(self):
        """Check all monitored channels for new videos."""
        channels = self.db.get_all_channels()
        
        if not channels:
            logger.debug("No channels to monitor")
            return
        
        logger.info(f"Checking {len(channels)} channels for new videos")
        
        for group_id, channel_id, channel_name, last_video_id, last_checked in channels:
            try:
                await self.check_channel_for_new_videos(group_id, channel_id, channel_name, last_video_id)
                
                # Small delay between channel checks to avoid rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error checking channel {channel_name} for group {group_id}: {e}")
    
    async def check_channel_for_new_videos(self, group_id: int, channel_id: str, channel_name: str, last_video_id: Optional[str]):
        """Check a specific channel for new videos."""
        try:
            # Get latest videos
            videos = self.youtube.get_latest_videos(channel_id, MAX_VIDEOS_PER_CHECK)
            
            if not videos:
                logger.debug(f"No videos found for channel {channel_name}")
                return
            
            # Find new videos
            new_videos = []
            
            for video in videos:
                video_id = video['video_id']
                
                # Skip if we've already processed this video
                if self.db.is_video_processed(video_id, group_id):
                    continue
                
                # If this is the first check, only consider recent videos
                if last_video_id is None:
                    if not self.youtube.is_video_recent(video['published_at'], 24):
                        continue
                else:
                    # Stop if we've reached the last known video
                    if video_id == last_video_id:
                        break
                
                new_videos.append(video)
            
            # Also check for live streams
            live_streams = self.youtube.get_live_streams(channel_id)
            for stream in live_streams:
                if not self.db.is_video_processed(stream['video_id'], group_id):
                    new_videos.append(stream)
            
            # Share new videos
            if new_videos:
                logger.info(f"Found {len(new_videos)} new videos for {channel_name} in group {group_id}")
                
                for video in reversed(new_videos):  # Share oldest first
                    await self.share_video_to_group(group_id, video)
                    self.db.mark_video_processed(video['video_id'], channel_id, group_id)
                    
                    # Update last video ID
                    if 'is_live' not in video:  # Don't update for live streams
                        self.db.update_channel_last_video(group_id, channel_id, video['video_id'])
                    
                    # Small delay between messages
                    await asyncio.sleep(2)
            else:
                # Update last checked time even if no new videos
                if videos:
                    self.db.update_channel_last_video(group_id, channel_id, videos[0]['video_id'])
        
        except Exception as e:
            logger.error(f"Error checking channel {channel_name} for new videos: {e}")
    
    async def share_video_to_group(self, group_id: int, video: Dict):
        """Share a new video to a Telegram group."""
        try:
            # Format the message
            if video.get('is_live', False):
                message = f"🔴 **Live Stream:** {video['title']}\n"
            else:
                message = f"🎬 **New Video:** {video['title']}\n"
            
            message += f"📺 **From:** {video['channel_title']}\n"
            message += f"🔗 [Watch Here]({video['url']})\n"
            
            # Add description preview if available and not too long
            if video.get('description') and len(video['description']) > 0:
                description = video['description'][:200].strip()
                if len(description) < len(video['description']):
                    description += "..."
                message += f"\n📝 {description}"
            
            # Ensure message doesn't exceed Telegram's limit
            if len(message) > MAX_MESSAGE_LENGTH - 100:
                message = message[:MAX_MESSAGE_LENGTH - 100] + "..."
            
            # Create inline keyboard with the video link
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 Watch Video", url=video['url'])]
            ])
            
            # Send the message
            if video.get('thumbnail'):
                # Try to send with thumbnail
                try:
                    await self.application.bot.send_photo(
                        chat_id=group_id,
                        photo=video['thumbnail'],
                        caption=message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=keyboard
                    )
                    return
                except TelegramError:
                    # Fall back to text message if photo fails
                    pass
            
            # Send as text message
            await self.application.bot.send_message(
                chat_id=group_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
                disable_web_page_preview=False
            )
            
            logger.info(f"Shared video '{video['title']}' to group {group_id}")
        
        except TelegramError as e:
            logger.error(f"Error sharing video to group {group_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sharing video to group {group_id}: {e}")
