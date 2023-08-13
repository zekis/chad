import traceback
import config
import os

from datetime import datetime
from tempfile import TemporaryDirectory
import time 
import json

import faiss
from sys import exit
import asyncio
import threading

from bots.rabbit_handler import RabbitHandler
from common.rabbit_comms import publish, publish_action, consume, publish_input_card, get_input, send_prompt, send_to_bot
#from bots.langchain_todo import TaskBot
#from bots.langchain_search import SearchBot


from bots.loaders.google import GoogleBot
from bots.loaders.assistant import Help
from bots.loaders.web import WebBot
from bots.loaders.todo import MSGetTasks, MSGetTaskFolders, MSGetTaskDetail, MSSetTaskComplete, MSCreateTask, MSDeleteTask, MSCreateTaskFolder, MSUpdateTask
from bots.loaders.data import GetCredentials, GetCredential, CreateCredential, UpdateCredential, DeleteCredential, CredentialManager
from bots.loaders.calendar import MSGetCalendarEvents, MSGetCalendarEvent, MSCreateCalendarEvent
from bots.loaders.planner import PlannerBot
from bots.loaders.todo import scheduler_get_task_due_today, scheduler_get_bots_unscheduled_task
from bots.loaders.outlook import scheduler_check_emails
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

from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.agents import load_tools, Tool
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from langchain.prompts import MessagesPlaceholder
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.callbacks import StdOutCallbackHandler





class openaai_master:

    def __init__(self):
        
        #Check Config
        self.config_graph()
        self.config_openai(config.RESET_CONFIG)
        config.RESET_CONFIG = False

        #Init AI
        self.llm = ChatOpenAI(model_name='gpt-4', temperature=0, verbose=True)
        self.handler = RabbitHandler()
        self.tools = self.load_chads_tools(self.llm)

        #Always include these tools
        self.plannerBot = PlannerBot()
        self.helperBot = Help()
        self.plannerBot.init(self.tools)
        self.helperBot.init(self.tools)
        self.tools.append(self.plannerBot)
        self.tools.append(self.helperBot)

        #Publish tools to Human
        available_tools = f"""The following tools have been loaded \n"""
        for tool in self.tools:
            available_tools = available_tools + f"- {tool.name} \n"
        publish(available_tools)

        #Initate Agent Executor
        self.chat_history = MessagesPlaceholder(variable_name="chat_history")
        self.memory = ConversationBufferWindowMemory(memory_key="chat_history", k=6, return_messages=True)
        self.agent_executor = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            max_iterations=12, early_stopping_method="generate",
            memory=self.memory,
            agent_kwargs = {
                "memory_prompts": [self.chat_history],
                "input_variables": ["input", "agent_scratchpad", "chat_history"]
            })

    def config_graph(self):
        #Init Settings/Config
        self.planner_mode = False
        credentials = CredentialManager(config.DATA_DIR, config.USER_ID)
        credentials.load_credentials()
        response = credentials.get_credential('graph_api')
        #print(f"Credential {config.DATA_DIR} {config.USER_ID} {response}")

        #Office API Login
        if response:
            credentials.delete_credential('graph_api')
        credentials.add_credential('graph_api', {"application_id": config.APP_ID, "application_password": config.APP_PASSWORD, "tenantID": config.TENANT_ID, "main_resource": config.OFFICE_USER} )
        credentials.save_credentials()

        

    def config_openai(self, reset=False):
        #GPT API Key
        credentials = CredentialManager(config.DATA_DIR, config.USER_ID)
        credentials.load_credentials()
        if reset:
            credentials.delete_credential('openai_api')
            
        cred = credentials.get_credential('openai_api')
        if cred:
            cred_openAI_api_key = json.loads(cred)
            config.OPENAI_API_KEY = cred_openAI_api_key['parameters']['key']
            os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
        else:
            #No openai api key, Better get the key before doing anything
            publish_input_card("Please enter your OpenAI API Key", [{"label": "OpenAI GPT-4.0 Key (Type 'config' if you need to change this later)", "id": "config_value"}] )
            response = get_input(0)
            if response:
                print(response)
                credentials.add_credential('openai_api', {"key": response})
                config.OPENAI_API_KEY = response
                os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
                credentials.save_credentials()
                publish("Config updated. restart bot using bot_restart")
                exit()
            else:
                raise "Could not set OpenAI api key"
                exit()
    #Main Loop
    def model_response(self):
        planner = self.planner_mode
        try:
            msg = consume()
            
            if msg:
                question = msg
                if question == 'memory':
                    response = f"Memory: {len(self.memory.buffer)}\n{self.memory.buffer}"
                    publish(response)
                elif question == 'action':
                    response = "test action"
                    publish_action(response,"continue","pass")
                else:
                    current_date_time = datetime.now() 
                    if planner:
                        revised_plan = self.plannerBot.get_plan_input(question)
                        if revised_plan != 'stop':
                            inital_prompt = f'''Thinking step by step and with only the tools and assistants provided and with the current date and time of {current_date_time},
                            Please assist using the following steps as a guide: {revised_plan}
                            To reach the objective: {question}
                            '''
                            response = self.agent_executor.run(input=inital_prompt, callbacks=[self.handler])
                        else:
                            publish("Ok, let me know if I can be of assistance.")
                    else:
                        inital_prompt = f'''Thinking step by step and With only the tools provided and with the current date and time of {current_date_time} help the human with the following request, Request: {question} '''
                        response = self.agent_executor.run(input=inital_prompt, callbacks=[self.handler])
                    print(f"Memory: {len(self.memory.buffer)}")
        except Exception as e:
            traceback.print_exc()
            publish( f"An exception occurred: {e}")
            

    def process_task_schedule(self):
        while True:
            task = scheduler_get_task_due_today(config.Todo_BotsTaskFolder)
            if not task:
                break
            else:
                publish(f"Looks like one of my tasks is due - {task.subject}")
                current_date_time = datetime.now() 
                try:
                    inital_prompt = f'''With only the tools provided and with the current date and time of {current_date_time}, help the human with the following request, Request: {task.subject} - {task.body}'''
                    response = self.agent_executor.run(input=inital_prompt, callbacks=[self.handler])
                    task.body = response
                    task.mark_completed()
                    task.save()
                except Exception as e:
                    publish( f"An exception occurred: {e}")

        while True:
            task = scheduler_get_bots_unscheduled_task(config.Todo_BotsTaskFolder)
            if not task:
                break
            else:
                publish(f"Looks like one of my tasks is due - {task.subject}")
                current_date_time = datetime.now() 
                try:
                    inital_prompt = f'''With only the tools provided and with the current date and time of {current_date_time}, help the human with the following request, Request: {task.subject} - {task.body}'''
                    response = self.agent_executor.run(input=inital_prompt, callbacks=[self.handler])
                    task.body = response
                    task.mark_completed()
                    task.save()
                except Exception as e:
                    publish( f"An exception occurred: {e}")

    def process_email_schedule(self):
        scheduler_check_emails()

    
    def load_chads_tools(self, llm) -> list():
        
        tools = load_tools(["human"], input_func=get_input, prompt_func=send_prompt, llm=llm)
        
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
        
        tools.append(GetCredentials())
        tools.append(GetCredential())
        tools.append(CreateCredential())
        tools.append(UpdateCredential())
        tools.append(DeleteCredential())
        
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

        return tools

    