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
from bots.langchain_assistant import generate_response
from common.rabbit_comms import publish_todo_card, publish_list
#from common.rabbit_comms import publish, publish_card, publish_list
#from common.utils import encode_message, decode_message
from common.utils import validate_response, parse_input, sanitize_subject
#from common.utils import generate_response, generate_whatif_response, generate_plan_response
from O365 import Account, FileSystemTokenBackend, MSGraphProtocol

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from langchain.tools import StructuredTool


### With your own identity (auth_flow_type=='credentials') ####
def authenticate():
    credentials = (config.APP_ID, config.APP_PASSWORD)
    account = Account(credentials,auth_flow_type='credentials',tenant_id=config.TENANT_ID, main_resource=config.OFFICE_USER)
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
    todo = account.tasks()
    try:
        folder = todo.get_folder(folder_name=folder_name)
        query = todo.new_query("title").equals(task_name)
        #query = {"subject": task_name}
        todo_task = folder.get_task(query)
        if todo_task:
            print("found " + str(todo_task))
            return todo_task
        else:
            return None
        
    except Exception as e:
        return repr(e)

def get_task_detail_by_id(task_id):
    account = authenticate()
    print("searching for " + task_id)
    todo =  account.tasks()
    try:
        
        todo_task = todo.get_task(task_id)
        if todo_task:
            print("found " + str(todo_task))
            return todo_task
        else:
            return None
        
    except Exception as e:
        return repr(e)

# def build_task_sumary(task):
#     body = f"""
#         subject = {task.subject}
#         created = {task.created}
#         modified = {task.modified}
#         importance = {task.importance}
#         is_starred = {task.is_starred}
#         due = {task.due}
#         completed = {task.completed}
#         description = {task.body}
#     """
#     return body

# def tasks_to_string(task_list, folder):
# #list current tasks
#     if task_list:
#         task_str = "### Folder: " + str(folder)
#         for task in task_list:
#             #print(str(folder) + " " + str(task))
#             if not task.is_completed:
#                 task_str = task_str + "\n - " + str(task.subject) + " Due: " + str(task.due)
#         return task_str
#     else:
#         return "You must specify a valid folder name, use get_task_folders to get the list of folders"

# def folders_to_string(folders_list):
# #list current tasks
#     folders_str = "### Folders:"
#     for folder in folders_list:
#         print(folder)
#         folders_str = folders_str + "\n - " + str(folder)
#     return folders_str

def scheduler_check_tasks(folder):
    account = authenticate()
    todo =  account.tasks()
    try:
        folder = todo.get_folder(folder_name=folder)
    except:
        #Later I will call the AI to create the folder
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
    name = "GET_TASKS"
    description = """useful for when you need to get a list of tasks in a task folder.
    To use the tool you must provide the following parameter "task_name" and optional "folder_name" 
    If folder not specified, default will be used.
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema
    return_direct= True
    def _run(self, task_name: str, folder_name: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            # print(text)
            # data = parse_input(text)
            # folder_name = data.get("folder_name")
            # folder_name = sanitize_subject(folder_name)
            if not folder_name:
                folder = todo.get_default_folder()
            else:
                folder = todo.get_folder(folder_name)
            
            query = todo.new_query("title").equals(task_name)
            tasks = folder.get_tasks(folder_name)

            ai_summary = ""
            human_summary = []

            if tasks:
                for task in tasks:
                    if task.completed == False:
                        ai_summary = ai_summary + " - Subject: " + task.subject + ", Due " + task.due.strftime("%A, %B %d, %Y at %I:%M %p") + "\n"
                        title = task.subject + " - " + task.due.strftime("%A, %B %d, %Y at %I:%M %p")
                        value = "Please use the GET_TASK_DETAIL tool using ID: " + task.task_id
                        human_summary.append((title, value))
                
                title_message = f"Current Open Tasks"
                publish_list(title_message, human_summary)
                #notify_channel.basic_publish(exchange='',routing_key='notify',body=human_summary)
            else:
                return "No events"
            
            #return ai_summary
            return generate_response(ai_summary)
        except Exception as e:
            traceback.print_exc()
            return f"You must specify a valid folder name, use get_task_folders to get the list of folders ({e})"
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSGetTasks does not support async")

class MSGetTaskDetail(BaseTool):
    name = "GET_TASK_DETAIL"
    description = """useful for when you need more information about a task.
    To use the tool you must provide the following parameters "task_id".
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[BaseModel] = MSTodoToolSchema
    return_direct= True
    def _run(self, task_id: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            # print(text)
            # data = parse_input(text)
            task = get_task_detail_by_id(task_id)

            ai_summary = ""
            human_summary = []
            
            if task:
                ai_summary =  f"""{ai_summary} - Task: {task.subject},
                Created: {task.start.strftime("%A, %B %d, %Y at %I:%M %p")},
                Modified: {task.modified.strftime("%A, %B %d, %Y at %I:%M %p")},
                Importance: {task.importance},
                Is starred: {task.is_starred},
                Due: {task.due.strftime("%A, %B %d, %Y at %I:%M %p")},
                Completed: {task.completed},
                Description: {task.description},
                """
                message = task.subject + " - " + task.due.strftime("%A, %B %d, %Y at %I:%M %p") + "\n"
                publish_todo_card(message, task)
                return ai_summary

            #print(f"folder_name: {data["folder_name"]}, task_name: {data["task_name"]}") 
            return "No task found"
            
        except Exception as e:
            return "Could not update task. You must specify a valid task name and folder name, use get_task_folders and get_tasks to get the list of folders and tasks"
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSGetTaskDetail does not support async")

class MSGetTaskFolders(BaseTool):
    name = "GET_TASK_FOLDERS"
    description = """useful for when you need a list of existing task folders.
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema
    return_direct= True
    def _run(self, query, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        print(f"query: {query}")

        ai_summary = ""
        human_summary = []

        folders = get_folders()
        if folders:
            for folder in folders:
                ai_summary = ai_summary + " - " + str(folder) + "\n"
                title = " - " + str(folder) + "\n"
                value = "Please use the GET_TASKS tool using folder name: " + str(folder)
                human_summary.append((title, value))
            
            title_message = f"Task Folders"
            publish_list(title_message, human_summary)
            return ai_summary
        else:
            return "No Task Folders"
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSGetTaskFolders does not support async")

class MSCreateTaskFolder(BaseTool):
    name = "CREATE_TASK_FOLDER"
    description = """useful for when you need to create a new folder to contain tasks.
    To use the tool you must provide the following parameter "folder_name"
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema
    return_direct= True
    def _run(self, folder_name: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            # print(text)
            # data = parse_input(text)
            # folder_name = data.get("folder_name")
            folder_name = sanitize_subject(folder_name)
            #tasks = get_tasks(data["folder_name"])
            account = authenticate()
            todo =  account.tasks()
            new_folder = todo.new_folder(folder_name)
            
            #print(f"folder_name: {data["folder_name"]}") 
            return "Task Folder Created"
        except Exception as e:
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSGetTasks does not support async")

class MSSetTaskComplete(BaseTool):
    name = "SET_TASK_COMPLETE"
    description = """
    Useful for when you need to mark a task as complete
    To use the tool you must provide the following parameters "task_id.
    Input should be a json string with two keys: "folder_name" and "task_name"
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema
    return_direct= True
    def _run(self, task_id: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            # print(text)
            # data = parse_input(text)
            # folder_name = data.get("folder_name")
            # folder_name = sanitize_subject(folder_name)
            # task_name = data.get("task_name")
            # task_name = sanitize_subject(task_name)
            
            account = authenticate()
            todo = account.tasks()

            # #get the folder and task
            # folder = todo.get_folder(folder_name=folder_name)
            # query = todo.new_query("title").equals(task_name)
            todo_task = todo.get_task(task_id)
            
            if todo_task:
                todo_task.mark_completed()
                todo_task.save()
                publish_todo_card("Task Complete", todo_task)
                return "Task Marked as Complete"
            else:
                return "could not find task"
            
        except Exception as e:
            return repr(e)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSSetTaskComplete does not support async")

class MSCreateTask(BaseTool):
    name = "CREATE_TASK"
    description = """
    Useful for when you need to create a task.
    To use the tool you must provide the following parameters "folder_name", "task_name", "due_date", "reminder_date", "body".
    If not sure what folder to create the task in, use the default folder name 'Tasks' or use the GET_TASK_FOLDERS tool.
    due_date should be in the format "2023-02-28" for a python datetime.date object
    reminder_date should be in the format "2023-02-28" for a python datetime.date object
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema
    return_direct= True
    def _run(self, folder_name: str, task_name: str, due_date: str = None, reminder_date: str = None, body: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            # print(text)
            # data = parse_input(text)
            # folder_name = data.get("folder_name")
            # folder_name = sanitize_subject(folder_name)
            # task_name = data.get("task_name")
            # task_name = sanitize_subject(task_name)
            # due_date = data.get("due_date")
            # reminder_date = data.get("reminder_date")
            # body = data.get("body")
            
            account = authenticate()
            todo = account.tasks()

            #get the folder and task
            folder = todo.get_folder(folder_name=folder_name)

            if folder:
                new_task = folder.new_task(task_name)
                #expression_if_true if condition else expression_if_false
                new_task.body = body if body else "Created by AutoCHAD"
                if due_date:
                    new_task.due_date = due_date
                if reminder_date:
                    new_task.reminder_date = reminder_date
                new_task.save()

                #ai_summary = get_task_detail(folder_name, task_name)
                
                publish_todo_card(task_name, new_task) 
                return new_task.task_id
            else:
                return "Could not create task. You must specify a valid folder name, use get_task_folders to get the list of folders"

        except Exception as e:
            traceback.print_exc()
            #most likely error
            return f"Could not create task. {e}"
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSCreateTask does not support async")

class MSDeleteTask(BaseTool):
    name = "DELETE_TASK"
    description = """
    Useful for when you need to delete a task.
    To use the tool you must provide the following parameters "task_id"
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema
    return_direct= True
    def _run(self, task_id, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            # print(text)
            # data = parse_input(text)
            # folder_name = data.get("folder_name")
            # folder_name = sanitize_subject(folder_name)
            # task_name = data.get("task_name")
            # task_name = sanitize_subject(task_name)

            # account = authenticate()
            # todo = account.tasks()

            # #get the folder and task
            # folder = todo.get_folder(folder_name=folder_name)
            # query = todo.new_query("title").equals(task_name)
            todo_task = todo.get_task(task_id)
            
            todo_task.delete()
            publish_todo_card("Task Deleted", todo_task)

            return "Task Deleted"
        except Exception as e:
            return "Could not delete task. You must specify a valid task ID, use get_task_folders and get_tasks to get the list of folders and tasks"
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSDeleteTask does not support async")

class MSUpdateTask(BaseTool):
    name = "UPDATE_TASK"
    description = """
    Useful for when you need to update a task.
    To use the tool you must provide the following parameters "task_id", "task_name", "due_date", "reminder_date", "body".
    If not sure what folder the is in, use the get_task_folders tool.
    due_date should be in the format "2023-02-28" for a python datetime.date object
    reminder_date should be in the format "2023-02-28" for a python datetime.date object
    Be careful to always use double quotes for strings in the json string
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema
    return_direct= True
    def _run(self, task_id: str, task_name: str = None, due_date: str = None, reminder_date: str = None, body: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            # print(text)
            # data = parse_input(text)
            # # folder_name = data["folder_name"]
            # # task_name = data["task_name"]

            # folder_name = data.get("folder_name")
            # folder_name = sanitize_subject(folder_name)

            # task_name = data.get("task_name")
            # task_name = sanitize_subject(task_name)
            
            # due_date = data.get("due_date")
            # reminder_date = data.get("reminder_date")
            # body = data.get("body")

            account = authenticate()
            todo = account.tasks()

            #get the folder and task
            # folder = todo.get_folder(folder_name=folder_name)
            # query = todo.new_query("title").equals(task_name)
            existing_task = todo.get_task(task_id)

            if existing_task:
                existing_task.subject = task_name
                if body:
                    existing_task.body = body
                if due_date:
                    #date_format = '%Y-%m-%d'
                    existing_task.due_date = parser.parse(due_date)
                if reminder_date:
                    #date_format = '%Y-%m-%d'
                    existing_task.reminder_date = parser.parse(due_date)
                existing_task.save()
                publish_todo_card("Task Updated", existing_task)
                return "Task Updated"
            else:
                return "Could not update task. You must specify a valid task id and folder name, use get_task_folders and get_tasks to get the list of folders and tasks"

        except Exception as e:
            traceback.print_exc()
            #most likely error
            return "Could not update task. You must specify a valid task name and folder name, use get_task_folders and get_tasks to get the list of folders and tasks"
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSDeleteTask does not support async")

