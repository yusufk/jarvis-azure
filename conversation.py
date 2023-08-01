# A class for the brain of the AI assistant keeping track of a conversation as a series of dialogues in a circular buffer.
import datetime
import json
import os
import logging
import openai
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureTextCompletion

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info("Conversation class loaded...")

class Conversation:
    def __init__(self, user_id=None):
         # Get environment variables from .env file
        load_dotenv()
        self.path = os.getenv("PERSISTENCE_PATH","/volumes/persist/")
        # Create a semantic kernel
        self.kernel = sk.Kernel()
        # Prepare OpenAI service using credentials stored in the `.env` file
        azure_openapi_key, azure_openapi_endpoint, azure_openapi_deployment_name, azure_openapi_version = os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_API_BASE"), os.getenv("ENGINE"), os.getenv("OPENAI_API_VERSION")
        self.kernel.add_text_completion_service("dv", AzureTextCompletion(azure_openapi_key, azure_openapi_endpoint, azure_openapi_deployment_name, azure_openapi_version,logger=logger))

        # Create the Application and pass it your bot's token.
        self.context = "The following is a conversation with an AI assistant, Jarvis. Jarvis has a personality like the Marvel character he's named after. He is curious, helpful, creative, very witty and a bit sarcastic."


    def get_answer(self, prompt=None):
        prompt = self.kernel.create_semantic_function(prompt)
        return prompt()


def main():
    # Test the Conversation class
    conv = Conversation("Yusuf")
    print(conv.get_answer(prompt="What is your motivation?"))
    print(conv.get_answer(prompt="List my previous questions?"))
    print(conv.get_answer(prompt="Who are you?"))
# If main.py is run as a script, run the main function
if __name__ == "__main__":
    main()    
