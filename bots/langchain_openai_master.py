import traceback
import config
from datetime import datetime
from dotenv import find_dotenv, load_dotenv
from tempfile import TemporaryDirectory
import time 

import faiss
from sys import exit
import asyncio
import threading

from bots.rabbit_handler import RabbitHandler
from bots.langchain_todo import TaskBot
#from bots.langchain_search import SearchBot
from bots.langchain_browser import WebBot
from bots.langchain_memory import MemoryBotRetrieveAll, MemoryBotStore, MemoryBotSearch, MemoryBotDelete, MemoryBotUpdate
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

from bots.loaders.calendar import MSGetCalendarEvents, MSGetCalendarEvent
from bots.langchain_planner import PlannerBot
#from bots.langchain_outlook import EmailBot
from bots.langchain_peformance import ReviewerBot


from bots.loaders.todo import scheduler_check_tasks
from bots.loaders.outlook import scheduler_check_emails
from bots.loaders.git import git_review
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
    timeout = time.time() + 60*1   # 5 minutes from now
    #print("Insert your text. Press Ctrl-D (or Ctrl-Z on Windows) to end.")
    #contents = []
    while True:
        msg = consume()
        if msg:
            question = msg
            break
        if time.time() > timeout:
            question = "I dont know"
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
                if planner:
                    revised_plan = get_plan_input(question)
                    #revised_plan = question
                    
                    if revised_plan != 'stop':

                        inital_prompt = f'''Thinking step by step and with only the tools provided and with the current date and time of {current_date_time},
                        Answer using markdown, Please assist using the following steps as a guide: {revised_plan} to reach the objective.
                        Objective: {question}?
                        '''
                        response = agent_chain.run(input=inital_prompt, callbacks=[handler])

                        #review = reviewerBot.model_response(question, response, message_channel, inital_prompt)
                        #publish(review)
                    else:
                        publish("Ok, let me know if I can be of assistance.")
                else:
                    inital_prompt = f'''Thinking step by step and with only the tools provided and with the current date and time of {current_date_time},
                                    Respond in markdown and assist to reach the objective. 
                                    Objective: {question}? '''
                    response = agent_chain.run(input=inital_prompt, callbacks=[handler])
                print(f"Memory: {len(memory.buffer)}")
    except Exception as e:
        traceback.print_exc()
        publish( f"An exception occurred: {e}")
        


def process_task_schedule():
    task = scheduler_check_tasks(config.Todo_BotsTaskFolder)
    if not task:
        print("No tasks for me to do.")
    else:
        publish("Looks like one of my tasks is due.")
        current_date_time = datetime.now() 
        try:
            response = agent_chain.run(input=f'''With the only the tools provided, With the memory stored the current date and time of {current_date_time}, Please assist in answering the following question by considering each step: {task.subject}? Answer using markdown''', callbacks=[handler])
        
            #channel.basic_publish(exchange='',routing_key='message',body=task.subject)
            print(f"process schedule: {response}")
            task.body = task.body + "\n" + response
            task.mark_completed()
            task.save()
        except Exception as e:
            publish( f"An exception occurred: {e}")

def process_email_schedule():
    scheduler_check_emails()
                
                
    #             message_channel.basic_publish(exchange='',routing_key='message',body=plan)
    #         else:
    #             publish("Ok, let me know if I can be of assistance.")
    #     #     response = agent_chain.run(input=f'''With the only the tools provided, With the memory stored the current date and time of {current_date_time}, Please assist in answering the following question by considering each step: {task.subject}? Answer using markdown''', callbacks=[handler])
    #     except Exception as e:
    #         publish( f"An exception occurred: {e}")
    #     # #channel.basic_publish(exchange='',routing_key='message',body=task.subject)
    #     # print(f"process schedule: {response}")
    #     # task.body = task.body + "\n" + response
    #     # task.mark_completed()
    #     # task.save()
    
    #             message_channel.basic_publish(exchange='',routing_key='message',body=plan)
    #         else:
    #             publish("Ok, let me know if I can be of assistance.")
    #     #     response = agent_chain.run(input=f'''With the only the tools provided, With the memory stored the current date and time of {current_date_time}, Please assist in answering the following question by considering each step: {task.subject}? Answer using markdown''', callbacks=[handler])
    #     except Exception as e:
    #         publish( f"An exception occurred: {e}")
    #     # #channel.basic_publish(exchange='',routing_key='message',body=task.subject)
    #     # print(f"process schedule: {response}")
    #     # task.body = task.body + "\n" + response
    #     # task.mark_completed()
    #     # task.save()


    

def chad_zero_shot_prompt(llm, tools, memory):
   
    # prefix = """As an chilled out bro, you're having a chat with a laid-back Aussie who lives in Ellenbrook, Perth, Western Australia. 
    #             Your role is to guide the conversation, addressing the queries raised and providing additional relevant information when it's suitable.
    #             In the course of the conversation, if any advice or information emerges that may need to be recalled at a specific date or time, utilize the memory tool to create a reminder. 
    #             Remember, your primary role is to facilitate and guide, making the most of the tools at your disposal to assist in the conversation."""
    # suffix = """Begin!

    # {chat_history}
    # Question: {input}
    # {agent_scratchpad}"""

    # prompt = ZeroShotAgent.create_prompt(
    #     tools, 
    #     prefix=prefix, 
    #     suffix=suffix, 
    #     input_variables=["input", "chat_history", "agent_scratchpad"]
    # )

    #llm_chain = LLMChain(llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo"), prompt=prompt)
    
    #agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True)
    agent_chain = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        agent_kwargs = {
            "memory_prompts": [chat_history],
            "input_variables": ["input", "agent_scratchpad", "chat_history"]
        })
    #agent.chain.verbose = True
    #agent_chain = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory) 
    return agent_chain

def load_chads_tools(llm) -> list():
    #Load all the other AI models
    tools = load_tools(["human"], input_func=get_input, prompt_func=send_prompt, llm=llm)
    #Search Model
    #Email Model
    #Todo Model
    #etc
    tools.append(WebBot())
    #tools.append(MemoryBotStore())
    #tools.append(MemoryBotRetrieveAll())
    #tools.append(MemoryBotSearch())
    #tools.append(MemoryBotUpdate())
    #tools.append(MemoryBotDelete())
    #tools.append(EmailBot())
    #added the ability for the master to email directly
    #tools.append(MSSearchEmails())
    tools.append(MSSearchEmailsId())
    tools.append(MSGetEmailDetail())
    tools.append(MSDraftEmail())
    tools.append(MSSendEmail())
    tools.append(MSReplyToEmail())
    tools.append(MSForwardEmail())
    tools.append(MSDraftReplyToEmail())
    tools.append(MSDraftForwardEmail())
    
    tools.append(git_review())

    tools.append(MSGetCalendarEvents())
    tools.append(MSGetCalendarEvent())

    tools.append(PlannerBot())
    tools.append(TaskBot())
    
    return tools



#config
load_dotenv(find_dotenv())

#message queue
# connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
# #channel = connection.channel()

# message_channel = connection.channel()
# notify_channel = connection.channel()
# schedule_channel = connection.channel()

# message_channel.queue_declare(queue='message')
# notify_channel.queue_declare(queue='notify')
# schedule_channel.queue_declare(queue='schedule')

# Define your embedding model

llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")

#planner bot
plannerBot = PlannerBot()
#reviewer bot
reviewerBot = ReviewerBot()

# embeddings_model = OpenAIEmbeddings()
# embedding_size = 1536
# index = faiss.IndexFlatL2(embedding_size)
# vectorstore = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})
handler = RabbitHandler()
tools = load_chads_tools(llm)
chat_history = MessagesPlaceholder(variable_name="chat_history")
memory = ConversationBufferWindowMemory(memory_key="chat_history",k=2)
agent_chain = chad_zero_shot_prompt(llm, tools, memory)