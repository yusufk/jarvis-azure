# A class for the brain of the AI assistant keeping track of a conversation as a series of dialogues in a circular buffer.
import datetime
import json
import os
import logging
import openai
from dotenv import load_dotenv
# Import Azure OpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain.llms import AzureOpenAI
from langchain import LLMChain
from langchain.chains import LLMChain, ConversationChain
from langchain.chains.conversation.memory import (ConversationBufferMemory, 
                                                  ConversationSummaryMemory, 
                                                  ConversationBufferWindowMemory,
                                                  ConversationKGMemory)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info("Conversation class loaded...")

class Conversation:
    def __init__(self, user_id="Human"):
        self.user_id = user_id
        # Initialize OpenAI API
        load_dotenv()
        openai.api_type = os.getenv("OPENAI_API_TYPE")
        openai.api_base = os.getenv("OPENAI_API_BASE")
        openai.api_version = os.getenv("OPENAI_API_VERSION")
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.token_limit = int(os.getenv("CONTEXT_TOKEN_LIMIT",(4097-1024)))
        self.openai_temp = os.getenv("TEMPERATURE")
        self.openai_top_p = os.getenv("TOP_PROB") 

        # Create a new conversation
        self.context = "Jarvis has a personality like the Marvel character he's named after. He is curious, helpful, creative, very witty and a bit sarcastic. If the AI does not know the answer to a question, it truthfully says it does not know."
        self.examples = self.get_from_file("training.jsonl")
        template = "The following is a conversation with an AI assistant, Jarvis.\n{context}\n{examples}\n{chat_history}"+self.user_id+": {human_input}\nJarvis: "
        prompt = PromptTemplate(template=template, input_variables=["context", "examples", "chat_history", "human_input"])

        # Create an instance of Azure OpenAI
        self.llm = AzureOpenAI(deployment_name=os.getenv("ENGINE") , temperature=self.openai_temp, top_p=self.openai_top_p)
        self.conversation = LLMChain(
        llm=self.llm,
        prompt=prompt,
        memory=ConversationBufferMemory(memory_key="chat_history", input_key="human_input", ai_prefix="Jarvis", human_prefix=self.user_id),
        )

    def get_answer(self, prompt=None):
        # Get the answer from the model chain
        return self.conversation.predict(context=self.context, examples=self.examples, human_input=prompt)
    
    def get_from_file(self, memory_file):
        history = ""
        with open(memory_file, "r") as f:
            for line in f:
                line = json.loads(line)
                history+=(line["prompt"].replace("Human: ",self.user_id+": "))+("\n")
                history+=(line["completion"].rstrip('\n'))+("\n\n")
        return history

def main():
    # Test the Conversation class
    conv = Conversation("Yusuf")
    print(conv.get_answer(prompt="What is your motivation?"))
    print(conv.get_answer(prompt="List my previous questions?"))
    print(conv.get_answer(prompt="Who are you?"))
# If main.py is run as a script, run the main function
if __name__ == "__main__":
    main()    
