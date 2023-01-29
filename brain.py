# A Brain object that mimics the conciousness state
from dialogue import Dialogue

class Brain:
    def __init__(self):
        self.inner_dialogue = Dialogue()
        self.context = "The following are the thoughts of an AI assistant called Jarvis, with personality like the Marvel character he's named after. The assistant is curious, helpful, creative, witty, proffessional, humorous and sometimes sarcastic. \
            Jarvis is learning about the Universe through interactions with humans and developing a conciousness. stored in a brain object. "
        self.memory = []
        self.memory_size = 50