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
    #ConversationHandler,
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
logger.info("Telegram token: "+telegram_token)

# Initialise OpenAI
openai.api_type = "azure"
openai.api_base = "https://jarvis-openai.openai.azure.com/"
openai.api_version = "2022-12-01"
openai.api_key = os.getenv("OPENAI_KEY")

def get_answer(question):
  response = openai.Completion.create(
  engine="davinci2deployment",
  prompt="The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by OpenAI. How can I help you today?\nHuman: "+question+" AI: ",
  temperature=0,
  max_tokens=64,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0,
  stop=None)
  return response.choices[0].text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(get_answer(update.message.text))


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    persistence = PicklePersistence(filepath="conversationbot")
    application = Application.builder().token(telegram_token).persistence(persistence).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    #application.run_polling()

    application.run_webhook(
        listen='0.0.0.0',
        port=8000,
        secret_token=telegram_webhook_token,
        #key='private.key',
        #cert='cert.pem',
        webhook_url='https://jarvis-app.delightfulpond-bcd4c846.westeurope.azurecontainerapps.io'
    )


if __name__ == "__main__":
    main()