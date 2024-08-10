#!/usr/bin/env python
# This program is dedicated to the public domain under the CC0 license.

"""
An intelligent AI assistant that can answer questions and perform tasks via a Telegram bot powered by Azure OpenAI.
It uses the Updater class to handle the bot.
First, a few callback functions are defined. Then, those functions are passed to the Dispatcher and
registered at their respective places. Then, the bot is started and runs until we press Ctrl-C on the
command line.
Usage:
ConversationBot example, ConversationHandler and PicklePersistence.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import os
import telegram
from typing import Dict
from openai import AzureOpenAI
from dotenv import load_dotenv
import time

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
debug_level = os.getenv("DEBUG_LEVEL", "INFO")
if (debug_level == "DEBUG"):
    debug_level = logging.DEBUG
elif (debug_level == "INFO"):
    debug_level = logging.INFO
elif (debug_level == "WARNING"):
    debug_level = logging.WARNING
elif (debug_level == "ERROR"):
    debug_level = logging.ERROR
elif (debug_level == "CRITICAL"):
    debug_level = logging.CRITICAL
else:
    debug_level = logging.INFO
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=debug_level
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

CONVERSATION = range(1)

# Setup Azure Open AI
client = AzureOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),  
    api_version=os.getenv("OPENAI_API_VERSION"),
    azure_endpoint = os.getenv("OPENAI_API_BASE")
    )

# Initialise the context from the context.txt file if it exists
path = os.getenv("PERSISTENCE_PATH","/volumes/persist/")
if os.path.exists(path+"context.txt"):
    with open(path+"context.txt", "r") as f:
        context = f.read()
else:
    context = "You have a personality like the Marvel character Jarvis. You are curious, helpful, creative, very witty and a bit sarcastic."

# Create an assistant
assistant = client.beta.assistants.create(
    name="Jarvis",
    instructions=context,
    tools=[{"type": "code_interpreter"}],
    model=os.getenv("ENGINE")
)


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Chat back based on the user message."""
    user_id = str(update.effective_user.id)
    user_handle = update.effective_user.username
    user_first_name = update.effective_user.first_name
    user_last_name = update.effective_user.last_name
    if user_handle is None:
        user_handle = "Unknown"
    if user_first_name is None:
        user_first_name = "Unknown"
    if user_last_name is None:
        user_last_name = "Unknown"
    if update.effective_user.id not in white_list:
        logging.warning(f"Unauthorized access denied for user {user_handle} with id {user_id} and name {user_first_name} {user_last_name}.")
        await update.message.reply_text("You're not authorized to use this bot. Please contact the bot owner.")
        return CONVERSATION

    # Get the persisted context
    if ("conversation" in context.chat_data):
        conversation = context.chat_data["conversation"]
    else:
        # Create a new conversation
        logger.info(f"New user detected: {user_handle} with id {user_id}")
        conversation = client.beta.threads.create()

    # Add the user question to the thread
    message = client.beta.threads.messages.create(
        thread_id=conversation.id,
        role="user",
        content=update.message.text
    )

    # Run the thread
    run = client.beta.threads.runs.create(
    thread_id=conversation.id,
    assistant_id=assistant.id,
    )
    status = run.status

    # Wait till the assistant has responded
    while status not in ["completed", "cancelled", "expired", "failed"]:
        time.sleep(5)
        run = client.beta.threads.runs.retrieve(thread_id=conversation.id,run_id=run.id)
        status = run.status

    messages = client.beta.threads.messages.list(
    thread_id=conversation.id
    )
    message =  messages.data[0].content[0].text.value

    msgs = [message[i:i + 4096] for i in range(0, len(message), 4096)]
    for text in msgs:
        await update.message.reply_text(text=text)

    # Update persisted context
    context.chat_data["conversation"] = conversation
    logger.debug(f"{str(update.effective_user.id)} --> {update.message.text} , Jarvis: {message}")
    return CONVERSATION

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {str(update.effective_user.username)}!",
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear the conversation."""
    if update.effective_user.id != master_id:
        await update.message.reply_text("You're not authorized to use this bot. Please contact the bot owner.")
        return CONVERSATION
    context.chat_data["conversation"] = client.beta.threads.create()
    await update.message.reply_text("Conversation cleared.")
    logger.info(f"Conversation cleared by {update.effective_user.id}")
    return CONVERSATION

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    path = os.getenv("PERSISTENCE_PATH","./")
    persistence = PicklePersistence(filepath=path+"jarvis_brain.pkl")
    application = Application.builder().token(telegram_token).persistence(persistence).build()

    # Add conversation handler with the states INTRO and CONVERSATION
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, chat),CommandHandler("start", start)],
        states={
            CONVERSATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat)],
        },
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND, chat)],
        name="my_conversation",
        persistent=True,
    )
#    command_handler = CommandHandler("clear", clear)
#    application.add_handler(command_handler)
    application.add_handler(conv_handler)

    # Start the Bot
    run_as_polling = os.getenv("RUN_POLL", False)
    if run_as_polling:
        logger.info("Starting polling...")
        application.run_polling()
    else:
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