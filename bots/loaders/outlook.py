import traceback
import config
from dotenv import find_dotenv, load_dotenv
#from flask import request
import json
import os
import re
import pika

from pydantic import BaseModel, Field
from datetime import datetime, date, time, timezone, timedelta
from dateutil import parser
from typing import Any, Dict, Optional, Type

from bots.utils import validate_response, parse_input
from O365 import Account, FileSystemTokenBackend, MSGraphProtocol

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from langchain.tools import StructuredTool


### With your own identity (auth_flow_type=='credentials') ####
def authenticate():
    credentials = (config.APP_ID, config.APP_PASSWORD)
    account = Account(credentials,auth_flow_type='credentials',tenant_id=config.tenant_id, main_resource=config.OFFICE_USER)
    account.authenticate()
    return account

def get_folders():
    account = authenticate()
    todo =  account.tasks()
    folders = todo.list_folders()
    return folders

def get_tasks(folder_name):
    account = authenticate()
    todo =  account.tasks()
    try:
        folder = todo.get_folder(folder_name=folder_name)
    except:
        return "You must specify a valid folder name, use get_task_folders to get the list of folders"
    todo_list = folder.get_tasks()
    return todo_list

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
    if task_list:
        task_str = "### Folder: " + str(folder)
        for task in task_list:
            #print(str(folder) + " " + str(task))
            if not task.is_completed:
                task_str = task_str + "\n - " + str(task.subject) + " Due: " + str(task.due)
        return task_str
    else:
        return "You must specify a valid folder name, use get_task_folders to get the list of folders"

def folders_to_string(folders_list):
#list current tasks
    folders_str = "### Folders:"
    for folder in folders_list:
        print(folder)
        folders_str = folders_str + "\n - " + str(folder)
    return folders_str

async def scheduler_check_tasks(folder, channel):
    account = authenticate()
    todo =  account.tasks()
    try:
        folder = todo.get_folder(folder_name=folder)
    except:
        #Later I will call the AI to create the folder
        channel.basic_publish(exchange='',routing_key='message',body="Need to create the AutoCHAD task folder")
        return "Need to create the AutoCHAD task folder"
    
    todo_list = folder.get_tasks()

    for task in todo_list:
        due_date = task.due
        if not task.is_completed:
            #print(f"{task.subject} - Due: {due_date}")
            if due_date:
                if datetime.now().astimezone() - due_date  > timedelta(hours=8):
                    return task
    return None

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
            data = parse_input(text)
            folder_name = data["folder_name"]
            tasks = get_tasks(folder_name)
            #print(f"folder_name: {data["folder_name"]}") 
            return validate_response(tasks_to_string(tasks, folder_name))
        except Exception as e:
            return f"You must specify a valid folder name, use get_task_folders to get the list of folders ({e})"
    
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
            data = parse_input(text)
            #print(f"folder_name: {data["folder_name"]}, task_name: {data["task_name"]}") 
            return get_task_detail(data["folder_name"], data["task_name"])
        except Exception as e:
            return "Could not update task. You must specify a valid task name and folder name, use get_task_folders and get_tasks to get the list of folders and tasks"
    
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
        return folders_to_string(get_folders())
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSGetTaskFolders does not support async")

class MSCreateTaskFolder(BaseTool):
    name = "create_task_folder"
    description = """useful for when you need to create a new folder to contain tasks.
    To use the tool you must provide the following parameter ["folder_name"]
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)
            data = parse_input(text)
            folder_name = data["folder_name"]
            tasks = get_tasks(data["folder_name"])
            account = authenticate()
            todo =  account.tasks()
            new_folder = todo.new_folder(folder_name)
            
            #print(f"folder_name: {data["folder_name"]}") 
            return "folder created"
        except Exception as e:
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSGetTasks does not support async")

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
            data = parse_input(text)
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
    To use the tool you must provide the following parameters ["folder_name", "task_name", "due_date", "reminder_date"].
    If not sure what folder to create the task in, use the Tasks folder.
    Input should be a json string with at least two keys: "folder_name" and "task_name"
    due_date should be in the format "2023-02-28" for a python datetime.date object
    reminder_date should be in the format "2023-02-28" for a python datetime.date object
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema

    def _run(self, text, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            print(text)
            data = parse_input(text)
            folder_name = data.get("folder_name")
            task_name = data.get("task_name")
            due_date = data.get("due_date")
            reminder_date = data.get("reminder_date")
            body = data.get("body")
            
            account = authenticate()
            todo = account.tasks()

            #get the folder and task
            folder = todo.get_folder(folder_name=folder_name)
            if folder:
                new_task = folder.new_task(task_name)
                new_task.body = "Created by AutoCHAD"
                if due_date:
                    #date_format = '%Y-%m-%d'
                    new_task.due = parser.parse(due_date)
                if reminder_date:
                    #date_format = '%Y-%m-%d'
                    new_task.reminder = parser.parse(reminder_date)
                new_task.save()
                return get_task_detail(folder_name, task_name)
            else:
                return "Could not create task. You must specify a valid folder name, use get_task_folders to get the list of folders"

        except Exception as e:
            traceback.print_exc()
            #most likely error
            return "Could not create task. You must specify a valid folder name, use get_task_folders to get the list of folders"
    
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
            data = parse_input(text)
            folder_name = data["folder_name"]
            task_name = data["task_name"]

            account = authenticate()
            todo = account.tasks()

            #get the folder and task
            folder = todo.get_folder(folder_name=folder_name)
            query = todo.new_query("title").equals(task_name)
            todo_task = folder.get_task(query)
            
            todo_task.delete()

            return get_task_detail(folder_name, task_name)
        except Exception as e:
            return "Could not update task. You must specify a valid task name and folder name, use get_task_folders and get_tasks to get the list of folders and tasks"
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSDeleteTask does not support async")

class MSUpdateTask(BaseTool):
    name = "update_task"
    description = """
    Useful for when you need to update a task.
    To use the tool you must provide the following parameters ["folder_name", "task_name", "due_date", "reminder_date", "body"].
    If not sure what folder the is in, use the get_task_folders tool.
    Input should be a json string with at least two keys: "folder_name" and "task_name"
    due_date should be in the format "2023-02-28" for a python datetime.date object
    reminder_date should be in the format "2023-02-28" for a python datetime.date object
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema

    def _run(self, text, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            print(text)
            data = parse_input(text)
            # folder_name = data["folder_name"]
            # task_name = data["task_name"]

            folder_name = data.get("folder_name")
            task_name = data.get("task_name")
            due_date = data.get("due_date")
            reminder_date = data.get("reminder_date")
            body = data.get("body")

            account = authenticate()
            todo = account.tasks()

            #get the folder and task
            folder = todo.get_folder(folder_name=folder_name)
            query = todo.new_query("title").equals(task_name)
            existing_task = folder.get_task(query)

            if folder:
                existing_task = folder.get_task(task_name)
                if body:
                    existing_task.body = body
                if due_date:
                    #date_format = '%Y-%m-%d'
                    existing_task.due = parser.parse(due_date)
                if reminder_date:
                    #date_format = '%Y-%m-%d'
                    existing_task.reminder = parser.parse(due_date)
                existing_task.save()
                return get_task_detail(folder_name, task_name)
            else:
                return "Could not update task. You must specify a valid task name and folder name, use get_task_folders and get_tasks to get the list of folders and tasks"

        except Exception as e:
            traceback.print_exc()
            #most likely error
            return "Could not update task. You must specify a valid task name and folder name, use get_task_folders and get_tasks to get the list of folders and tasks"
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSDeleteTask does not support async")