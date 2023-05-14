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

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain import ConversationChain, LLMChain, PromptTemplate
from langchain.chat_models import ChatOpenAI

from langchain.memory import ConversationBufferWindowMemory
from langchain.tools import BaseTool

load_dotenv(find_dotenv())


class ReviewerBot(BaseTool):
    name = "REVIEW"
    description = """useful for when you want to review your peformance reaching the objective.  
    """

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            notify_channel = connection.channel()
            notify_channel.queue_declare(queue='notify')

            return self.model_response(text, notify_channel)
        except Exception as e:
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("PlannerBot does not support async")

    #this bot needs to provide similar commands as autoGPT except the commands are based on Check Email, Check Tasks, Load Doc, Load Code etc.
    def model_response(self, text, response, notify_channel):
        try:
            #config
            load_dotenv(find_dotenv())

            # Define embedding model
            #prompt = "You are a planner who is an expert at coming up with a todo list."
            #template = "Come up with a todo list for this objective: {text}"
            #chat = OpenAI(temperature=0)
            #connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            #notify_channel = connection.channel()
            #notify_channel.queue_declare(queue='notify')
            handler = RabbitHandler(notify_channel)

            template="""You are a performance reviewer bro who reviews the final response to see if it met the objective and see if the task should be redone.
            Objective: {objective}
            Response: {response}
            """
            prompt = PromptTemplate(
                input_variables=["objective", "response"], 
                template=template
            )

            chatgpt_chain = LLMChain(
                llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo"), 
                prompt=prompt, 
                verbose=True,
                callbacks=[handler]
            )

            response = chatgpt_chain.run(objective=text, response=response, callbacks=[handler])
            return response
        except Exception as e:
            traceback.print_exc()
            return( f"An exception occurred: {e}")


