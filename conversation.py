# A class for the brain of the AI assistant keeping track of a conversation as a series of dialogues in a circular buffer.
import json
import os

class Dialogue:
    def __init__(self):
        self.question = ""
        self.answer = ""

    def set_question(self, question):
        self.question = question
    
    def set_answer(self, answer):
        self.answer = answer

    def get_question(self):
        return self.question
    
    def get_answer(self):
        return self.answer
    
    def populate(self, reply):
        #self.answer = reply[reply.index("Jarvis: "):len(reply)].rstrip('\n')
        self.answer = reply.rstrip('\n')

class Conversation:
    def __init__(self, user_id=None):
        self.context = "The following is a conversation with an AI assistant named Jarvis. Jarvis has a personality like the Marvel character he's named after. He is curious, helpful, creative, very witty and a bit sarcastic."
        self.memory = []
        self.token_limit = 3106
        self.memory_size = 50
        self.user_id = user_id
        self.populate_memory("training.jsonl")
        self.tokens_used = len(self.get_complete_context())//4
        
    def add_to_memory(self, dialogue):
        if (len(self.memory) == self.memory_size):
            self.add_to_training_file(self.memory[0])
            self.memory.pop(0)
        self.tokens_used = len(self.get_complete_context())//4
        self.memory.append(dialogue)
        while (self.tokens_used > self.token_limit):
            self.add_to_training_file(self.memory[0])
            self.memory.pop(0)
            self.tokens_used = len(self.get_complete_context())//4
        
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
                dialogue.question = line["prompt"].replace("Human: ",self.user_id+": ")
                dialogue.populate(line["completion"])
                self.add_to_memory(dialogue)
    
    def add_to_training_file(self, dialogue):
        path = os.getenv("PERSISTENCE_PATH","/volumes/persist/")
        with open(path+"training_"+self.user_id+".jsonl", "w+") as f:
            f.write(json.dumps({"prompt": dialogue.get_question(), "completion": dialogue.get_answer()})+"\n")

    def get_complete_context(self):
        complete_context = self.context+"\n\n"
        # iterate through memory and add to context
        for dialogue in self.memory:
            complete_context += dialogue.get_question()+"\n"
            if dialogue.get_answer() != "":
                complete_context += dialogue.get_answer()+"\n\n"
            else:
                complete_context += "Jarvis: "
        return complete_context

# If main.py is run as a script, run the main function
if __name__ == "__main__":
    conversation = Conversation('1234')
    dialog = Dialogue()
    dialog.set_question("1234: Hello, pleased to meet you, my name is Yusuf")
    conversation.add_to_memory(dialog)
    print(conversation.get_complete_context())
    
    
