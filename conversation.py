# A class for the brain of the AI assistant keeping track of a conversation as a series of dialogues in a circular buffer.
import datetime
import json
import os
import logging
import openai
from dotenv import load_dotenv
# Import Azure OpenAI
from langchain.llms import AzureOpenAI


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info("Conversation class loaded...")

# Initialize OpenAI API
load_dotenv()
openai.api_type = os.getenv("OPENAI_API_TYPE")
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Create an instance of Azure OpenAI
llm = AzureOpenAI(deployment_name=os.getenv("ENGINE") , model_name="text-davinci-003")


def main():
    response = openai.Completion.create(
    engine="text-davinci-002-prod",
    prompt="This is a test",
    max_tokens=5
    )
    print(response)
    # Run the LLM
    llm("Tell me a joke")
    print(llm)
    
# If main.py is run as a script, run the main function
if __name__ == "__main__":
    main()    
