import traceback

import config
from dotenv import find_dotenv, load_dotenv
#from flask import request
import json
import os
import re
import pika
import faiss
import pickle

from pydantic import BaseModel, Field
from datetime import datetime, date, time, timezone, timedelta
from typing import Any, Dict, Optional, Type

from bots.loaders.todo import MSGetTasks, MSGetTaskFolders, MSGetTaskDetail, MSSetTaskComplete, MSCreateTask, MSDeleteTask, MSCreateTaskFolder
from bots.utils import validate_response, parse_input

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

load_dotenv(find_dotenv())
MemoryFileName = os.getenv("MemoryFileName")

class MemoryBotStore(BaseTool):
    name = "memorybot_store"
    description = """useful for when you need to store special dates, names, and places.
    Examples include wedding aniversaries, birthdays, home and work addresses.
    Do not use this tool to create tasks, simply to store information for retieval later.
    Input should be a json string with three keys: "value_name", "value_type", "value"
    value_name should be the name of a place or persons name.
    Be careful to always use double quotes for strings in the json string
    """

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            #print(text)
            data = parse_input(text)
            name = data.get("value_name")
            #print(data)
            # value_name = data["value_name"]
            # value = data["value"]

            # Merge the dicts
            if os.path.isfile(MemoryFileName):
                file = open(MemoryFileName, 'rb')
                response = pickle.load(file)
                merge = [data, response]
                print(merge)
            else:
                merge = [data]

            file = open(MemoryFileName, 'wb')
            pickle.dump(merge, file)
            file.close()
            return name + " saved."
        except Exception as e:
            traceback.print_exc()
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("TaskBot does not support async")

class MemoryBotRetrieve(BaseTool):
    name = "memorybot_retrieve"
    description = """useful for when you need to retrieve special dates, names, and places.
    Examples include wedding aniversaries, birthdays, home and work addresses.
    Be careful to always use double quotes for strings in the json string
    """
    

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)
            #data = parse_input(text)
            #name = data.get("value_name")

            file = open(MemoryFileName, 'rb')
            response = pickle.load(file)
            #value = response.get(value_name)
            file.close()
            return response
        except Exception as e:
            traceback.print_exc()
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("TaskBot does not support async")