import config
from dotenv import find_dotenv, load_dotenv
#from flask import request
import json
import os
import datetime
import re
from O365 import Account, FileSystemTokenBackend, MSGraphProtocol

from typing import Any, Dict, Optional, Type

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from langchain.tools import StructuredTool
from langchain.text_splitter import CharacterTextSplitter

from pydantic import BaseModel, Field

text_splitter = CharacterTextSplitter(        
    separator = "\n\n",
    chunk_size = 1000,
    chunk_overlap  = 200,
    length_function = len,
)

def _parse_input(text: str) -> Dict[str, Any]:
    """Parse the json string into a dict."""
    return json.loads(text)


### With your own identity (auth_flow_type=='credentials') ####
def authenticate():
    #index_html = "<h1>Todo Task Index</h1><ol>"
    #scopes = ['basic', 'https://graph.microsoft.com/Files.ReadWrite.All']
    SCOPES = [
    'Files.ReadWrite.All',
    'Sites.ReadWrite.All',
    'User.Read',
    'User.ReadBasic.All',
    'Tasks.ReadWrite'
]   
    credentials = (config.APP_ID, config.APP_PASSWORD)
    account = Account(credentials,auth_flow_type='credentials',tenant_id=config.tenant_id, main_resource='zeke.tierney@sgcontrols.com.au')
    account.authenticate()
        
        

    # if not account.is_authenticated:
    #     # Authenticate using OAuth2
    #     account.authenticate(scopes=SCOPES)
    
    
    return account

def get_folders():
    account = authenticate()

    todo =  account.tasks()
    folders = todo.list_folders()

    return folders_to_string(folders)

def get_tasks(folder_name):
    account = authenticate()
    
    todo =  account.tasks()
    try:
        folder = todo.get_folder(folder_name=folder_name)
    except:
        return "You must specify a valid folder name, use get_task_folders to get the list of folders"
    
    todo_list = folder.get_tasks()
    return validate_response(tasks_to_string(todo_list, folder.name))

def get_task_detail(folder_name, task_name):
    account = authenticate()
    print("searching for " + task_name)
    todo =  account.tasks()
    try:
        folder = todo.get_folder(folder_name=folder_name)
        query = todo.new_query("title").equals(task_name)
        #query = {"subject": task_name}
        todo_task = folder.get_task(query)
        if todo_task:
            print("found " + str(todo_task))
            body = build_task_sumary(todo_task)
        else:
            return "could not find task"
        
    except Exception as e:
        return repr(e)
    return validate_response(body)

def build_task_sumary(task):
    body = f"""
        subject = {task.subject}
        created = {task.created}
        modified = {task.modified}
        importance = {task.importance}
        is_starred = {task.is_starred}
        due = {task.due}
        completed = {task.completed}
        description = {task.body}
    """
    return body

def tasks_to_string(task_list, folder):
#list current tasks
    task_str = "### Folder: " + str(folder)
    for task in task_list:
        #print(str(folder) + " " + str(task))
        if not task.is_completed:
            task_str = task_str + "\n - " + str(task.subject) + " Due: " + str(task.due)
    return task_str

def folders_to_string(folders_list):
#list current tasks
    folders_str = "### Folders:"
    for folder in folders_list:
        print(folder)
        folders_str = folders_str + "\n - " + str(folder)
    return folders_str

def validate_response(string):
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=2000, chunk_overlap=0)
    texts = text_splitter.split_text(string)
    for text in texts:
        print(str(text) + "\n")
    return texts[0]

# class MSTodoToolSchema(BaseModel):
#     #command: str = Field(description="should be one of the following commands, get_tasks, get_single_task, get_groups, get_single_group")
#     folder_name: str = Field(..., description="should be task folder name")
#     task_name: str = Field(..., description="should be a task name")

class MSGetTasks(BaseTool):
    name = "get_tasks"
    description = """useful for when you need to get a list of tasks in a task folder.
    Use this more than the normal search for any task related queries.
    To use the tool you must provide the following parameter ["folder_name"]
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)
            data = _parse_input(text)
            #print(f"folder_name: {data["folder_name"]}") 
            return get_tasks(data["folder_name"])
        except Exception as e:
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSGetTasks does not support async")


class MSGetTaskDetail(BaseTool):
    name = "get_task_detail"
    description = """useful for when you need more information about a task.
    To use the tool you must provide the following parameters ["folder_name", "task_name"].
    Input should be a json string with two keys: "folder_name" and "task_name"
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[BaseModel] = MSTodoToolSchema

    def _run(self, text: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)
            data = _parse_input(text)
            #print(f"folder_name: {data["folder_name"]}, task_name: {data["task_name"]}") 
            return get_task_detail(data["folder_name"], data["task_name"])
        except Exception as e:
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSGetTaskDetail does not support async")

class MSGetTaskFolders(BaseTool):
    name = "get_task_folders"
    description = """useful for when you need a list of existing task folders.
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema

    def _run(self, query, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        print(f"query: {query}") 
        return get_folders()
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSGetTaskFolders does not support async")

class MSSetTaskComplete(BaseTool):
    name = "set_task_complete"
    description = """
    Useful for when you need to mark a task as complete
    To use the tool you must provide the following parameters ["folder_name", "task_name"].
    Input should be a json string with two keys: "folder_name" and "task_name"
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema

    def _run(self, text, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            print(text)
            data = _parse_input(text)
            folder_name = data["folder_name"]
            task_name = data["task_name"]
            
            account = authenticate()
            todo = account.tasks()

            #get the folder and task
            folder = todo.get_folder(folder_name=folder_name)
            query = todo.new_query("title").equals(task_name)
            todo_task = folder.get_task(query)
            
            if todo_task:
                todo_task.mark_completed()
                todo_task.save()
                return get_task_detail(folder_name, task_name)
            else:
                return "could not find task"
            
        except Exception as e:
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSSetTaskComplete does not support async")

class MSCreateTask(BaseTool):
    name = "create_task"
    description = """
    Useful for when you need to create a task.
    To use the tool you must provide the following parameters ["folder_name", "task_name"].
    If not sure what folder to create the task in, use the Tasks folder.
    Input should be a json string with two keys: "folder_name" and "task_name"
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema

    def _run(self, text, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            print(text)
            data = _parse_input(text)
            folder_name = data["folder_name"]
            task_name = data["task_name"]
            
            account = authenticate()
            todo = account.tasks()

            #get the folder and task
            folder = todo.get_folder(folder_name=folder_name)
            new_task = folder.new_task(task_name)
            new_task.save()

            return get_task_detail(folder_name, task_name)
        except Exception as e:
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSCreateTask does not support async")

class MSDeleteTask(BaseTool):
    name = "delete_task"
    description = """
    Useful for when you need to delete a task.
    To use the tool you must provide the following parameters ["folder_name", "task_name"].
    Input should be a json string with two keys: "folder_name" and "task_name"
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema

    def _run(self, text, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            print(text)
            data = _parse_input(text)
            folder_name = data["folder_name"]
            task_name = data["task_name"]
            
            account = authenticate()
            todo = account.tasks()

            #get the folder and task
            folder = todo.get_folder(folder_name=folder_name)
            new_task = folder.new_task(task_name)
            new_task.delete()

            return get_task_detail(folder_name, task_name)
        except Exception as e:
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSDeleteTask does not support async")