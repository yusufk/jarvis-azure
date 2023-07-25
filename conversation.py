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
from langchain.chains import ConversationChain
from langchain.memory import (ConversationKGMemory, ConversationBufferMemory,
    CombinedMemory,
    ConversationSummaryMemory, VectorStoreRetrieverMemory)
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
import pinecone

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
        embeddings = OpenAIEmbeddings(deployment=os.getenv("EMBEDDING_ENGINE"))

        # initialize pinecone
        pinecone.init(
            api_key=os.getenv("PINECONE_API_KEY"),  # find at app.pinecone.io
            environment=os.getenv("PINECONE_ENV")  # next to api key in console
        )

        index_name = "jarvis"
        vectorstore = Pinecone(index=pinecone.Index(index_name), embedding_function=embeddings.embed_query, text_key="text",namespace=user_id)

        retriever = vectorstore.as_retriever()

        # Create an instance of Azure OpenAI
        llm = AzureOpenAI(deployment_name=os.getenv("ENGINE") , temperature=self.openai_temp, top_p=self.openai_top_p)

        # Create a prompt template
        path = os.getenv("PERSISTENCE_PATH","/volumes/persist/")
        contextFile=(path+"context.txt")
        if os.path.exists(contextFile):
            with open(contextFile, "r") as f:
                self.context = f.read()
        template = """The following is a friendly conversation between a human with user id="""+self.user_id+""" and an AI called Jarvis. 
        """+self.context+"""
        Conversation summary:
        {summary}        

        Relevant memories:
        {relevant}

        Current conversation:
        {history}
        """+self.user_id+""": {input}
        Jarvis:"""
        prompt = PromptTemplate(input_variables=["history", "relevant", "summary", "input"], template=template)
       
        conv_memory = ConversationBufferMemory(memory_key="history", input_key="input")

        summary_memory = ConversationSummaryMemory(llm=llm, input_key="input", memory_key="summary")

        #kgmemory = ConversationKGMemory(llm=llm, input_key="input", memory_key="relevant")

        persisted_memory = VectorStoreRetrieverMemory(retriever=retriever, input_key="input", memory_key="relevant")

        # Combined
        memory = CombinedMemory(memories=[conv_memory, summary_memory, persisted_memory])

        self.conversation = ConversationChain(
            llm=llm, verbose=True, prompt=prompt, memory=memory
        )

    def get_answer(self, prompt=None):
        # Get the answer from the model chain
        return self.conversation.predict(input=prompt)
    
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
    print(conv.get_answer(prompt="What is my name?"))
    print(conv.get_answer(prompt="What is your motivation?"))
    print(conv.get_answer(prompt="List my previous questions?"))
    print(conv.get_answer(prompt="Who are you?"))
# If main.py is run as a script, run the main function
if __name__ == "__main__":
    main()    
