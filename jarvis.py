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
import traceback
from datetime import datetime
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
from telegram.error import TelegramError
import telegramify_markdown
from telegramify_markdown.customize import markdown_symbol
from telegramify_markdown.interpreters import BaseInterpreter, MermaidInterpreter
from telegramify_markdown.type import ContentTypes
import asyncio

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

ASSISTANT_ID = os.getenv("ASSISTANT_ID","asst_0123vPqpL2qQKhBa3iuZQczr")
try:
    assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
except Exception as e:
    logger.error(f"Failed to retrieve assistant: {e}")
    # Create an assistant
    assistant = client.beta.assistants.create(
        name="Jarvis",
        instructions=context,
        model=os.getenv("ENGINE"),
        temperature=os.getenv("TEMPERATURE", 0.7)
    )

async def send_formatted_message(update: Update, message: str) -> None:
    boxs = await telegramify_markdown.telegramify(
        content=message,
        interpreters_use=[BaseInterpreter(), MermaidInterpreter(session=None)],  # Render mermaid diagram
        latex_escape=True,
        normalize_whitespace=True,
        max_word_count=4096  # The maximum number of words in a single message.
    )
    for item in boxs:
        print("Sent one item")
        await asyncio.sleep(0.2)
        try:
            if item.content_type == ContentTypes.TEXT:
                logger.info("TEXT")
                await update.message.reply_text(
                    text=item.content,
                    parse_mode="MarkdownV2"
                )
            elif item.content_type == ContentTypes.PHOTO:
                logger.info("PHOTO")
                await update.message.reply_photo(
                    photo=item.file_data,
                    filename=item.file_name, 
                    caption=item.caption,
                    parse_mode="MarkdownV2",
                )
            elif item.content_type == ContentTypes.FILE:
                logger.info("FILE")
                await update.message.reply_document(
                    filename=item.file_name,
                    document=item.file_data,
                    caption=item.caption,
                    parse_mode="MarkdownV2"
                )
        except Exception as e:
            logger.error(f"Error: {item}")
            raise e


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
        await update.message.reply_text(text="You're not authorized to use this bot. Please contact the bot owner.", parse_mode='MarkdownV2')
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

    if status != "completed":
        logger.error(f"Assistant run failed with status {status}")
        await update.message.reply_text("I'm sorry, I'm having trouble understanding you right now. Please try again later.")
        return CONVERSATION

    messages = client.beta.threads.messages.list(
    thread_id=conversation.id
    )
    message =  messages.data[0].content[0].text.value
    logger.debug(f"Assistant response: {message}")

    msgs = [message[i:i + 4096] for i in range(0, len(message), 4096)]
    for text in msgs:
        #await update.message.reply_text(text=text)
        await send_formatted_message(update, text)

    # Update persisted context
    context.chat_data["conversation"] = conversation
    logger.debug(f"{str(update.effective_user.id)} --> {update.message.text} , Jarvis: {message}")
    return CONVERSATION

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {str(update.effective_user.username)}!\n
        I'm Jarvis, a personal assistant. How can I help you today?\n
        Written by @yusufk and powered by Azure OpenAI\n
        Source code available at: [GitHub](https://github.com/yusufk/jarvis-azure)\n",
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

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send status information including revision timestamp."""
    revision_timestamp = os.getenv("REVISION_TIMESTAMP", "Unknown")
    api_version = os.getenv("OPENAI_API_VERSION", "Unknown")
    engine = os.getenv("ENGINE", "Unknown")
    
    status_message = (
        "🤖 *Bot Status*\n\n"
        f"📅 Revision: `{revision_timestamp}`\n"
        f"🔄 API Version: `{api_version}`\n"
        f"⚙️ Engine: `{engine}`"
    )
    await update.message.reply_text(status_message)
    return CONVERSATION

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Extract error details
    error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_msg = f"⚠️ *Error Report*\n\n"
    error_msg += f"🕒 Time: `{error_time}`\n"
    
    if context.error:
        error_msg += f"❌ Error: `{str(context.error)[:100]}`\n"
        error_msg += f"📍 Location: `{traceback.format_tb(context.error.__traceback__)[-1][:100]}`"
    
    # Log the error
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        # Send error message to master user
        await context.bot.send_message(
            chat_id=master_id,
            text=error_msg,
            parse_mode='MarkdownV2'
        )
    except TelegramError as send_error:
        logger.error(f"Failed to send error message: {send_error}")

async def post_init_handler(application):
    try:
            revision = os.getenv("REVISION_TIMESTAMP", "Unknown")
            message = (
                f"🤖 *Jarvis Online*\n"
                f"🔄 Revision: `{revision}`\n"
                f"⚙️ Engine: `{os.getenv('ENGINE')}`\n"
                f"📅 Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
            )
            await application.bot.send_message(
                chat_id=master_id,
                text=message,
                parse_mode='MarkdownV2'
            )
    except Exception as e:
        logger.error(f"Startup notification failed: {e}")
    
def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    path = os.getenv("PERSISTENCE_PATH","./")
    persistence = PicklePersistence(filepath=path+"jarvis_brain.pkl")
    
    # application = Application.builder().token(telegram_token).persistence(persistence).build()
    # Initialize application with job queue
    application = (
        Application.builder()
        .token(telegram_token)
        .persistence(persistence)
        .post_init(post_init_handler)
        .concurrent_updates(True)
        .build()
    )

    # Add conversation handler with the states INTRO and CONVERSATION
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, chat)],
        states={
            CONVERSATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat)],
        },
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND, chat)],
        name="my_conversation",
        persistent=True,
    )
    # Other handlers
    start_handler = CommandHandler("start", start)
    clear_handler = CommandHandler("clear", clear)
    status_handler = CommandHandler("status", status)
    application.add_handler(clear_handler)
    application.add_handler(start_handler)
    application.add_handler(status_handler)
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

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