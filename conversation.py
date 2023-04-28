# A class for the brain of the AI assistant keeping track of a conversation as a series of dialogues in a circular buffer.
import datetime
import json
import os
import logging
import openai
from dotenv import load_dotenv

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info("Conversation class loaded...")

class Dialogue:
    def __init__(self):
        self.question = ""
        self.answer = ""
        self.datetime = ""

    def set_question(self, question):
        self.question = question
        self.datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def set_answer(self, answer):
        self.answer = answer

    def get_question(self):
        return self.question
    
    def get_answer(self):
        return self.answer
    
    def get_datetime(self):
        return self.datetime

class Conversation:
    def __init__(self, user_id=None):
        # Get environment variables from .env file
        load_dotenv()
        openai.api_type = os.getenv("OPENAI_API_TYPE")
        openai.api_base = os.getenv("OPENAI_API_BASE")
        openai.api_version = os.getenv("OPENAI_API_VERSION")
        openai.api_key = os.getenv("OPENAI_API_KEY")
        # Create the Application and pass it your bot's token.
        self.context = "The following is a conversation with an AI assistant, Jarvis. Jarvis has a personality like the Marvel character he's named after. He is curious, helpful, creative, very witty and a bit sarcastic."
        self.memory = []
        self.token_limit = int(os.getenv("CONTEXT_TOKEN_LIMIT",(4097-1024))) # Token limit 4097 - 1024 for response
        self.memory_size = 50
        self.user_id = user_id
        self.openai_temp = os.getenv("TEMPERATURE")
        self.openai_top_p = os.getenv("TOP_PROB")
        self.openai_engine = os.getenv("ENGINE")
        self.openai_max_tokens = os.getenv("MAX_TOKENS")

    def get_answer(self, tg_user=None):
        try:
            response = openai.Completion.create(
            engine=self.openai_engine,
            prompt=self.get_complete_context(),
            temperature=float(self.openai_temp),
            max_tokens=int(self.openai_max_tokens),
            top_p=float(self.openai_top_p),
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            user=tg_user)
        # If the request is invalid due to too many tokens, purge a memory and try again
        except openai.error.InvalidRequestError as e:
            logger.error(f"Error: {e}")
            self.purge_a_memory()
            return self.get_answer(tg_user)
        # Return a generic response for any other error
        except Exception as e:
            logger.error(f"Error: {e}")
            return "I'm sorry, I'm not feeling well. I'll be back soon."
        return response.choices[0].text
        
    def add_to_memory(self, dialogue):
        while (len(self.memory) >= self.memory_size):
            self.purge_a_memory()
        self.memory.append(dialogue)
        self.archive_extra_memories()

    def purge_a_memory(self):
        self.add_to_training_file(self.memory[0])
        self.memory.pop(0)
        
    def get_memory(self):
        return self.memory

    def get_context(self):
        return self.context

    def populate_memory(self, memory_file):
        with open(memory_file, "r") as f:
            for line in f:
                dialogue = Dialogue()
                # Parse the json line into a dialogue object
                # e.g. {"prompt": "Human: Hello, pleased to meet you, my name is Yusuf", "completion": "Jarvis thinks: What a friendly person, looking forward to finding out more.\nJarvis: Hi Yusuf, it's a pleasure to meet you too."}
                line = json.loads(line)
                dialogue.set_question(line["prompt"].replace("Human: ",self.user_id+": "))
                dialogue.set_answer(line["completion"].rstrip('\n'))
                self.add_to_memory(dialogue)
    
    def add_to_training_file(self, dialogue):
        with open(self.path+"training_"+self.user_id+".jsonl", "a+") as f:
            f.write(json.dumps({"prompt": dialogue.get_question(), "completion": dialogue.get_answer()})+"\n")

    def get_complete_context(self):
        self.archive_extra_memories()
        complete_context = self.context+"\n\n"
        # iterate through memory and add to context
        for dialogue in self.memory:
            complete_context += dialogue.get_datetime()+"\n"
            complete_context += dialogue.get_question()+"\n"
            if dialogue.get_answer() != "":
                complete_context += dialogue.get_answer()+"\n\n"
            else:
                complete_context += "Jarvis: "
        logging.debug("Context: "+complete_context)
        return complete_context

    def archive_extra_memories(self):
        # Trim the context to the within the token limit
        context_size = len(self.context)
        for dialogue in self.memory:
            context_size += len(dialogue.get_question())+1
            if dialogue.get_answer() != "":
                context_size += len(dialogue.get_answer())+2
            else:
                context_size += 8

        while (context_size > self.token_limit*4):
            logging.debug("Context size: "+str(context_size)+", cutting a few dialogues from the memory...")
            self.add_to_training_file(self.memory[0])
            dialog = self.memory.pop(0)
            context_size -= len(dialog.get_question())+1 + len(dialog.get_answer())+2
    
    def set_context(self, context):
        self.context = context

    def set_context_from_file(self, contextFile):
        if os.path.exists(contextFile):
            with open(contextFile, "r") as f:
                self.context = f.read()

    def pretrain_using_file(self,filename):
        self.populate_memory(filename)


# If main.py is run as a script, run the main function
if __name__ == "__main__":
    conversation = Conversation('Me')
    conversation.set_context("The following is the internal conversation of an AI assistant, Jarvis. Jarvis has a personality like the Marvel character he's named after. He is curious, helpful, creative, very witty and a bit sarcastic.")
    conversation.pretrain_using_file("training.jsonl")
    dialog = Dialogue()
    dialog.set_question("Me: How do clocks work?")
    conversation.add_to_memory(dialog)
    dialog.set_answer(conversation.get_answer("Me"))
    print(conversation.get_complete_context())
    print(dialog.get_answer().replace('Jarvis: ','').replace("Me"+': ','').strip())
    
    
