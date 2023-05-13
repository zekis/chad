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
    name = "MEMORY_STORE"
    description = """useful for when you need to store personal preferences, favorite things, special dates, names, and places.
    Examples include favorite foods, music, wedding aniversaries, birthdays, home and work addresses.
    Do not use this tool to create tasks, simply to store information for retieval later.
    Input should be a json string with three keys: "value_name", "value_type", "value"
    value_name should be the name of a place or persons name.
    Be careful to always use double quotes for strings in the json string
    """

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            input = parse_input(text)
            print(input)

            with open(config.EMAIL_CACHE_FILE_NAME, 'ab+') as file:
                pickle.dump(input, file)
                #file.close()
     
            return "memory saved."
        except Exception as e:
            traceback.print_exc()
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("TaskBot does not support async")

class MemoryBotRetrieve(BaseTool):
    name = "MEMORY_RETRIEVE_ALL"
    description = """useful for when you need to retrieve all personal preferences, hobbies, favorite things, special dates, names, and places as a list of JSON.
    Do not use this tool to retrieve tasks but use this tool to retrieve a date or place needed to create a task.
    Examples include favorite things, wedding aniversaries, birthdays, home and work addresses.
    """
    

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)
            data = []
            if os.path.isfile(config.EMAIL_CACHE_FILE_NAME):
                with open(config.EMAIL_CACHE_FILE_NAME, 'rb') as file:
                    try:
                        while True:
                            data.append(pickle.load(file))
                    except EOFError:
                        pass
                        
                print(data)
                return data
            else:
                return []
        except Exception as e:
            traceback.print_exc()
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("TaskBot does not support async")