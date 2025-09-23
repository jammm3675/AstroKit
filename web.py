import os
import threading
import asyncio
from flask import Flask
from bot import main as run_bot

def start_bot_in_thread():
    """Creates a new event loop and runs the bot in it."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())

# Start the bot in a separate thread
bot_thread = threading.Thread(target=start_bot_in_thread)
bot_thread.daemon = True
bot_thread.start()

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 AstroKit Bot is running!"

@app.route('/health')
def health_check():
    return "OK", 200
