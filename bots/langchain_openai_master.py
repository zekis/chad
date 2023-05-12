import traceback
import config
from datetime import datetime
from dotenv import find_dotenv, load_dotenv
import time
from tempfile import TemporaryDirectory
import time 
import pika
import faiss

from bots.rabbit_handler import RabbitHandler
from bots.langchain_todo import TaskBot
from bots.langchain_search import SearchBot
from bots.langchain_memory import MemoryBotRetrieve, MemoryBotStore
from bots.langchain_planner import PlannerBot

from bots.loaders.todo import scheduler_check_tasks

from langchain.experimental import AutoGPT
from langchain.experimental import BabyAGI
from langchain.chat_models import ChatOpenAI
from langchain.agents import load_tools, Tool
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.llms import OpenAI
from langchain.agents import tool
from langchain.callbacks import StdOutCallbackHandler
from langchain.tools.file_management import (
    ReadFileTool,
    CopyFileTool,
    DeleteFileTool,
    MoveFileTool,
    WriteFileTool,
    ListDirectoryTool,
)
from langchain.agents.agent_toolkits import FileManagementToolkit
from langchain.vectorstores import FAISS
from langchain.docstore import InMemoryDocstore
from langchain.embeddings import OpenAIEmbeddings

#callbacks
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
        time.sleep(0.5)
    return question

def send_prompt(query):
    publish(query + "?")

#This code used a language model and tools to fire up additional models to solve tasks
async def model_response():
    try:
        #history.predict(input=msg)
        msg = consume()
        
        if msg:
            question = msg.decode("utf-8")
            print(question)
            if question == 'ping':
                response = 'pong'
                publish(response)
                #return response
            elif question == 'restart':
                response = 'ok'
                publish(response)
                #return response
            else:
                current_date_time = datetime.now() 
                response = agent_chain.run(input=f'''With the memory stored and with the current date and time of {current_date_time}, Please assist in answering the following question by considering each step: {question}? Answer using markdown''', callbacks=[handler])
    except Exception as e:
        traceback.print_exc()
        publish( f"An exception occurred: {e}")
        

def publish(message):
    channel.basic_publish(exchange='',
                      routing_key='notify',
                      body=message)
    print(message)

async def process_schedule():
    task = await scheduler_check_tasks(config.Todo_BotsTaskFolder,channel)
    if not task:
        print("No tasks for me to do.")
    else:
        publish("Looks like one of my tasks is due.")
        current_date_time = datetime.now() 
        response = agent_chain.run(input=f'''With the memory stored the current date and time of {current_date_time}, Please assist in answering the following question by considering each step: {task.subject}? Answer using markdown''', callbacks=[handler])
        #channel.basic_publish(exchange='',routing_key='message',body=task.subject)
        print(f"process schedule: {response}")
        task.body = task.body + "\n" + response
        task.mark_completed()
        task.save()

def consume():
    method, properties, body = notify_channel.basic_get(queue='message', auto_ack=True)
    return body

def consume_schedule():
    method, properties, body = notify_channel.basic_get(queue='schedule', auto_ack=True)
    if body:
        print(f"schedule: {body}")
    return body

def chad_zero_shot_prompt(llm, tools, vectorstore):
   
    prefix = """As an AI, you are engaged in a conversation with a relaxed Aussie resident of Ellenbrook, Perth, Western Australia. 
    Your task is to address the following inquiries and/or suggest supplementary information, as appropriate.
    If the discussion leads to a recommendation or a piece of information that might need to be recalled at a specific date or time, please create a reminder using the Taskbot tool. 
    You have the following resources at your disposal:"""
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

    llm_chain = LLMChain(llm=OpenAI(temperature=0), prompt=prompt, callbacks=[handler])
    memory = ConversationBufferMemory(memory_key="chat_history")
    agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True)
    #agent.chain.verbose = True
    agent_chain = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory) 
    return agent_chain

def action_chain(llm) -> LLMChain:
    todo_prompt = PromptTemplate.from_template(
    "the current date is {datetime} and you are an assistant for an australian enginner who breaks down an objective into short lists of tasks. Come up with a short todo list for this objective: {objective}"
    )
    action_chain = LLMChain(llm=llm, prompt=todo_prompt)
    return action_chain

def load_chads_tools(llm, action_chain) -> list():
    #Load all the other AI models
    tools = load_tools(["human"], input_func=get_input, prompt_func=send_prompt, llm=llm)
    #Search Model
    #Email Model
    #Todo Model
    #etc
    tools.append(MemoryBotStore())
    tools.append(MemoryBotRetrieve())
    tools.append(PlannerBot())
    tools.append(TaskBot())
    tools.append(SearchBot())


    return tools



#config
load_dotenv(find_dotenv())

#message queue
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

message_channel = connection.channel()
notify_channel = connection.channel()
schedule_channel = connection.channel()

message_channel.queue_declare(queue='message')
notify_channel.queue_declare(queue='notify')
schedule_channel.queue_declare(queue='schedule')

# Define your embedding model
llm = OpenAI(temperature=0)

embeddings_model = OpenAIEmbeddings()
embedding_size = 1536
index = faiss.IndexFlatL2(embedding_size)
vectorstore = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})
handler = RabbitHandler(notify_channel)

baby_chad_chain = action_chain(llm)
tools = load_chads_tools(llm, baby_chad_chain)
agent_chain = chad_zero_shot_prompt(llm, tools, vectorstore)