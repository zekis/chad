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

from bots.loaders.todo import MSGetTasks, MSGetTaskFolders, MSGetTaskDetail, MSSetTaskComplete, MSCreateTask, MSDeleteTask, MSCreateTaskFolder

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from langchain.tools import StructuredTool
from langchain import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore import InMemoryDocstore
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.agents import load_tools, Tool
from langchain.utilities import SerpAPIWrapper

load_dotenv(find_dotenv())


class PlannerBot(BaseTool):
    name = "PLANNER"
    description = """useful for when you need to breakdown objectives into a list of tasks. 
    Input: an objective to create a todo list for. 
    Output: a todo list for that objective. 
    Please be very clear what the objective is!
    """
    
    search = SerpAPIWrapper()

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)
            return model_response(text)
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
            llm = OpenAI(temperature=0)
            messages = [
                SystemMessage(content="You are a planner who is an expert at coming up with a todo list for a given objective."),
                HumanMessage(content=f"Come up with a todo list for this objective: {text}")
            ]
            response = llm(messages)
            return response
        except Exception as e:
            traceback.print_exc()
            return( f"An exception occurred: {e}")


