Jarvis POC/Demo Telegram bot
===========================
This Telegram bot is my personal AI Assistant, primarily built to explore LLM's and how they can be used to enable AI assistants.

There are multiple branches with different experiments, using various LLM models. The most interesting are the ones where I've attempted to give the AI assistant the ability to have an internal conversation and develop it's own train of thought. My personal view is that this is an important component of conciousness. 

It is based on the [python-telegram-bot](http://python-telegram-bot.org/) library and is currently deployed on Azure using Azure Container App.

Installation
------------
To install the bot, you need to have Python 3.6 or higher installed on your system.
Then, you can install the required dependencies using poetry:
    `poetry install`

Usage
-----
To run the bot, you need to create a Telegram bot using the [BotFather](https://t.me/botfather).
Store environment variables in `.env` in the root of the project directory.
