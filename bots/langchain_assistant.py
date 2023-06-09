import traceback
import config
from datetime import date, timedelta
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from O365 import Account, FileSystemTokenBackend, MSGraphProtocol


### With your own identity (auth_flow_type=='credentials') ####
def authenticate():
    credentials = (config.APP_ID, config.APP_PASSWORD)
    account = Account(credentials,auth_flow_type='credentials',tenant_id=config.TENANT_ID, main_resource=config.OFFICE_USER)
    account.authenticate()
    return account

def search_calendar(start_date, end_date):
    account = authenticate()
    schedule = account.schedule()
    calendar = schedule.get_default_calendar()
    print(calendar.name)

    #query = calendar.new_query().search(search_query)
    q = calendar.new_query('start').greater_equal(start_date)
    q.chain('and').on_attribute('end').less_equal(end_date)

    events = calendar.get_events(query=q, include_recurring=True)  # include_recurring=True will include repeated events on the result set.

    if events:
        return events
    return None

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

def generate_response(text):
    return text
# def generate_response(text):
#     chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
#     my_tasks = get_tasks(config.Todo_BotsTaskFolder)

#     today = date.today() - timedelta(days=1)
#     end_of_week = date.today() + timedelta(days=7)
#     my_appointments = search_calendar(start_date=today.strftime('%Y-%m-%d'), end_date=end_of_week.strftime('%Y-%m-%d'))

    
#     query = f"""My Calendar: {my_appointments} My tasks: {my_tasks} given this information, please recommend if I should create a todo task, add an appointment to my calander, respond with an email or ignore: {text}"""
#     print(f"Function Name: generate_response | Query: {query}, Text: {text}")
#     return chat([HumanMessage(content=query)]).content