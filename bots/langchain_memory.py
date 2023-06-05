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
import urllib

from pydantic import BaseModel, Field
from datetime import datetime, date, time, timezone, timedelta
from typing import Any, Dict, Optional, Type

#from bots.loaders.todo import MSGetTasks, MSGetTaskFolders, MSGetTaskDetail, MSSetTaskComplete, MSCreateTask, MSDeleteTask, MSCreateTaskFolder
from common.utils import validate_response, parse_input
from common.utils import generate_response, generate_whatif_response, generate_plan_response
from bots.rabbit_handler import RabbitHandler

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from langchain.tools import StructuredTool

#from langchain import OpenAI
from langchain.chat_models import ChatOpenAI

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
    description = """useful for when you need to store personal preferences, favorite things, names, and places.
    Examples include favorite foods, music, wedding aniversaries, birthdays, home and work addresses.
    DO NOT USER this tool to create tasks.
    Input should be a json string with three keys: "value_name", "value_type", "value"
    value_name should be the name of a place or persons name.
    Be careful to always use double quotes for strings in the json string
    """

    def _run(self, value_name: str = None, value_type: str = None, value: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        timestamp = datetime.now()
        try:
            if value_type.lower() == "task":
                return "Do not store tasks in memory, use the ASSIGN tool instead"
            if value:
                return add_memory(value_name, value_type, value)
        except Exception as e:
            traceback.print_exc()
            return """ Input should be a json string with three keys: "value_name", "value_type", "value"."""
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("TaskBot does not support async")

class MemoryBotUpdate(BaseTool):
    name = "MEMORY_UPDATE"
    description = """useful for when you need to update a memory, personal preferences, favorite things, names, and places.
    Examples include favorite foods, music, wedding aniversaries, birthdays, home and work addresses.
    Input should be a json string with three keys: "value_name", "value_type", "value"
    value_name should be the name of a place or persons name.
    Be careful to always use double quotes for strings in the json string
    """

    def _run(self, value_name: str = None, value_type: str = None, value: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        timestamp = datetime.now()
        try:
            if value_type.lower() == "task":
                return "Do not store tasks in memory, use the ASSIGN tool instead"
            if value:
                return update_memory(value_name, value_type, value)
        except Exception as e:
            traceback.print_exc()
            return """ Input should be a json string with three keys: "value_name", "value_type", "value"."""
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("TaskBot does not support async")

class MemoryBotDelete(BaseTool):
    name = "MEMORY_DELETE"
    description = """useful for when you need to delete a memory, favorite things, names, and places.
    Input should be a json string with 1 key: "value_name"
    Be careful to always use double quotes for strings in the json string
    """

    def _run(self, value_name: str = None, value_type: str = None, value: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        timestamp = datetime.now()
        try:
            return delete_memory(value_name)
        except Exception as e:
            traceback.print_exc()
            return """ Input should be a json string with three keys: "value_name", "value_type", "value"."""
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("TaskBot does not support async")

        

class MemoryBotRetrieveAll(BaseTool):
    name = "MEMORY_RETRIEVE_ALL"
    description = """useful for when you need to retrieve all personal preferences, hobbies, favorite things, special dates, names, and places as a list.
    Do not use this tool to retrieve tasks but use this tool to retrieve a date or place needed to create a task.
    Examples include favorite things, wedding aniversaries, birthdays, home and work addresses.
    Be careful to always use double quotes for strings in the json string
    """
    

    def _run(self, query: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            #print(text)
            return load_data()
        except Exception as e:
            traceback.print_exc()
            return "No memories stored."
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("TaskBot does not support async")

class MemoryBotSearch(BaseTool):
    name = "MEMORY_SEARCH"
    description = """useful for when you need to retrieve a memory of personal preferences, hobbies, favorite things, special dates, names, and places as a list.
    Do not use this tool to retrieve tasks but use this tool to retrieve a date or place.
    Input should be a json string with 1 key: "value_name".
    Examples include favorite things, wedding aniversaries, birthdays, home and work addresses.
    Be careful to always use double quotes for strings in the json string
    """
    

    def _run(self, value_name: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            return search_memory(value_name)
        except Exception as e:
            traceback.print_exc()
            return """Input should be a json string with 1 key: "value_name"."""
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("TaskBot does not support async")

def add_memory(value_name, value_type, value):
    data = load_data()
    add_value(data, value_name, value_type, value)
    return search_memory(value_name)

def search_memory(value_name):
    data = load_data()
    return search_value(data, value_name)
    

def update_memory(value_name, value_type, value):
    data = load_data()
    update_value(data, value_name, value_type, value)

def delete_memory(value_name):
    data = load_data()
    delete_value(data, value_name)

# def format_memories(memories):
#     if memories:
#         memories_str = "### Memories\n"
#         for mem in memories:
#             #print(str(folder) + " " + str(task))
#             #print(mem)
#             formated_memory = format_memory(mem)
#             memories_str = f"{memories_str} {formated_memory}"
           
#             # input = '{"value_name": "' + value_name + '", "value_type": "' + value_type + '", "value": "' + value + '"}'
#         return memories_str
#     return "No memories found."

# def format_memory(memory):
#     try:
#         value_time = memory.get("timestamp")
#         value_name = memory.get("value_name")
#         value_type = memory.get("value_type")
#         value = memory.get("value")

#         memory_str = ""
#         memory_str = f" - {value_time}: {value_name} = {value_type}({value})\n"
#         print(f"{memory} -> {memory_str}")
#         return memory_str
#     except Exception as e:
#         traceback.print_exc()
#         return " - Bad Memory"


def save_data(data, filename='data.pickle'):
    with open(filename, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

def load_data(filename='data.pickle'):
    if os.path.exists(filename):
        with open(filename, 'rb') as handle:
            return pickle.load(handle)
    else:
        return {}  # return an empty dictionary if no data file exists

def add_value(data, value_name, value_type, value, filename='data.pickle'):
    data[value_name] = {'value_name': value_name, 'value_type': value_type, 'value': value}
    save_data(data, filename)

def search_value(data, value_name):
    return data.get(value_name, None)

def update_value(data, value_name, value_type=None, value=None, filename='data.pickle'):
    if value_name in data:
        if value_type:
            data[value_name]['value_type'] = value_type
        if value:
            data[value_name]['value'] = value
        save_data(data, filename)
    else:
        print(f"No value named {value_name} found in the data.")

def delete_value(data, value_name, filename='data.pickle'):
    if value_name in data:
        del data[value_name]
        save_data(data, filename)
    else:
        print(f"No value named {value_name} found in the data.")