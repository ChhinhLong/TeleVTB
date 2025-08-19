#!/usr/bin/env python3
"""
Main entry point for the YouTube monitoring Telegram bot.
"""

import asyncio
import logging
import signal
import sys
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from bot import YouTubeBot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple health check handler for Render deployment."""
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass

def start_health_server():
    """Start a simple HTTP server for health checks."""
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Health check server starting on port {port}")
    server.serve_forever()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal. Stopping bot...")
    sys.exit(0)

async def main():
    """Main function to start the bot."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start health check server in background thread (for Render)
        health_thread = Thread(target=start_health_server, daemon=True)
        health_thread.start()
        
        # Initialize and start the bot
        bot = YouTubeBot()
        await bot.start()
        
        # Keep the bot running
        logger.info("Bot started successfully. Press Ctrl+C to stop.")
        await bot.run_forever()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
