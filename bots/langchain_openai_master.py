import traceback
import config
from datetime import datetime
from dotenv import find_dotenv, load_dotenv
from tempfile import TemporaryDirectory
import time 
import json

import faiss
from sys import exit
import asyncio
import threading

from bots.rabbit_handler import RabbitHandler
#from bots.langchain_todo import TaskBot
#from bots.langchain_search import SearchBot

from bots.langchain_browser import WebBot
from bots.langchain_google import GoogleBot

#from bots.langchain_memory import MemoryBotRetrieveAll, MemoryBotStore, MemoryBotSearch, MemoryBotDelete, MemoryBotUpdate
from bots.langchain_assistant import Help

from bots.loaders.todo import MSGetTasks, MSGetTaskFolders, MSGetTaskDetail, MSSetTaskComplete, MSCreateTask, MSDeleteTask, MSCreateTaskFolder, MSUpdateTask
from bots.langchain_credential_manager import GetCredentials, GetCredential, CreateCredential, UpdateCredential, DeleteCredential, CredentialManager
from bots.loaders.outlook import (
    MSSearchEmailsId,
    MSGetEmailDetail,
    MSDraftEmail,
    MSSendEmail,
    MSReplyToEmail,
    MSForwardEmail,
    MSDraftForwardEmail,
    MSDraftReplyToEmail
)

from bots.loaders.calendar import MSGetCalendarEvents, MSGetCalendarEvent, MSCreateCalendarEvent
from bots.langchain_planner import PlannerBot
#from bots.langchain_outlook import EmailBot
#from bots.langchain_peformance import ReviewerBot


from bots.loaders.todo import scheduler_get_task_due_today, scheduler_get_bots_unscheduled_task
from bots.loaders.outlook import scheduler_check_emails
from bots.loaders.git import git_review
from bots.langchain_toolman import ToolManGetTools, ToolManNewTool, ToolManStartTool, ToolManEditTool, ToolManTestTool, ToolManRemoveTool
from common.rabbit_comms import publish, publish_action, consume

#from bots.utils import encode_message, decode_message, encode_response, decode_response
from botbuilder.schema import (
    ActionTypes,
    CardImage,
    CardAction
)


from langchain.experimental import AutoGPT
from langchain.experimental import BabyAGI
from langchain.chat_models import ChatOpenAI

from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.agents import load_tools, Tool
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from langchain.prompts import MessagesPlaceholder
from langchain import OpenAI, LLMChain, PromptTemplate
#from langchain.llms import OpenAI
from langchain.agents import tool
from langchain.callbacks import StdOutCallbackHandler
# from langchain.tools.file_management import (
#     ReadFileTool,
#     CopyFileTool,
#     DeleteFileTool,
#     MoveFileTool,
#     WriteFileTool,
#     ListDirectoryTool,
# )
from langchain.agents.agent_toolkits import FileManagementToolkit
from langchain.vectorstores import FAISS
from langchain.docstore import InMemoryDocstore
from langchain.embeddings import OpenAIEmbeddings

#callbacks
def get_input():
    timeout = time.time() + 60*1   # 5 minutes from now
    #print("Insert your text. Press Ctrl-D (or Ctrl-Z on Windows) to end.")
    #contents = []
    while True:
        msg = consume()
        if msg:
            question = msg
            break
        if time.time() > timeout:
            question = "break"
            break
        time.sleep(0.5)
        #await asyncio.sleep(0.5)
    return question

#callbacks
def get_plan_input(question):
    timeout = time.time() + 60*5   # 1 minutes from now
    #Calculate plan
    plan = plannerBot.model_response(question, tools)
    #publish(plan)
    publish_action(plan,"continue","pass")
    publish("Would you like to make any changes to the plan above?")
    #loop until human happy with plan
    #contents = []
    while True:
        msg = consume()
        if msg:
            question = msg
            if question.lower() == "continue":
                return plan
            if question.lower() == "pass":
                return "stop"
            if question.lower() == "break":
                return "stop"
            else:
                new_prompt = f"Update the following plan: {plan} using the following input: {question}"
                plan = plannerBot.model_response(new_prompt, tools)
                publish_action(plan,"continue","pass")
                publish("Would you like to make any changes to the plan above?")
                timeout = time.time() + 60*5
        if time.time() > timeout:
            return "stop"
        time.sleep(0.5)
    return plan

def send_prompt(query):
    publish(query + "?")

#This code used a language model and tools to fire up additional models to solve tasks
def model_response():
    planner = False
    reviewer = False
    
    try:
        #history.predict(input=msg)
        msg = consume()
        
        if msg:
            question = msg
            #print(question)
            if question == 'memory':
                response = f"Memory: {len(memory.buffer)}\n{memory.buffer}"
                
                publish(response)
                #return response
            elif question == 'action':
                response = "test action"
                publish_action(response,"continue","pass")
                #return response
            else:
                current_date_time = datetime.now() 
                #assistants = get_assistants()
                if planner:
                    revised_plan = get_plan_input(question)
                    #revised_plan = question
                    
                    if revised_plan != 'stop':

                        inital_prompt = f'''Thinking step by step and with only the tools and assistants provided and with the current date and time of {current_date_time},
                        Please assist using the following steps as a guide: {revised_plan}
                        To reach the objective: {question}
                        '''
                        #publish(inital_prompt)
                        response = agent_executor.run(input=inital_prompt, callbacks=[handler])

                        #review = reviewerBot.model_response(question, response, message_channel, inital_prompt)
                        #publish(review)
                        #publish(f"Response: {response}")
                    else:
                        publish("Ok, let me know if I can be of assistance.")
                else:
#                     inital_prompt = f'''With only the tools and assistants provided and with the current date and time of {current_date_time},
#                                     Respond in markdown and assist to reach the objective. 
#                                     Always show the results, do not assume the human can see the previous response.
#                                     To use assistants, use the GET_ASSISTANTS to list the available assistants. use the ENGAGE_ASSISTANT tool
#                                     If an assistant is not available, use the HIRE_ASSISTANT tool. You must inlcude credentials as parameters value pairs if they are required.
                                    
# Objective: {question} '''

                    inital_prompt = f'''With only the tools provided and with the current date and time of {current_date_time},
                                    Respond in markdown and assist to reach the objective. 
                                    Always show the results, do not assume the human can see the previous response.
                                    
Objective: {question} '''
                    #publish(inital_prompt)
                    response = agent_executor.run(input=inital_prompt, callbacks=[handler])
                    #response = agent_executor.run(input=inital_prompt)
                    #publish(f"Response: {response}")
                print(f"Memory: {len(memory.buffer)}")
    except Exception as e:
        traceback.print_exc()
        publish( f"An exception occurred: {e}")
        
# def get_assistants():
#     GetAssistants = ToolManGetTools()
#     assistants_list = []
#     data_string = GetAssistants._run()
    
#     return data_string

def process_task_schedule():
    while True:
        task = scheduler_get_task_due_today(config.Todo_BotsTaskFolder)
        if not task:
            print("No scheduled tasks for me to do.")
            break
        else:
            publish(f"Looks like one of my tasks is due - {task.subject}")
            current_date_time = datetime.now() 
            try:
                inital_prompt = f'''With only the tools provided and with the current date and time of {current_date_time}, 
                Respond in markdown and assist to reach the objective. 
                Always show the results, do not assume the human can see the previous response.
                                    
Objective: {task.subject} '''
                
                response = agent_executor.run(input=inital_prompt, callbacks=[handler])
                #channel.basic_publish(exchange='',routing_key='message',body=task.subject)
                print(f"process task schedule: {response}")
                task.body = response
                task.mark_completed()
                task.save()
            except Exception as e:
                publish( f"An exception occurred: {e}")

    while True:
        task = scheduler_get_bots_unscheduled_task(config.Todo_BotsTaskFolder)
        if not task:
            print("No unscheduled tasks for me to do.")
            break
        else:
            publish(f"Looks like one of my tasks is due - {task.subject}")
            current_date_time = datetime.now() 
            try:
                inital_prompt = f'''With only the tools provided and with the current date and time of {current_date_time}, 
                Respond in markdown and assist to reach the objective. 
                Always show the results, do not assume the human can see the previous response.
                                    
Objective: {task.subject} '''
                
                response = agent_executor.run(input=inital_prompt, callbacks=[handler])
                #channel.basic_publish(exchange='',routing_key='message',body=task.subject)
                print(f"process task schedule: {response}")
                task.body = response
                task.mark_completed()
                task.save()
            except Exception as e:
                publish( f"An exception occurred: {e}")

def process_email_schedule():
    scheduler_check_emails()


def load_chads_tools(llm) -> list():
    #Load all the other AI models
    tools = load_tools(["human"], input_func=get_input, prompt_func=send_prompt, llm=llm)
    #Search Model
    #Email Model
    #Todo Model
    #etc
    tools.append(Help())
    tools.append(MSGetTaskFolders())
    tools.append(MSGetTasks())
    tools.append(MSGetTaskDetail())
    tools.append(MSSetTaskComplete())
    tools.append(MSCreateTask())
    tools.append(MSDeleteTask())
    tools.append(MSCreateTaskFolder())
    #tools.append(ToolManGetTools())
    #tools.append(ToolManNewTool())
    #tools.append(ToolManStartTool())
    #tools.append(ToolManEditTool())
    #tools.append(ToolManTestTool())
    #tools.append(ToolManRemoveTool())
    tools.append(GoogleBot())
    tools.append(WebBot())
    #tools.append(MemoryBotStore())
    #tools.append(MemoryBotRetrieveAll())
    #tools.append(MemoryBotSearch())
    #tools.append(MemoryBotUpdate())
    #tools.append(MemoryBotDelete())
    tools.append(GetCredentials())
    tools.append(GetCredential())
    tools.append(CreateCredential())
    tools.append(UpdateCredential())
    tools.append(DeleteCredential())
    #tools.append(EmailBot())

    tools.append(MSSearchEmailsId())
    tools.append(MSGetEmailDetail())
    tools.append(MSDraftEmail())
    tools.append(MSSendEmail())
    tools.append(MSReplyToEmail())
    tools.append(MSForwardEmail())
    tools.append(MSDraftReplyToEmail())
    tools.append(MSDraftForwardEmail())

    tools.append(MSGetCalendarEvents())
    tools.append(MSGetCalendarEvent())
    tools.append(MSCreateCalendarEvent())
    #added the ability for the master to email directly
    #tools.append(MSSearchEmails())
    

    tools.append(PlannerBot())
    #tools.append(TaskBot())

    return tools

def Init():
    
    credentials = CredentialManager(config.DATA_DIR, config.USER_ID)
    credentials.load_credentials()
    response = credentials.get_credential('graph_api')
    #print(f"Credential {config.DATA_DIR} {config.USER_ID} {response}")
    if response:
        credentials.delete_credential('graph_api')
    credentials.add_credential('graph_api', {"application_id": config.APP_ID, "application_password": config.APP_PASSWORD, "tenantID": config.TENANT_ID, "main_resource": config.OFFICE_USER} )
    credentials.save_credentials()

#llm = OpenAI(temperature=0)
llm = ChatOpenAI(model_name='gpt-4', temperature=0, verbose=True)
#planner bot
plannerBot = PlannerBot()
#reviewer bot
#reviewerBot = ReviewerBot()
#credential manager

# embeddings_model = OpenAIEmbeddings()
# embedding_size = 1536
# index = faiss.IndexFlatL2(embedding_size)
# vectorstore = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})
handler = RabbitHandler()
tools = load_chads_tools(llm)

#chat_history = MessagesPlaceholder(variable_name="chat_history")
#memory = ConversationBufferWindowMemory(memory_key="chat_history",k=2)
tool_names = [tool.name for tool in tools]
plannerBot.init(tools)

chat_history = MessagesPlaceholder(variable_name="chat_history")
memory = ConversationBufferWindowMemory(memory_key="chat_history", k=3, return_messages=True)
agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    max_iterations=12, early_stopping_method="generate",
    memory=memory,
    agent_kwargs = {
        "memory_prompts": [chat_history],
        "input_variables": ["input", "agent_scratchpad", "chat_history"]
    })
