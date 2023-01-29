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
