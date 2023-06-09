import traceback

import config
from dotenv import find_dotenv, load_dotenv
#from flask import request
import json
import os
import re
import pika
import faiss

from pydantic import BaseModel, Field
from datetime import datetime, date, time, timezone, timedelta
from typing import Any, Dict, Optional, Type

from bots.rabbit_handler import RabbitHandler
from common.rabbit_comms import publish, publish_email_card, publish_list, publish_draft_card, publish_draft_forward_card

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

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from langchain.tools import StructuredTool
from langchain.docstore.document import Document


#from langchain import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore import InMemoryDocstore
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain import OpenAI, LLMChain, PromptTemplate

class EmailBot(BaseTool):
    name = "EMAILER"
    #MSCreateEmail, MSGetEmailDetail, MSSearchEmails
    description = """To use this tool, you must provide step by step instructions
    This tool contains the following abilities:
    1. search through emails and get a summary.
    2. search through emails and get their IDs.
    3. get the email content for a single email or email chain.
    4. create a new email.
    5. auto reply to an existing email chain.
    Use this more than the memory search for emails questions.
    """
    #return_direct= True

    def _run(self, text: str, ConversationID: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)
            
            return self.model_response(text)
        except Exception as e:
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("EmailBot does not support async")

    #this bot needs to provide similar commands as autoGPT except the commands are based on Check Email, Check Tasks, Load Doc, Load Code etc.
    def model_response(self, text):
        try:
            #config
            # load_dotenv(find_dotenv())
            # connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            # notify_channel = connection.channel()
            # notify_channel.queue_declare(queue='notify')
            handler = RabbitHandler()
            
            # Define embedding model
            llm = ChatOpenAI(temperature=0)
            #embeddings_model = OpenAIEmbeddings()
            #embedding_size = 1536
            #index = faiss.IndexFlatL2(embedding_size)
            #vectorstore = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})

            tools = self.load_tools(llm)
            agent_chain = self.zero_shot_prompt(llm, tools)

            
            current_date_time = datetime.now() 
            response = agent_chain.run(input=f'''With the current date and time of {current_date_time} answer the following: {text}? Answer using markdown''', callbacks=[handler])
            return response
        except Exception as e:
            traceback.print_exc()
            return( f"An exception occurred: {e}")

    def zero_shot_prompt(self, llm, tools):
    
        prefix = f"""As an assistant that likes reading and writing office emails for {config.OFFICE_USER}, answering the following questions using markdown in australian localisation formating as best you can. You have access to the following tools:"""
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
        
        # connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        # notify_channel = connection.channel()
        # notify_channel.queue_declare(queue='notify')
        # handler = RabbitHandler(notify_channel)

        llm_chain = LLMChain(llm=OpenAI(temperature=0), prompt=prompt)
        memory = ConversationBufferMemory(memory_key="chat_history")
        #agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True)
        #agent.chain.verbose = True
        #agent_chain = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory) 
        agent_chain = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            memory=memory,
            verbose=True)

        return agent_chain


    def load_tools(self, llm) -> list():
        tools = []
        tools.append(MSSearchEmailsId())
        tools.append(MSGetEmailDetail())
        tools.append(MSDraftEmail())
        tools.append(MSSendEmail())
        tools.append(MSReplyToEmail())
        tools.append(MSForwardEmail())
        tools.append(MSDraftReplyToEmail())
        tools.append(MSDraftForwardEmail())
        
        #tools.append(git_review())

        tools.append(MSGetCalendarEvents())
        tools.append(MSGetCalendarEvent())
        
        return tools



