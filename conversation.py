# A class for the brain of the AI assistant keeping track of a conversation as a series of dialogues in a circular buffer.
import datetime
import json
import os
import logging
import openai
from dotenv import load_dotenv
# Import Azure OpenAI
from langchain.llms import AzureOpenAI
from langchain import OpenAI, ConversationChain, LLMChain, PromptTemplate
from langchain.memory import ConversationBufferMemory


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
        self.context = "Jarvis has a personality like the Marvel character he's named after. He is curious, helpful, creative, very witty and a bit sarcastic."
        self.template = """The following is a conversation with an AI assistant, Jarvis.\n{context}\n\n{history}\n{human_id}: {human_input}\nJarvis: """
        self.prompt = PromptTemplate(
            input_variables=["human_input"], 
            template=self.template,
            partial_variables={"context":self.context, "human_id":self.user_id, "history":self.get_history('./training.jsonl')}
        )
        # Create an instance of Azure OpenAI
        self.llm = AzureOpenAI(deployment_name=os.getenv("ENGINE") , model_name="text-davinci-003", temperature=self.openai_temp, top_p=self.openai_top_p)
        self.conversation_chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt,
            memory=ConversationBufferMemory(
                max_history=50,
                prompt_template=self.prompt,
                input_variables=["human_input"],
                output_variables=["jarvis_output"],
            ),
        )
    
    def get_answer(self, input=None):
        # Get the answer from the LLM chain
        return self.conversation_chain.predict(human_input=input)
    
    def get_history(self, memory_file):
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
    print(conv.get_answer(input="Hello, how are you?"))
    
# If main.py is run as a script, run the main function
if __name__ == "__main__":
    main()    
