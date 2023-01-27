# A class for the brain of the AI assistant keeping track of a conversation as a series of dialogues in a circular buffer.
import json

class Dialogue:
    def __init__(self):
        self.question = ""
        self.answer = ""
        self.thought = ""
    
    def set_thought(self, thought):
        self.thought = thought

    def get_thought(self):
        return self.thought

    def set_question(self, question):
        self.question = question
    
    def set_answer(self, answer):
        self.answer = answer

    def get_question(self):
        return self.question
    
    def get_answer(self):
        return self.answer
    
    def populate(self, reply):
        self.answer = reply[reply.index("Jarvis: "):len(reply)].rstrip('\n')
        self.thought = reply[reply.index("Jarvis thinks: "):reply.index("Jarvis: ")].rstrip('\n')

class Brain:
    def __init__(self):
        self.context = "The following is a conversation with an AI assistant called Jarvis, with personality like the Marvel character he's named after. The assistant is curious, helpful, creative, witty, proffessional, humorous and sometimes sarcastic. The AI assistant also has an internal dialogue as thoughts."
        self.memory = []
        self.memory_size = 50
        
    def add_to_memory(self, dialogue):
        if len(self.memory) == self.memory_size:
            self.memory.pop(0)
        self.memory.append(dialogue)
        
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
                # where the question is "Hello, pleased to meet you, my name is Yusuf" and the answer is "Hi Yusuf, it's a pleasure to meet you too. and the thought is "What a friendly person, looking forward to finding out more."
                # and the thought is "What a friendly person, looking forward to finding out more."
                line = json.loads(line)
                dialogue.question = line["prompt"]
                dialogue.populate(line["completion"])
                self.add_to_memory(dialogue)

    def get_complete_context(self):
        complete_context = self.context+"\n\n"
        # iterate through memory and add to context
        for dialogue in self.memory:
            complete_context += dialogue.get_question()+"\n"
            complete_context += dialogue.get_thought()+"\n"
            complete_context += dialogue.get_answer()+"\n\n"
        return complete_context

# Test the brain
brain = Brain()
brain.populate_memory("training.jsonl")
print(brain.get_complete_context())

    
    
