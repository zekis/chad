import config
from dotenv import find_dotenv, load_dotenv
#from flask import request

import os
import datetime
import re
from O365 import Account, FileSystemTokenBackend, MSGraphProtocol

### With your own identity (auth_flow_type=='credentials') ####

def get_all_todo_tasks():
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

    # if not account.is_authenticated:
    #     # Authenticate using OAuth2
    #     account.authenticate(scopes=SCOPES)
    
    if account.authenticate():
        print('Authenticated!')
    
    todo =  account.tasks()
    folder = todo.get_default_folder()
    todo_list = folder.get_tasks()

    #current_user = account.get_current_user()

    # for task in todo_list:
    #     account_folder = sanitize_subject(str(current_user))
    #     task_title = sanitize_subject(task.subject)
    #     file_name = f"{task_title}.html"

    #     account_output_folder = os.path.join(output_folder, account_folder)
    #     task_output_folder = os.path.join(account_output_folder, 'todo_tasks')

    #     # Create account and task folders if they don't exist
    #     os.makedirs(task_output_folder, exist_ok=True)

    #     output_file = os.path.join(task_output_folder, file_name)
    #     with open(output_file, "w", encoding="utf-8") as f:
    #         f.write(format_todo_task_as_html(task))

    #     index_html += f"\n<li><a href='{os.path.join(account_folder, 'todo_tasks', file_name)}'>{task_title}</a></li>"

    # index_html += "</ol>"
    # with open(os.path.join(output_folder, "index.html"), "w", encoding="utf-8") as index_file:
    #     index_file.write(index_html)

    return todo_list

def format_todo_task_as_html(task):
    html = f"<h1>{task.subject}</h1>"
    if task.due :
        html += f"<p>Due: {task.due.strftime('%Y-%m-%d %H:%M:%S')}</p>"
    if task.completed :
        html += f"<p>completed : {task.completed }</p>"
    return html




def sanitize_subject(subject, max_length=50):
    # Replace slashes with hyphens
    subject = subject.replace("/", "-").replace("\\", "-")
    
    # Remove or replace other special characters
    subject = re.sub(r"[^a-zA-Z0-9\-_]+", "_", subject)
    
    # Truncate the subject to the specified length
    subject = subject[:max_length]
    
    return subject