from langchain.experimental import AutoGPT
from langchain.chat_models import ChatOpenAI
from langchain.agents import load_tools
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain import OpenAI, LLMChain
from langchain.llms import OpenAI
from langchain.agents import tool

from langchain.tools.file_management import (
    ReadFileTool,
    CopyFileTool,
    DeleteFileTool,
    MoveFileTool,
    WriteFileTool,
    ListDirectoryTool,
)
from langchain.agents.agent_toolkits import FileManagementToolkit
from tempfile import TemporaryDirectory


from langchain.vectorstores import FAISS
from langchain.docstore import InMemoryDocstore
from langchain.embeddings import OpenAIEmbeddings

# Define your embedding model
embeddings_model = OpenAIEmbeddings()
# Initialize the vectorstore as empty
import faiss


load_dotenv(find_dotenv())


llm = OpenAI(temperature=0)
toolkit = FileManagementToolkit()
#toolkit.get_tools()
tools = load_tools(["wikipedia", "google-search", "llm-math", "requests_all"], llm=llm)
# Assuming the "human" tool is the first one in the list
# Set the custom prompt and input functions
tools.extend(toolkit.get_tools())

# tools.extend(tools.load_tools(
#     ["Human"],
#     input_func=get_input,
#     prompt_func=send_prompt
# ))

embedding_size = 1536
index = faiss.IndexFlatL2(embedding_size)
vectorstore = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})

prefix = """Have a conversation with a human, answering the following questions as best you can. You have access to the following tools:"""
suffix = """Begin!"

{chat_history}
Question: {input}
{agent_scratchpad}"""

prompt = ZeroShotAgent.create_prompt(
    tools, 
    prefix=prefix, 
    suffix=suffix, 
    input_variables=["input", "chat_history", "agent_scratchpad"]
)
#memory = ConversationBufferMemory(memory_key="chat_history")

#llm_chain = LLMChain(llm=OpenAI(temperature=0), prompt=prompt)
#agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True)
#agent_chain = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory) 
agent = AutoGPT.from_llm_and_tools(
    ai_name="Tom",
    ai_role="Assistant",
    tools=tools,
    llm=ChatOpenAI(temperature=0),
    memory=vectorstore.as_retriever()
)
# Set verbose to be true
agent.chain.verbose = True

#this bot needs to provide similar commands as autoGPT except the commands are based on Check Email, Check Tasks, Load Doc, Load Code etc.
def model_response(self, msg):
    try:
        #history.predict(input=msg)
        if msg == 'agent.template':
            response = "NA:"
            return response
        response = self.agent.run([msg])
        #history.chat_memory.add_ai_message(response)
        return response
    except Exception as e:
        return f"An exception occurred: {e}"