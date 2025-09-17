import asyncio
import os
import json
import logging
from telethon import TelegramClient, events, types
from telethon.errors import BadRequestError
from telethon.sessions import StringSession

# ---------------------------
# Logging setup
# ---------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# Load settings
# ---------------------------
SETTINGS_FILE = "settings.json"
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        settings = json.load(f)
else:
    settings = {"replace": True, "src": "source_chat", "dst": "target_chat"}
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

# ---------------------------
# Telegram API setup
# ---------------------------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# Initialize both clients
user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient('bot', API_ID, API_HASH)

# ---------------------------
# Poll copy helper
# ---------------------------
async def copy_poll(message, dst_chat):
    """Safely rebuild and send a poll from a message object."""
    try:
        orig = message.poll.poll

        new_poll = types.Poll(
            id=0,
            question=types.TextWithEntities(text=orig.question.text, entities=orig.question.entities or []),
            answers=[
                types.PollAnswer(
                    text=types.TextWithEntities(text=ans.text.text, entities=ans.text.entities or []),
                    option=ans.option
                )
                for ans in orig.answers
            ],
            multiple_choice=orig.multiple_choice,
            quiz=orig.quiz
        )

        solution = None
        solution_entities = None
        correct_answers = None
        
        # --- FIX: Correctly calculate the correct_answers from the results list ---
        if message.media.results:
            solution = message.media.results.solution
            solution_entities = message.media.results.solution_entities
            # Iterate through the results to find the correct one(s)
            if message.media.results.results:
                correct_answers = [res.option for res in message.media.results.results if res.correct]

        media = types.InputMediaPoll(
            poll=new_poll,
            correct_answers=correct_answers,
            solution=solution,
            solution_entities=solution_entities
        )

        await user_client.send_file(dst_chat, file=media)
        logger.info(f"✅ Poll from message {message.id} copied successfully")
        return True
    except Exception as e:
        logger.exception(f"⚠️ Poll copy for message {message.id} failed: {e}")
        return False

# ---------------------------
# /forward COMMAND
# ---------------------------
@bot_client.on(events.NewMessage(pattern=r'/forward (\d+) (\d+)', from_users=OWNER_ID))
async def forward_range_handler(event):
    start_id = int(event.pattern_match.group(1))
    end_id = int(event.pattern_match.group(2))

    if start_id > end_id:
        await event.respond("❌ **Error:** Start ID must be less than or equal to End ID.")
