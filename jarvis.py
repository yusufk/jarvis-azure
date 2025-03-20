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
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.messages import TextMessage
from autogen_core.tools import FunctionTool
from autogen_core import CancellationToken
from autogen_core.memory import MemoryContent, MemoryMimeType, ListMemory
from autogen_core.model_context import BufferedChatCompletionContext
from autogen_ext.memory.chromadb import ChromaDBVectorMemory, PersistentChromaDBVectorMemoryConfig
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

# Get environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Enable logging
debug_level = os.getenv("DEBUG_LEVEL", "DEBUG")
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

telegram_token = os.getenv("TELEGRAM_TOKEN")
telegram_webhook_token = os.getenv("WEBHOOK_TOKEN")
telegram_webhook_url = os.getenv("WEBHOOK_URL")
white_list_str = os.getenv("WHITE_LIST").split(",")
white_list = [int(x) for x in white_list_str]
master_id = white_list[0]

CONVERSATION = range(1)

client = AzureOpenAIChatCompletionClient(
    azure_deployment=os.getenv("AZURE_DEPLOYMENT_NAME"),
    model="o3-mini",
    api_version=os.getenv("AZURE_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_API_KEY")
)

# Initialise the context from the context.txt file if it exists
path = os.getenv("PERSISTENCE_PATH","/volumes/persist/")
if os.path.exists(path+"context.txt"):
    with open(path+"context.txt", "r") as f:
        context = f.read()
else:
    context = "You have a personality like the Marvel character Jarvis. You are curious, helpful, creative, very witty and a bit sarcastic."

def google_search(query: str, num_results: int = 2, max_chars: int = 500) -> list:  # type: ignore[type-arg]
    import requests
    from bs4 import BeautifulSoup

    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        raise ValueError("API key or Search Engine ID not found in environment variables")

    url = "https://customsearch.googleapis.com/customsearch/v1"
    params = {"key": str(api_key), "cx": str(search_engine_id), "q": str(query), "num": str(num_results)}

    response = requests.get(url, params=params)

    if response.status_code != 200:
        logger.debug(response.json())
        raise Exception(f"Error in API request: {response.status_code}")

    results = response.json().get("items", [])

    def get_page_content(url: str) -> str:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            words = text.split()
            content = ""
            for word in words:
                if len(content) + len(word) + 1 > max_chars:
                    break
                content += " " + word
            return content.strip()
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return ""

    enriched_results = []
    for item in results:
        body = get_page_content(item["link"])
        enriched_results.append(
            {"title": item["title"], "link": item["link"], "snippet": item["snippet"], "body": body}
        )
        time.sleep(1)  # Be respectful to the servers
    
    # Convert the response to a chat friendly, markdown format response
    response = ""
    for result in enriched_results:
        response += f"## {result['title']}\n\n"
        response += f"**Snippet:** {result['snippet']}\n\n"
        response += f"**Content:**\n{result['body']}\n\n"
        response += "---\n\n"  # Horizontal rule between results

    return response


def analyze_stock(ticker: str) -> dict:  # type: ignore[type-arg]
    import os
    from datetime import datetime, timedelta

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import yfinance as yf
    from pytz import timezone  # type: ignore

    stock = yf.Ticker(ticker)

    # Get historical data (1 year of data to ensure we have enough for 200-day MA)
    end_date = datetime.now(timezone("UTC"))
    start_date = end_date - timedelta(days=365)
    hist = stock.history(start=start_date, end=end_date)

    # Ensure we have data
    if hist.empty:
        return {"error": "No historical data available for the specified ticker."}

    # Compute basic statistics and additional metrics
    current_price = stock.info.get("currentPrice", hist["Close"].iloc[-1])
    year_high = stock.info.get("fiftyTwoWeekHigh", hist["High"].max())
    year_low = stock.info.get("fiftyTwoWeekLow", hist["Low"].min())

    # Calculate 50-day and 200-day moving averages
    ma_50 = hist["Close"].rolling(window=50).mean().iloc[-1]
    ma_200 = hist["Close"].rolling(window=200).mean().iloc[-1]

    # Calculate YTD price change and percent change
    ytd_start = datetime(end_date.year, 1, 1, tzinfo=timezone("UTC"))
    ytd_data = hist.loc[ytd_start:]  # type: ignore[misc]
    if not ytd_data.empty:
        price_change = ytd_data["Close"].iloc[-1] - ytd_data["Close"].iloc[0]
        percent_change = (price_change / ytd_data["Close"].iloc[0]) * 100
    else:
        price_change = percent_change = np.nan

    # Determine trend
    if pd.notna(ma_50) and pd.notna(ma_200):
        if ma_50 > ma_200:
            trend = "Upward"
        elif ma_50 < ma_200:
            trend = "Downward"
        else:
            trend = "Neutral"
    else:
        trend = "Insufficient data for trend analysis"

    # Calculate volatility (standard deviation of daily returns)
    daily_returns = hist["Close"].pct_change().dropna()
    volatility = daily_returns.std() * np.sqrt(252)  # Annualized volatility

    # Create result dictionary
    result = {
        "ticker": ticker,
        "current_price": current_price,
        "52_week_high": year_high,
        "52_week_low": year_low,
        "50_day_ma": ma_50,
        "200_day_ma": ma_200,
        "ytd_price_change": price_change,
        "ytd_percent_change": percent_change,
        "trend": trend,
        "volatility": volatility,
    }

    # Convert numpy types to Python native types for better JSON serialization
    for key, value in result.items():
        if isinstance(value, np.generic):
            result[key] = value.item()

    # Generate plot
    plt.figure(figsize=(12, 6))
    plt.plot(hist.index, hist["Close"], label="Close Price")
    plt.plot(hist.index, hist["Close"].rolling(window=50).mean(), label="50-day MA")
    plt.plot(hist.index, hist["Close"].rolling(window=200).mean(), label="200-day MA")
    plt.title(f"{ticker} Stock Price (Past Year)")
    plt.xlabel("Date")
    plt.ylabel("Price ($)")
    plt.legend()
    plt.grid(True)

    # Save plot to file
    os.makedirs("coding", exist_ok=True)
    plot_file_path = f"coding/{ticker}_stockprice.png"
    plt.savefig(plot_file_path)
    logger.debug(f"Plot saved as {plot_file_path}")
    result["plot_file_path"] = plot_file_path

    return result

# Setup tools

google_search_tool = FunctionTool(
    google_search, description="Search Google for information, returns results with a snippet and body content"
)
stock_analysis_tool = FunctionTool(analyze_stock, description="Analyze stock data and generate a plot")

# Setup Memory
# Initialize user memory
list_memory = ListMemory()

chroma_user_memory = ChromaDBVectorMemory(
    config=PersistentChromaDBVectorMemoryConfig(
        collection_name="memories",
        persistence_path=os.path.join(path, ".chromadb_autogen"),
        k=2,  # Return top  k results
        score_threshold=0.4,  # Minimum similarity score
    )
)

model_context = BufferedChatCompletionContext(buffer_size=50)

# Setup agents

agent = AssistantAgent(
    name="Jarvis",
    model_client=client,
    tools=[google_search_tool],
    system_message=context,
    #memory=[list_memory, chroma_user_memory],
    memory=[list_memory],
    reflect_on_tool_use=True,
    model_context=model_context
)

search_agent = AssistantAgent(
    name="Google_Search_Agent",
    model_client=client,
    tools=[google_search_tool],
    description="Search Google for information, returns top 2 results with a snippet and body content",
    system_message="You are a helpful AI assistant. Solve tasks using your tools.",
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
        logger.debug("Sent one item")
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
    if ("memory" in context.chat_data):
        # Existing conversation found, load it
        logger.info(f"Existing conversation found for user {user_handle} with id {user_id}")
        list_memory = context.chat_data["memory"]
    else:
        # Create a new conversation
        logger.info(f"New user detected: {user_handle} with id {user_id}")
        #list_memory = ListMemory()
        context.chat_data["memory"] = list_memory

    #content_timestamped = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " - " + update.message.text

    user_content=TextMessage(content=update.message.text, source="user")
    logger.debug(f"User-{user_handle}: {update.message.text}")

    # Add the user message to the conversation
    #conversation.append(user_content)

    # Get the assistant response
    response = await agent.on_messages(
        [user_content],
        cancellation_token=CancellationToken(),
    )
    # Debug messages in useful format
    logger.debug(f"Jarvis thoughts: {response.inner_messages}")
    logger.debug(f"Jarvis: {response.chat_message}")

    # Add to memory
    await list_memory.add(MemoryContent(content=update.message.text, mime_type=MemoryMimeType.TEXT,metadata={"user":user_id}))
    await list_memory.add(MemoryContent(content=response.chat_message.content, mime_type=MemoryMimeType.TEXT,metadata={"user":user_id}))

    #chroma_user_memory.add(MemoryContent(content=user_content, mime_type=MemoryMimeType.TEXT))
    #chroma_user_memory.add(MemoryContent(content=response.chat_message.content, mime_type=MemoryMimeType.TEXT))

    # Send the response to the user
    message =  response.chat_message.content
    logger.debug(f"Assistant response: {message}")

    msgs = [message[i:i + 4096] for i in range(0, len(message), 4096)]
    for text in msgs:
        await send_formatted_message(update, text)

    # Update persisted context
    #context.chat_data["conversation"] = conversation
    logger.debug(f"{str(update.effective_user.id)} --> {update.message.text} , Jarvis: {message}")
    return CONVERSATION

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(f"Hi {str(update.effective_user.username)}!\n\
    I'm Jarvis, a personal assistant. How can I help you today?\n\
    Written by @yusufkaka and powered by Azure OpenAI\n\
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
    engine = os.getenv("AZURE_DEPLOYMENT_NAME", "Unknown")
    
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
                f"⚙️ Engine: `{os.getenv('AZURE_DEPLOYMENT_NAME')}`\n"
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
    #application.add_error_handler(error_handler)

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