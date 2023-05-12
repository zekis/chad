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

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain import OpenAI, ConversationChain, LLMChain, PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.tools import BaseTool

load_dotenv(find_dotenv())


class PlannerBot(BaseTool):
    name = "PLANNER"
    description = """useful for when you need to breakdown objectives into a list of tasks. 
    Input: an objective to create a todo list for. 
    Output: a todo list for that objective. 
    Please be very clear what the objective is!
    """

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)
            return self.model_response(text)
        except Exception as e:
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("PlannerBot does not support async")

    #this bot needs to provide similar commands as autoGPT except the commands are based on Check Email, Check Tasks, Load Doc, Load Code etc.
    def model_response(self, text):
        try:
            #config
            load_dotenv(find_dotenv())

            # Define embedding model
            #prompt = "You are a planner who is an expert at coming up with a todo list."
            #template = "Come up with a todo list for this objective: {text}"

            #chat = OpenAI(temperature=0)

            template="""You are a planner who is an expert at coming up with a todo list for the following objective: {objective}
            """
            prompt = PromptTemplate(
                input_variables=["objective"], 
                template=template
            )

            chatgpt_chain = LLMChain(
                llm=OpenAI(temperature=0), 
                prompt=prompt, 
                verbose=True, 
            )

            response = chatgpt_chain.run(objective=text)
            return response
        except Exception as e:
            traceback.print_exc()
            return( f"An exception occurred: {e}")


