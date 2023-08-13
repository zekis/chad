import traceback
import config

from datetime import datetime, timedelta
from dateutil import parser
from typing import Any, Dict, Optional, Type

from common.rabbit_comms import publish_todo_card, publish_list, publish_folder_list
from common.utils import tool_description, tool_error
from common.utils import validate_response, parse_input, sanitize_subject

from O365 import Account

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool

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
        traceback.print_exc()
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
        traceback.print_exc()
        return repr(e)

def get_task_detail_by_id(folder_name, task_id):
    account = authenticate()
    print("searching for " + task_id + " in " + folder_name)
    todo = account.tasks()
    folder = todo.get_folder(folder_name = folder_name)
    try:
        
        todo_task = folder.get_task(task_id)
        if todo_task:
            print("found " + str(todo_task))
            return todo_task
        else:
            return None
        
    except Exception as e:
        traceback.print_exc()
        return repr(e)

def scheduler_get_task_due_today(folder):
    account = authenticate()
    todo =  account.tasks()
    try:
        folder = todo.get_folder(folder_name=folder)
    except:
        #Later I will call the AI to create the folder
        return "Need to create the AutoCHAD task folder"
    query = folder.new_query()
    query = query.on_attribute('status').unequal('completed')
    todo_list = folder.get_tasks(query)

    for task in todo_list:
        due_date = task.due
        #print(f"{task.subject} - Due: {due_date}")
        if due_date:
            if datetime.now().astimezone() - due_date  > timedelta(hours=8):
                return task
    return None

def scheduler_get_bots_unscheduled_task(folder):
    account = authenticate()
    todo = account.tasks()
    try:
        folder = todo.get_folder(folder_name=folder)
    except:
        #Later I will call the AI to create the folder
        return "Need to create the AutoCHAD task folder"
    query = folder.new_query()
    query = query.on_attribute('status').unequal('completed')
    todo_list = folder.get_tasks(query)

    for task in todo_list:
        due_date = task.due
        #print(f"{task.subject} - Due: {due_date}")
        if not due_date:
            return task
    return None

class MSGetTasks(BaseTool):
    parameters = []
    optional_parameters = []
    name = "GET_TASKS"
    summary = """useful for when you need to get a list of tasks in a task folder. """
    parameters.append({"name": "folder_name", "description": "If folder not specified, default will be used" })
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, folder_name: str = None, publish: str = "True", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            # print(text)
            # data = parse_input(text)
            account = authenticate()
            todo = account.tasks()
            # folder_name = data.get("folder_name")
            # folder_name = sanitize_subject(folder_name)
            if not folder_name:
                folder = todo.get_folder(folder_name="Tasks")
            else:
                folder = todo.get_folder(folder_name=folder_name)
            
            query = folder.new_query()
            query = query.on_attribute('status').unequal('completed')
            #query = todo.new_query("title").equals(task_name)
            tasks = folder.get_tasks(query)

            ai_summary = ""
            human_summary = []

            if tasks:
                for task in tasks:
                    
                    if task.due:
                        due_date = task.due.strftime("%A, %B %d, %Y at %I:%M %p")
                    else:
                        due_date = "No due date"
                    ai_summary = ai_summary + " - Subject: " + task.subject + ", Due " + due_date + "\n"
                    title = task.subject + " - " + due_date
                    print(title)
                    value = "Please use the GET_TASK_DETAIL tool using folder_name: " + folder_name + " and task_id: " + task.task_id
                    human_summary.append((title, value))
                
                if publish.lower() == "true":
                    title_message = f"Open Tasks in Folder: {folder.name}"
                    publish_list(title_message, human_summary)
                    return config.PROMPT_PUBLISH_TRUE
                else:
                    return ai_summary
                
            
            raise Exception(f"Could not find tasks in folder {folder_name}")

        except Exception as e:
            traceback.print_exc()
            return tool_error(e, self.description)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GET_TASKS does not support async")

class MSGetTaskDetail(BaseTool):
    parameters = []
    optional_parameters = []
    name = "GET_TASK_DETAIL"
    summary = """useful for when you need more information about a task. """
    parameters.append({"name": "folder_name", "description": "task folder name" })
    parameters.append({"name": "task_id", "description": "task id" })
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, folder_name: str, task_id: str, publish: str = "True", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            # print(text)
            # data = parse_input(text)
            if task_id or folder_name:
                task = get_task_detail_by_id(folder_name,task_id)
            else:
                return "Must specify folder_name and task_id"

            ai_summary = ""
            human_summary = []
            
            if task:
                if task.due:
                    due_date = task.due.strftime("%A, %B %d, %Y at %I:%M %p")
                else:
                    due_date = "No due date"
                
                ai_summary =  f"""{ai_summary} - Task: {task.subject},
                # importance: {task.importance},
                # is_starred: {task.is_starred},
                # due: {due_date},
                # completed: {task.completed}"""

                if publish.lower() == "true":
                    message = task.subject
                    publish_todo_card(message, task)
                    return config.PROMPT_PUBLISH_TRUE
                else:
                    return ai_summary
            
            raise Exception(f"Could not find task {task_id} in folder {folder_name}")
            
        except Exception as e:
            traceback.print_exc()
            return tool_error(e, self.description)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GET_TASK_DETAIL does not support async")

class MSGetTaskFolders(BaseTool):
    parameters = []
    optional_parameters = []
    name = "GET_TASK_FOLDERS"
    summary = """Useful for when you need a list of existing task folders. """
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, publish: str = "True", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:

        ai_summary = ""
        human_summary = []

        folders = get_folders()
        if folders:
            for folder in folders:
                folder_clean = folder.name.replace("Folder: ","")
                ai_summary = ai_summary + " - " + str(folder_clean) + "\n"
                title = str(folder_clean) + "\n"
                value = "Please use the GET_TASKS tool using folder name: " + str(folder_clean)
                human_summary.append((title, value))
            
            
            if publish == "True":
                title_message = f"Task Folders"
                publish_folder_list(title_message, human_summary)
                return config.PROMPT_PUBLISH_TRUE
            else:
                return ai_summary
        else:
            raise Exception(f"Could not find any task folders")
    
    async def _arun(self, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GET_TASK_FOLDERS does not support async")

class MSCreateTaskFolder(BaseTool):
    parameters = []
    optional_parameters = []
    name = "CREATE_TASK_FOLDER"
    summary = """Useful for when you need to create a new folder to contain tasks. """
    parameters.append({"name": "folder_name", "description": "folder name" })
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, folder_name: str, publish: str = "True", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            # print(text)
            # data = parse_input(text)
            # folder_name = data.get("folder_name")
            folder_name = sanitize_subject(folder_name)
            #tasks = get_tasks(data["folder_name"])
            account = authenticate()
            todo =  account.tasks()
            new_folder = todo.new_folder(folder_name)
            
            if publish.lower() == "true":
                publish(f"Task Folder {folder_name} Created")
                return config.PROMPT_PUBLISH_TRUE
            else:
                return f"Task Folder {folder_name} Created"

        except Exception as e:
            traceback.print_exc()
            return tool_error(e, self.description)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("CREATE_TASK_FOLDER does not support async")

class MSSetTaskComplete(BaseTool):
    parameters = []
    optional_parameters = []
    name = "SET_TASK_COMPLETE"
    summary = """Useful for when you need to mark a task as complete """
    parameters.append({"name": "task_id", "description": "task id" })
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, task_id: str, publish: str = "True", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            
            account = authenticate()
            todo = account.tasks()

            todo_task = todo.get_task(task_id)
            
            if todo_task:
                todo_task.mark_completed()
                todo_task.save()

                if publish.lower() == "true":
                    publish_todo_card("Task Complete", todo_task)
                    return config.PROMPT_PUBLISH_TRUE
                else:
                    return f"Task {task_id} marked complete"
            else:
                raise Exception(f"Could not find task {task_id}")
            
        except Exception as e:
            traceback.print_exc()
            return tool_error(e, self.description)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("SET_TASK_COMPLETE does not support async")

class MSCreateTask(BaseTool):
    parameters = []
    optional_parameters = []
    name = "CREATE_TASK"
    summary = """Useful for when you need to create a task. """
    parameters.append({"name": "folder_name", "description": "task folder name" })
    parameters.append({"name": "task_name", "description": "task subject" })
    optional_parameters.append({"name": "due_date", "description": "due_date should be in the format 2023-02-28 for a python datetime.date object" })
    optional_parameters.append({"name": "reminder_date", "description": "due_date should be in the format 2023-02-26 for a python datetime.date object" })
    optional_parameters.append({"name": "body", "description": "task body content" })
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, task_name: str, folder_name: str = None, due_date: str = None, reminder_date: str = None, body: str = None, publish: str = "True", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            
            account = authenticate()
            todo = account.tasks()

            #get the folder and task
            if not folder_name:
                folder_name = "Tasks"
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
                if publish.lower() == "true":
                    publish_todo_card(task_name, new_task) 
                    return config.PROMPT_PUBLISH_TRUE
                else:
                    return f"Task {task_name} created"
            else:
                raise Exception(f"Could not find folder {folder_name}")

        except Exception as e:
            traceback.print_exc()
            return tool_error(e, self.description)
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("CREATE_TASK does not support async")

class MSDeleteTask(BaseTool):
    parameters = []
    optional_parameters = []
    name = "DELETE_TASK"
    summary = """Useful for when you need to delete a task. """
    parameters.append({"name": "task_id", "description": "task id" })
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, task_id, publish: str = "True", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            
            todo_task = todo.get_task(task_id)
            
            todo_task.delete()

            if publish.lower() == "true":
                publish(f"Task Deleted")
                return config.PROMPT_PUBLISH_TRUE
            else:
                return f"Task {task_id} deleted"
        except Exception as e:
            traceback.print_exc()
            return tool_error(e, self.description)

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("DELETE_TASK does not support async")

class MSUpdateTask(BaseTool):
    parameters = []
    optional_parameters = []
    name = "UPDATE_TASK"
    summary = """Useful for when you need to update a task. """
    parameters.append({"name": "task_id", "description": "task id" })
    optional_parameters.append({"name": "task_name", "description": "task subject" })
    optional_parameters.append({"name": "due_date", "description": "due_date should be in the format 2023-02-28 for a python datetime.date object" })
    optional_parameters.append({"name": "reminder_date", "description": "due_date should be in the format 2023-02-26 for a python datetime.date object" })
    optional_parameters.append({"name": "body", "description": "task body content" })
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, task_id: str, task_name: str = None, due_date: str = None, reminder_date: str = None, body: str = None, publish: str = "True", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:

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

                if publish.lower() == "true":
                    publish_todo_card("Task Updated", existing_task)
                    return config.PROMPT_PUBLISH_TRUE
                else:
                    return f"Task {task_id} updated"
            else:
                raise Exception(f"Could not find task {task_id}")

        except Exception as e:
            traceback.print_exc()
            return tool_error(e, self.description)

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("UPDATE_TASK does not support async")

