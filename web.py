import os
import threading
import asyncio
from flask import Flask

# A flag to ensure the bot is only started once
bot_started = False

def main_bot_logic():
    """
    This function will contain the logic to run the bot.
    We'll import the actual bot's main function and run it.
    """
    # We need to set up an asyncio event loop for the bot's thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # We will import the bot's main function later, once we modify bot.py
    from bot import main as run_bot
    loop.run_until_complete(run_bot())


# Create the Flask app
app = Flask(__name__)

@app.route('/')
def home():
    """A simple endpoint to confirm the web server is running."""
    return "Web server is running. Bot is in a background thread."

@app.route('/health')
def health_check():
    """Endpoint for Render's health checks."""
    return "OK", 200

# Start the bot in a background thread when the app is initialized.
# The `if not bot_started` check prevents the bot from being started multiple times
# by Gunicorn's multiple workers.
if not bot_started:
    bot_thread = threading.Thread(target=main_bot_logic)
    bot_thread.daemon = True
    bot_thread.start()
    bot_started = True