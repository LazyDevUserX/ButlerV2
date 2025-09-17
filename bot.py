import os
import asyncio
from pyrogram import Client, filters
from pyrogram.enums import PollType

# --- Environment Variables ---
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
USERBOT_SESSION = os.environ.get("USERBOT_SESSION")
SOURCE_CHAT_ID = int(os.environ.get("SOURCE_CHAT_ID", 0))
DESTINATION_CHAT_ID = int(os.environ.get("DESTINATION_CHAT_ID", 0))

# Settings for the userbot, controlled by the frontend bot
forward_with_header = True

# --- Userbot (Backend) Client ---
# The session_string parameter is what makes this non-interactive.
app_user = Client("my_session", api_id=API_ID, api_hash=API_HASH, session_string=USERBOT_SESSION)

@app_user.on_message(filters.chat(SOURCE_CHAT_ID) & filters.poll)
async def handle_poll(client, message):
    if forward_with_header:
        # Option 1: Forward with header (normal forward)
        await client.forward_messages(DESTINATION_CHAT_ID, from_chat_id=message.chat.id, message_ids=message.id)
    else:
        # Option 2: Recreate poll without header
        poll_data = message.poll
        
        # Check if it's a quiz poll to get the correct answer and explanation
        if poll_data.is_quiz:
            correct_id = poll_data.correct_option_id
            explanation = poll_data.explanation
            await client.send_poll(
                chat_id=DESTINATION_CHAT_ID,
                question=poll_data.question,
                options=[o.text for o in poll_data.options],
                is_anonymous=poll_data.is_anonymous,
                allows_multiple_answers=poll_data.allows_multiple_answers,
                is_quiz=True,
                correct_option_id=correct_id,
                explanation=explanation
            )
        else:
            await client.send_poll(
                chat_id=DESTINATION_CHAT_ID,
                question=poll_data.question,
                options=[o.text for o in poll_data.options],
                is_anonymous=poll_data.is_anonymous,
                allows_multiple_answers=poll_data.allows_multiple_answers,
                is_quiz=False
            )

# --- Bot (Frontend) Client ---
app_bot = Client(":memory:", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

@app_bot.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text("Hello! I am your poll forwarder command center. Use /toggle_header to change settings.")

@app_bot.on_message(filters.command("toggle_header"))
async def toggle_header_command(client, message):
    global forward_with_header
    forward_with_header = not forward_with_header
    if forward_with_header:
        await message.reply_text("Forwarding mode changed: **With Header** (Normal Forward).")
    else:
        await message.reply_text("Forwarding mode changed: **Without Header** (Recreate Poll).")

# --- Main function to run both clients ---
async def main():
    await asyncio.gather(
        app_user.start(),
        app_bot.start()
    )

if __name__ == "__main__":
    asyncio.run(main())
