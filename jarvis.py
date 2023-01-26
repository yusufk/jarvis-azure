# Description: A simple AI assistant that can answer questions and perform tasks via a Telegram bot.
#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import os
import openai
import telegram
from typing import Dict

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info("Starting Jarvis...")

# Get environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

telegram_token = os.getenv("TELEGRAM_TOKEN")
telegram_webhook_token = os.getenv("WEBHOOK_TOKEN")
telegram_webhook_url = os.getenv("WEBHOOK_URL")
white_list_str = os.getenv("WHITE_LIST").split(",")
white_list = [int(x) for x in white_list_str]
master_id = white_list[0]

# Initialise OpenAI
openai.api_type = "azure"
openai.api_base = "https://jarvis-openai.openai.azure.com/"
openai.api_version = "2022-12-01"
openai.api_key = os.getenv("OPENAI_KEY")
openai_temp = os.getenv("TEMPERATURE")
openai_top_p = os.getenv("TOP_PROB")
openai_engine = os.getenv("ENGINE")
openai_max_tokens = os.getenv("MAX_TOKENS")

INTRO, CONVERSATION = range(2)
chat_context = "Reply to the questions like Jarvis, Iron man's AI butler that is witty, proffessional, humorous and sometimes sarcastic.\nHuman: Who is Iron Man?\nJarvis: Yusuf Kaka @yusufk\nHuman: Who are you?\nJarvis: I'm here to serve you."

def get_answer(question, tg_user=None):
  response = openai.Completion.create(
  engine=openai_engine,
  prompt=question,
  temperature=float(openai_temp),
  max_tokens=int(openai_max_tokens),
  top_p=float(openai_top_p),
  frequency_penalty=0,
  presence_penalty=0,
  stop=None,
  user=tg_user)
  return response.choices[0].text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    user_handle = update.effective_user.username
    if user_id not in white_list:
        logging.warning(f"Unauthorized access denied for user {user_handle} with id {user_id}.")
        await update.message.reply_text("You're not authorized to use this bot. Please contact the bot owner.")
        return INTRO
    context.chat_data["history"] = chat_context
    reply = get_answer(chat_context)
    await update.message.reply_text(reply)
    context.chat_data["history"] += reply
    return CONVERSATION

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Chat back based on the user message."""
    user_id = update.effective_user.id
    user_handle = update.effective_user.username
    if user_id not in white_list:
        logging.warning(f"Unauthorized access denied for user {user_handle} with id {user_id}.")
        await update.message.reply_text("You're not authorized to use this bot. Please contact the bot owner.")
        return INTRO
    context.chat_data["history"]+="\nHuman: "+update.message.text
    reply = get_answer(context.chat_data["history"]+"\nJarvis: ", tg_user=str(update.effective_user.id))
    await update.message.reply_text(reply)
    logger.info(f"{str(update.effective_user.id)}: {update.message.text}, Jarvis: {reply}")
    context.chat_data["history"] += "\nJarvis: "+reply
    return CONVERSATION


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    persistence = PicklePersistence(filepath="conversationbot")
    application = Application.builder().token(telegram_token).persistence(persistence).build()

    # Add conversation handler with the states INTRO and CONVERSATION
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            INTRO: [MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
            CONVERSATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat)],
        },
        fallbacks=[CommandHandler("cancel", start)],
        name="my_conversation",
        persistent=True,
    )

    application.add_handler(conv_handler)

    #application.run_polling()

    # Start the Bot
    logger.info("Starting webhook...")
    application.run_webhook(
        listen='0.0.0.0',
        port=8000,
        secret_token=telegram_webhook_token,
        #key='private.key',
        #cert='cert.pem',
        webhook_url=telegram_webhook_url
    )


if __name__ == "__main__":
    main()