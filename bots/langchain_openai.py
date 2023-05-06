import config
from dotenv import find_dotenv, load_dotenv

from langchain.experimental import AutoGPT
from langchain.chat_models import ChatOpenAI
from langchain.agents import load_tools
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain import OpenAI, LLMChain
from langchain.llms import OpenAI
from langchain.agents import tool
from langchain.callbacks import StdOutCallbackHandler
from bots.rabbit_handler import RabbitHandler
from bots.loaders.todo import get_all_todo_tasks

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

import time #used to timeout the QnA callback
import pika
# Initialize the vectorstore as empty
import faiss



load_dotenv(find_dotenv())

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

message_channel = connection.channel()
notify_channel = connection.channel()

message_channel.queue_declare(queue='message')
notify_channel.queue_declare(queue='notify')
# Define your embedding model
embeddings_model = OpenAIEmbeddings()

llm = OpenAI(temperature=0)
toolkit = FileManagementToolkit()

def get_input():
    timeout = time.time() + 60*5   # 5 minutes from now
    #print("Insert your text. Press Ctrl-D (or Ctrl-Z on Windows) to end.")
    contents = []
    while True:
        msg = consume()
        if msg:
            question = msg.decode("utf-8")
            break
        if time.time() > timeout:
            question = "I dont know"
            break
        time.sleep(1)
    return question

def send_prompt(query):
    publish(query + "?")


#toolkit.get_tools()
tools = load_tools(["wikipedia", "google-search", "llm-math", "requests_all","human","terminal"], commands=["git","ls"], input_func=get_input, prompt_func=send_prompt, llm=llm)
tools.extend(toolkit.get_tools())
embedding_size = 1536
index = faiss.IndexFlatL2(embedding_size)
vectorstore = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})

prefix = """Have a conversation with a human in Australia, answering the following questions as best you can. You have access to the following tools:"""
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
memory = ConversationBufferMemory(memory_key="chat_history")
handler = RabbitHandler(notify_channel)
llm_chain = LLMChain(llm=OpenAI(temperature=0), prompt=prompt, callbacks=[handler])
agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True)
agent_chain = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory) 


#this bot needs to provide similar commands as autoGPT except the commands are based on Check Email, Check Tasks, Load Doc, Load Code etc.
def model_response():
    print("Ready\n")
    while True:
        try:
            #history.predict(input=msg)
            msg = consume()
            if msg:
                question = msg.decode("utf-8")
                if question == 'todo':
                    response = tasks_to_string(get_all_todo_tasks())
                    publish(response)
                    return response
                response = agent_chain.run(question, callbacks=[handler])
                #history.chat_memory.add_ai_message(response)
                publish(response)
        except Exception as e:
            print( f"An exception occurred: {e}")

def publish(message):
    channel.basic_publish(exchange='',
                      routing_key='notify',
                      body=message)
    print(message)

def consume():
    method, properties, body = notify_channel.basic_get(queue='message', auto_ack=True)
    return body

def tasks_to_string(task_list):
#list current tasks
    task_str = ""
    for task in task_list:
        print(task)
        task_str = task_str + "\n" + str(task)
    return task_str