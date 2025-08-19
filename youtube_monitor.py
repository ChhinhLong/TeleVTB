"""
YouTube API integration for monitoring channels and fetching video data.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests

logger = logging.getLogger(__name__)

class YouTubeMonitor:
    """YouTube API client for monitoring channels."""
    
    def __init__(self, api_key: str):
        """Initialize YouTube API client."""
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def extract_channel_id_from_url(self, url: str) -> Optional[str]:
        """Extract channel ID from various YouTube URL formats."""
        try:
            # Handle different URL formats
            patterns = [
                r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
                r'youtube\.com/c/([a-zA-Z0-9_-]+)',
                r'youtube\.com/@([a-zA-Z0-9_.-]+)',
                r'youtube\.com/user/([a-zA-Z0-9_-]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    identifier = match.group(1)
                    
                    # If it's already a channel ID (starts with UC), return it
                    if identifier.startswith('UC'):
                        return identifier
                    
                    # For usernames, custom URLs, or handles, we need to resolve them
                    return self._resolve_channel_id(identifier, url)
            
            logger.error(f"Could not extract channel identifier from URL: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting channel ID from URL {url}: {e}")
            return None
    
    def _resolve_channel_id(self, identifier: str, original_url: str) -> Optional[str]:
        """Resolve username/custom URL/handle to channel ID."""
        try:
            # Try searching by username first
            if not identifier.startswith('@'):
                search_response = self.youtube.search().list(
                    q=identifier,
                    type='channel',
                    part='id',
                    maxResults=1
                ).execute()
                
                if search_response['items']:
                    return search_response['items'][0]['id']['channelId']
            
            # For handles (starting with @), try to get channel info directly
            if identifier.startswith('@'):
                identifier = identifier[1:]  # Remove @ symbol
            
            # Try to get channel by custom URL or username
            try:
                channels_response = self.youtube.channels().list(
                    forUsername=identifier,
                    part='id'
                ).execute()
                
                if channels_response['items']:
                    return channels_response['items'][0]['id']
            except HttpError:
                pass
            
            # Last resort: try to access the channel page and extract from HTML
            return self._extract_channel_id_from_page(original_url)
            
        except Exception as e:
            logger.error(f"Error resolving channel ID for {identifier}: {e}")
            return None
    
    def _extract_channel_id_from_page(self, url: str) -> Optional[str]:
        """Extract channel ID from YouTube channel page HTML."""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # Look for channel ID in the page source
                match = re.search(r'"channelId":"([^"]+)"', response.text)
                if match:
                    return match.group(1)
                
                # Alternative pattern
                match = re.search(r'<meta property="og:url" content="https://www\.youtube\.com/channel/([^"]+)"', response.text)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting channel ID from page {url}: {e}")
            return None
    
    def get_channel_info(self, channel_id: str) -> Optional[Dict]:
        """Get channel information including name and thumbnail."""
        try:
            response = self.youtube.channels().list(
                id=channel_id,
                part='snippet,statistics'
            ).execute()
            
            if response['items']:
                channel = response['items'][0]
                return {
                    'id': channel_id,
                    'name': channel['snippet']['title'],
                    'description': channel['snippet'].get('description', ''),
                    'thumbnail': channel['snippet']['thumbnails'].get('default', {}).get('url', ''),
                    'subscriber_count': channel['statistics'].get('subscriberCount', 'N/A'),
                    'video_count': channel['statistics'].get('videoCount', 'N/A')
                }
            
            return None
            
        except HttpError as e:
            logger.error(f"YouTube API error getting channel info for {channel_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting channel info for {channel_id}: {e}")
            return None
    
    def get_latest_videos(self, channel_id: str, max_results: int = 5) -> List[Dict]:
        """Get the latest videos from a channel."""
        try:
            # Get the uploads playlist ID
            channels_response = self.youtube.channels().list(
                id=channel_id,
                part='contentDetails'
            ).execute()
            
            if not channels_response['items']:
                logger.warning(f"Channel {channel_id} not found")
                return []
            
            uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get the latest videos from the uploads playlist
            playlist_response = self.youtube.playlistItems().list(
                playlistId=uploads_playlist_id,
                part='snippet',
                maxResults=max_results,
                order='date'
            ).execute()
            
            videos = []
            for item in playlist_response['items']:
                video_info = {
                    'video_id': item['snippet']['resourceId']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': item['snippet']['publishedAt'],
                    'thumbnail': item['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                    'channel_title': item['snippet']['channelTitle'],
                    'url': f"https://www.youtube.com/watch?v={item['snippet']['resourceId']['videoId']}"
                }
                videos.append(video_info)
            
            return videos
            
        except HttpError as e:
            logger.error(f"YouTube API error getting latest videos for {channel_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting latest videos for {channel_id}: {e}")
            return []
    
    def get_live_streams(self, channel_id: str) -> List[Dict]:
        """Get current live streams from a channel."""
        try:
            search_response = self.youtube.search().list(
                channelId=channel_id,
                type='video',
                eventType='live',
                part='snippet',
                maxResults=5
            ).execute()
            
            streams = []
            for item in search_response['items']:
                stream_info = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': item['snippet']['publishedAt'],
                    'thumbnail': item['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                    'channel_title': item['snippet']['channelTitle'],
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'is_live': True
                }
                streams.append(stream_info)
            
            return streams
            
        except HttpError as e:
            logger.error(f"YouTube API error getting live streams for {channel_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting live streams for {channel_id}: {e}")
            return []
    
    def is_video_recent(self, published_at: str, hours: int = 24) -> bool:
        """Check if a video was published within the specified hours."""
        try:
            # Parse the YouTube timestamp
            published_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            current_time = datetime.now(published_time.tzinfo)
            
            # Check if the video is within the specified time frame
            time_diff = current_time - published_time
            return time_diff.total_seconds() <= hours * 3600
            
        except Exception as e:
            logger.error(f"Error checking if video is recent: {e}")
            return False
    
    def validate_channel_url(self, url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate a YouTube channel URL and return channel info."""
        try:
            channel_id = self.extract_channel_id_from_url(url)
            if not channel_id:
                return False, None, "Could not extract channel ID from URL"
            
            channel_info = self.get_channel_info(channel_id)
            if not channel_info:
                return False, None, "Channel not found or invalid"
            
            return True, channel_id, channel_info['name']
            
        except Exception as e:
            logger.error(f"Error validating channel URL {url}: {e}")
            return False, None, f"Error validating channel: {str(e)}"
