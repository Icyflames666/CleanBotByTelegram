import telebot
import threading
import os
import time
import requests
import logging
from flask import Flask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CleanBotByTelegram")

# Initialize Flask app
app = Flask("CleanBotByTelegram")

# Get bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("Missing BOT_TOKEN environment variable")
    raise RuntimeError("Missing BOT_TOKEN environment variable")

# Validate token format
if ":" not in BOT_TOKEN or len(BOT_TOKEN) < 30:
    logger.error("Invalid token format")
    raise ValueError("Invalid token format")

bot = telebot.TeleBot(BOT_TOKEN)
logger.info("CleanBotByTelegram initialized")

# Message tracking
message_timers = {}

def schedule_delete(chat_id, message_id, delay=300):
    def delete_wrapper():
        try:
            bot.delete_message(chat_id, message_id)
            logger.info(f"Deleted message {message_id}")
        except telebot.apihelper.ApiException as e:
            if "message to delete not found" not in str(e):
                logger.error(f"Delete failed: {e}")
        except Exception as e:
            logger.error(f"Delete failed: {e}")
        finally:
            if message_id in message_timers:
                del message_timers[message_id]
    
    timer = threading.Timer(delay, delete_wrapper)
    timer.start()
    message_timers[message_id] = timer
    logger.info(f"Scheduled deletion: {message_id}")

@bot.message_handler(func=lambda _: True)
def handle_message(message):
    logger.info(f"New message: {message.message_id}")
    schedule_delete(message.chat.id, message.message_id)

def start_bot():
    logger.info("Starting bot polling")
    bot.infinity_polling()

@app.route('/')
def health_check():
    return "✅ CleanBotByTelegram is Running", 200

def keep_alive():
    logger.info("Keep-alive started")
    while True:
        try:
            render_url = os.getenv('RENDER_EXTERNAL_URL')
            if render_url:
                response = requests.get(f"{render_url}/")
                logger.info(f"Keep-alive ping successful ({response.status_code})")
            else:
                logger.warning("RENDER_EXTERNAL_URL not set")
        except Exception as e:
            logger.error(f"Keep-alive failed: {e}")
        time.sleep(120)

if _name_ == '_main_':
    # Start bot thread
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start keep-alive thread
    keep_alive_thread = threading.Thread(target=keep_alive)
    keep_alive_thread.daemon = True
    keep_alive_thread.start()
    
    # Start web server
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting CleanBotByTelegram on port {port}")
    app.run(host='0.0.0.0', port=port)
