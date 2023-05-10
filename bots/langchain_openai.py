import traceback
import config
from datetime import datetime
from dotenv import find_dotenv, load_dotenv
import time
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
from bots.rabbit_handler import RabbitHandler
from bots.loaders.todo import MSGetTasks, MSGetTaskFolders, MSGetTaskDetail, MSSetTaskComplete, MSCreateTask, MSDeleteTask, scheduler_check_tasks

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

#this bot needs to provide similar commands as autoGPT except the commands are based on Check Email, Check Tasks, Load Doc, Load Code etc.
async def model_response():
    # print("Ready\n")
    # publish("bot1_online")
    # while True:
    try:
        #history.predict(input=msg)
        msg = consume()
        schedule_msg = consume_schedule()
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
                response = agent_chain.run(input=f"With the current date and time of {current_date_time} {question}? Answer using markdown", callbacks=[handler])
                #response = agent.run([question])
                #print("forwarding to AI")
                #response = baby_agi({"objective": question}, callbacks=[handler])
                #history.chat_memory.add_ai_message(response)
                print(response)
                #publish("How was that?")
    except Exception as e:
        traceback.print_exc()
        # if e == "KeyboardInterrupt":
        #     publish("bot1_offline")
        #     break
        # print( f"An exception occurred: {e}")
        publish( f"An exception occurred: {e}")
        
    time.sleep(0.5)

def publish(message):
    channel.basic_publish(exchange='',
                      routing_key='notify',
                      body=message)
    print(message)

async def process_schedule():
    #print("schedule")
    #await publish("Checking my tasks...")
    task = await scheduler_check_tasks(config.Todo_BotsTaskFolder,channel)
    if not task:
        publish("No tasks for me to do.")

def consume():
    method, properties, body = notify_channel.basic_get(queue='message', auto_ack=True)
    return body

def consume_schedule():
    method, properties, body = notify_channel.basic_get(queue='schedule', auto_ack=True)
    if body:
        print(f"schedule: {body}")
    return body

def chad_zero_shot_prompt(llm, tools, vectorstore):
   
    prefix = """As an AI you are having a conversation with a laid back aussie, answering the following questions using markdown in australian localisation formating as best you can. You have access to the following tools:"""
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
  

# def baby_chad_agi(vectorstore, tools):
#     prefix = """You are an AI who performs one task for an australian engineer based on the following objective: {objective}. Take into account these previously completed tasks: {context}."""
#     suffix = """Question: {task}
#     {agent_scratchpad}"""
#     prompt = ZeroShotAgent.create_prompt(
#         tools,
#         prefix=prefix,
#         suffix=suffix,
#         input_variables=["objective", "task", "context", "agent_scratchpad"],
#     )

#     llm = OpenAI(temperature=0)
#     llm_chain = LLMChain(llm=llm, prompt=prompt)
#     tool_names = [tool.name for tool in tools]
#     agent = ZeroShotAgent(llm_chain=llm_chain, allowed_tools=tool_names)
#     agent_executor = AgentExecutor.from_agent_and_tools(
#         agent=agent, tools=tools, verbose=True
#     )

#     # Logging of LLMChains
#     verbose = True
#     # If None, will keep on going forever
#     #max_iterations: Optional[int] = 3
#     baby_agi = BabyAGI.from_llm(
#         llm=llm, vectorstore=vectorstore, verbose=verbose, task_execution_chain=agent_executor
#         #, max_iterations=max_iterations
#         #task_execution_chain=agent_executor, 
#     )
#     return baby_agi


def load_chads_tools(llm, action_chain) -> list():
    #toolkit = FileManagementToolkit()
    #toolkit.get_tools()
    #tools = load_tools(["wikipedia", "google-search", "llm-math", "requests_all", "human"], input_func=get_input, prompt_func=send_prompt, llm=llm)
    tools = load_tools(["wikipedia", "google-search", "human"], input_func=get_input, prompt_func=send_prompt, llm=llm)
 
    # chad_chain_tool = Tool(
    #     name="TODO",
    #     func=action_chain.run,
    #     description="useful for when you need to come up with todo lists. Input: an objective to create a todo list for. Output: a todo list for that objective. Only use this for complex objectives. Please be very clear what the objective is!",
    # )
    # tools.append(chad_chain_tool)

    # schedule_tool = Tool(
    #     name="SCHEDULE",
    #     func=schedule,
    #     description="useful for creating sheduling a prompt for later. Input: the prompt to be scheduled and date and time ",
    # )

    # tools.append(schedule_tool)
    

    tools.append(MSGetTaskFolders())
    tools.append(MSGetTasks())
    tools.append(MSGetTaskDetail())
    tools.append(MSSetTaskComplete())
    tools.append(MSCreateTask())
    tools.append(MSDeleteTask())

    # for tool in tools:
    #     print(str(tool) + "\n\n")
    #tools.extend(toolkit.get_tools())

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
#
handler = RabbitHandler(notify_channel)


baby_chad_chain = action_chain(llm)
#load the tools for chad
tools = load_chads_tools(llm, baby_chad_chain)

#agent, agent_executor = baby_chad_agent(llm, tools)

#configure the baby chad ai
#baby_agi = baby_chad_agi(vectorstore, tools)
agent_chain = chad_zero_shot_prompt(llm, tools, vectorstore)