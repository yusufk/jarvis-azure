# A class for the brain of the AI assistant keeping track of a conversation as a series of dialogues in a circular buffer.
import datetime
import json
import os
import logging      
import asyncio
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureTextCompletion, AzureTextEmbedding

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info("Conversation class loaded...")

class Conversation:
    def __init__(self, user_id="Human"):
        self.user_id = user_id
         # Get environment variables from .env file
        load_dotenv()
        self.path = os.getenv("PERSISTENCE_PATH","/volumes/persist/")
        self.token_limit = int(os.getenv("CONTEXT_TOKEN_LIMIT",(4097-1024)))
        self.openai_temp = os.getenv("TEMPERATURE")
        self.openai_top_p = os.getenv("TOP_PROB") 

        # Create a semantic kernel
        self.kernel = sk.Kernel()

        # Prepare OpenAI service using credentials stored in the `.env` file
        azure_openapi_key, azure_openapi_endpoint, azure_openapi_deployment_name, azure_openapi_version = os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_API_BASE"), os.getenv("ENGINE"), os.getenv("OPENAI_API_VERSION")
        self.kernel.add_text_completion_service("dv", AzureTextCompletion(api_key=azure_openapi_key, endpoint=azure_openapi_endpoint, deployment_name=azure_openapi_deployment_name, api_version=azure_openapi_version,logger=logger))
        self.kernel.add_text_embedding_generation_service("ada", AzureTextEmbedding(deployment_name="embedding-deployment",api_key=azure_openapi_key, endpoint=azure_openapi_endpoint,logger=logger))
        
        # Now lets add some memory
        self.kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())
        self.kernel.import_skill(sk.core_skills.TextMemorySkill())

        # Setup the context for memories
        self.context = self.kernel.create_new_context()
        self.context[sk.core_skills.TextMemorySkill.COLLECTION_PARAM] = "aboutMe"
        self.context[sk.core_skills.TextMemorySkill.RELEVANCE_PARAM] = 0.8
        self.context["chat_history"] = ""
        
        # Setup the prompt.
        sk_prompt = """The following is a friendly conversation between a human and an AI called Jarvis. Jarvis has a personality like the Marvel character he's named after. He is curious, helpful, creative, very witty and a bit sarcastic.
        If he does not know the answer to a question, he truthfully says he does not know. Jarvis uses the current chat and information from previous conversations and does not hallucinate.
        
        Jarvis remembers:
         - $memories {{recall $memories}}

        Chat:
        {{$chat_history}}

        """+self.user_id+""": {{$user_input}}
        Jarvis: """

        prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
            max_tokens=int(self.token_limit), temperature=float(self.openai_temp), top_p=float(self.openai_top_p)
        )

        prompt_template = sk.PromptTemplate(
            sk_prompt, self.kernel.prompt_template_engine, prompt_config
        )

        function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
        self.chat_function = self.kernel.register_semantic_function("ChatBot", "Chat", function_config)

    async def load_memories_from_file(self):
        # Open file if it exists
        memory_file = self.path+"memory_"+self.user_id+".jsonl"
        if os.path.isfile(memory_file):
            logger.info("Loading memories from file..."+memory_file)
            with open(memory_file, "r") as f:
                for line in f:
                    line = json.loads(line)
                    # if the user prompt offers any info about the user, save it to memory
                    if "user_input" in line:
                        # Check if the user input is a question or a statement
                        if not line["user_input"].endswith("?"):
                            # Check if the statement contains I am or I'm or my
                            #if "i am" in line["user_input"] or "i'm" in line["user_input"] or "my" in line["user_input"].lower():
                            await self.kernel.memory.save_information_async("memories", text=line["user_input"], context=self.context)


    async def get_answer(self, prompt=None):
        self.context["user_input"] = prompt
        answer = await self.chat_function.invoke_async(context=self.context)
        self.context["chat_history"] += self.user_id+f": {prompt}\nJarvis: {answer}\n\n"
        return answer.result

async def main():
    # Test the Conversation class
    conv = Conversation("Yusuf")
    await conv.load_memories_from_file()
    print(await conv.get_answer(prompt="What is your motivation?"))
    print(await conv.get_answer(prompt="List my previous questions?"))
    print(await conv.get_answer(prompt="Who are you?"))
    print(await conv.get_answer(prompt="Really, who are you?"))
# If main.py is run as a script, run the main function
if __name__ == "__main__":
    asyncio.run(main())
