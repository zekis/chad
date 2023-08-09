import traceback

import config
from dotenv import find_dotenv, load_dotenv
#from flask import request
import json
import os
import re
import pika
import faiss
import time

from pydantic import BaseModel, Field
from datetime import datetime, date, time, timezone, timedelta
from typing import Any, Dict, Optional, Type
from bots.rabbit_handler import RabbitHandler
from common.rabbit_comms import publish_actions, publish_email_card, publish_list, publish_draft_card, publish_draft_forward_card, send_to_bot
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain import ConversationChain, LLMChain, PromptTemplate
from langchain.chat_models import ChatOpenAI

from langchain.memory import ConversationBufferWindowMemory
from langchain.tools import BaseTool



class PlannerBot(BaseTool):
    name = "PLANNER"
    description = """useful for when you need to breakdown objectives into a list of tasks. 
    Input: an objective to create a todo list for. 
    Output: a todo list for that objective. 
    Please be very clear what the objective is!
    """
    return_direct= True
    tools = []

    def init(self, tools):
        self.tools = tools
    

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)

            

            plan = self.model_response(text, self.tools)
            buttons = [("Proceed", "Thinking step by step, action each of the following items in the plan using the tools available plan: "+ plan)]
            publish_actions(plan,buttons)
            #send_to_bot(config.USER_ID,plan)
            return "Done"
        except Exception as e:
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("PlannerBot does not support async")

    #this bot needs to provide similar commands as autoGPT except the commands are based on Check Email, Check Tasks, Load Doc, Load Code etc.
    def model_response(self, text, tools=None):
        try:
            #config
            
            
            current_date_time = datetime.now()
            handler = RabbitHandler()

            tool_details = ""
            for tool in tools:
                tool_details = tool_details + "\nName: " + tool.name + "\nDescription: " + tool.description + "\n"
            template="""You are a planner who can identify the right tool for the objective. If more then one tool is required, come up with a short todo lists of 1 to 5 tasks. 
            The objective is: {objective}.
            You have the following tools available {tools}
            """
            prompt = PromptTemplate(
                input_variables=["objective", "tools"], 
                template=template
            )

            chatgpt_chain = LLMChain(
                llm=ChatOpenAI(temperature=0), 
                prompt=prompt, 
                verbose=True,
                callbacks=[handler]
            )
            query = f"Given the current data and time of {current_date_time}, {text}"
            response = chatgpt_chain.run(objective=query, tools=tool_details)

            return response
        except Exception as e:
            traceback.print_exc()
            return( f"An exception occurred: {e}")


