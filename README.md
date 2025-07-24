Jarvis - An Advanced AI Assistant
============================

Jarvis is an experimental AI assistant that explores various approaches to artificial intelligence, natural language processing, and cognitive architectures. Built as a Telegram bot, it serves as a platform for testing different LLM models, frameworks, and cognitive architectures.

Key Features
-----------
- 🤖 Advanced conversation capabilities using Azure OpenAI
- 🏠 Home Assistant integration for IoT control
- 📈 Stock analysis and visualization
- 🔍 Web search and information retrieval
- 🧠 Memory and context persistence
- 🤔 Internal thought processes and reasoning

Project Branches
--------------
The project contains several experimental branches, each exploring different aspects of AI:

- `main`: Stable release with core functionality
- `home-assistant`: Integration with Home Assistant for IoT control
- `autogen`: Implementation using Microsoft's AutoGen framework
- `autogen_memory`: Enhanced memory capabilities using AutoGen
- `central_thoughts`: Exploration of internal thought processes
- `langchain`: Integration with LangChain framework
- `semantic-kernel`: Microsoft Semantic Kernel implementation
- `tools`: Various tool integrations and utilities
- `stock-images`: Stock market analysis and visualization features

Prerequisites
------------
- Python 3.10 or higher
- Poetry for dependency management
- Azure OpenAI API access
- Telegram Bot Token (from [BotFather](https://t.me/botfather))
- (Optional) Home Assistant instance for IoT control

Installation
-----------
1. Clone the repository:
   ```bash
   git clone https://github.com/yusufk/jarvis-azure.git
   cd jarvis-azure
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Create a `.env` file in the project root with required environment variables:
   ```env
   TELEGRAM_TOKEN=your_telegram_bot_token
   AZURE_OPENAI_API_KEY=your_azure_openai_key
   AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
   # Optional for Home Assistant integration
   MCP_HOST_URL=your_home_assistant_url
   MCP_AUTH_TOKEN=your_home_assistant_token
   ```

Configuration
------------
1. Set up your Azure OpenAI deployments:
   - Create a deployment for chat completion (e.g., GPT-4)
   - Configure the deployment name in your environment variables

2. For Home Assistant integration (optional):
   - Ensure your Home Assistant instance is accessible
   - Generate a long-lived access token from Home Assistant
   - Configure the URL and token in your environment variables

Running the Bot
--------------
1. Start the bot:
   ```bash
   poetry run python jarvis.py
   ```

2. Available commands in Telegram:
   - `/start` - Initialize the bot
   - `/clear` - Clear conversation history
   - `/status` - Check bot status
   - Just chat normally for other interactions

Features in Detail
----------------
### Core Capabilities
- Natural conversation using Azure OpenAI's models
- Persistent memory across conversations
- Contextual understanding and response generation
- Tool integration for extended functionality

### Home Assistant Integration
- Control smart home devices
- Query device states
- Execute automation scripts
- Monitor sensors and systems

### Stock Analysis
- Real-time stock price analysis
- Historical data visualization
- Trend analysis and basic predictions

### Cognitive Architecture
- Internal thought processes
- Self-reflection capabilities
- Memory management and context awareness
- Tool usage reasoning

Contributing
-----------
Contributions are welcome! Feel free to:
- Submit bug reports or feature requests through issues
- Create pull requests for improvements
- Experiment with new branches for different approaches

License
-------
This project is licensed under the MIT License - see the LICENSE file for details.
