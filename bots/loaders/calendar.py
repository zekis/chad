import traceback
import config
import datetime as dt

import pika
import shutil


from pydantic import BaseModel, Field
from datetime import datetime, date, time, timezone, timedelta
from dateutil import parser
from typing import Any, Dict, Optional, Type
from bots.langchain_assistant import generate_response

from common.rabbit_comms import publish, publish_event_card, publish_list


from O365 import Account, FileSystemTokenBackend, MSGraphProtocol

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool

from langchain.chat_models import ChatOpenAI

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

def get_event(eventID):
    account = authenticate()
    schedule = account.schedule()
    calendar = schedule.get_default_calendar()
    print(calendar.name)

    event = calendar.get_event(eventID)  # include_recurring=True will include repeated events on the result set.
    return event




class MSGetCalendarEvents(BaseTool):
    name = "GET_CALENDAR_EVENTS"
    description = """useful for when you need to retrieve meetings and appointments
    To use the tool you must provide the following parameters "start_date" and "end_date"
    Be careful to always use double quotes for strings in the json string 
    """

    return_direct= True
    def _run(self, start_date: str, end_date: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            # connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            # notify_channel = connection.channel()
            # notify_channel.queue_declare(queue='notify')
            
            ai_summary = ""
            human_summary = []

            events = search_calendar(start_date, end_date)
            if events:
                for event in events:
                    ai_summary = ai_summary + " - Event: " + event.subject + ", At " + event.start.strftime("%A, %B %d, %Y at %I:%M %p") + "\n"
                    #human_summary = human_summary + " - Event: " + event.subject + ", At " + event.start.strftime("%A, %B %d, %Y at %I:%M %p") + "\n"
                    title = event.subject + " - " + event.start.strftime("%A, %B %d, %Y at %I:%M %p")
                    value = "Please use the GET_CALENDAR_EVENT tool using ID: " + event.object_id
                    human_summary.append((title, value))
                
                title_message = f"Events Scheduled {start_date} - {end_date}"
                publish_list(title_message, human_summary)
                #notify_channel.basic_publish(exchange='',routing_key='notify',body=human_summary)
                return "Done"
            else:
                return "No events"
            
            #return ai_summary
            return generate_response(ai_summary)
        except Exception as e:
            traceback.print_exc()
            return f'To use the tool you must provide the following parameters "start_date" "end_date"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GET_CALENDAR_EVENTS does not support async")

class MSGetCalendarEvent(BaseTool):
    name = "GET_CALENDAR_EVENT"
    description = """useful for when you need to retrieve a single meeting or appointment
    To use the tool you must provide the following parameter "eventID"
    Be careful to always use double quotes for strings in the json string 
    """

    return_direct= True
    def _run(self, eventID: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            notify_channel = connection.channel()
            notify_channel.queue_declare(queue='notify')
            
            ai_summary = ""
            human_summary = []

            event = get_event(eventID)
            if event:
                ai_summary = ai_summary + " - Event: " + event.subject + ", At " + event.start.strftime("%A, %B %d, %Y at %I:%M %p") + "\n"
                title_message = f"Event Review"
                publish_event_card(title_message, event)
                #notify_channel.basic_publish(exchange='',routing_key='notify',body=human_summary)
                return "Done"
            
            
            return "No events"
            
            
        except Exception as e:
            traceback.print_exc()
            return f'To use the tool you must provide the following parameters "start_date" "end_date"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GET_CALENDAR_EVENTS does not support async")

class MSCreateCalendarEvent(BaseTool):
    name = "CREATE_CALENDAR_EVENT"
    description = """useful for when you need to create a meetings or appointment in the humans calander
    To use the tool you must provide the following parameters "subject", "start_datetime" and "end_datetime" format as %Y-%m-%d %H:%M:%S
    Optional parameters include "is_all_day", "location" and "remind_before_minutes"
    Be careful to always use double quotes for strings in the json string 
    """

    return_direct= True
    def _run(self, subject, start_datetime: str, end_datetime: str, is_all_day: str = None, location: str = None, remind_before_minutes: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            # connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            # notify_channel = connection.channel()
            # notify_channel.queue_declare(queue='notify')
            
            ai_summary = ""
            human_summary = []

            account = authenticate()
            schedule = account.schedule()
            calendar = schedule.get_default_calendar()
            new_event = calendar.new_event()

            format = "%Y-%m-%d %H:%M:%S"
            formatted_start_datetime = dt.datetime.strptime(start_datetime, format)
            formatted_end_datetime = dt.datetime.strptime(end_datetime, format)

            new_event.subject = subject
            new_event.start = formatted_start_datetime
            if is_all_day:
                new_event.is_all_day = is_all_day
            else:
                new_event.end = formatted_end_datetime
            
            
            if location:
                new_event.location = location
            
            if remind_before_minutes:
                new_event.remind_before_minutes = remind_before_minutes

            new_event.save()    
        
            ai_summary = "New Calander Event: " + new_event.subject + ", At " + new_event.start.strftime("%A, %B %d, %Y at %I:%M %p") + "\n"
            title_message = f"New Calander Event"
            publish_event_card(title_message, new_event)
            #notify_channel.basic_publish(exchange='',routing_key='notify',body=human_summary)
            return "Done"

        except Exception as e:
            traceback.print_exc()
            print(e)
            return f'To use the tool you must provide the following parameters "subject" "start_date" "end_date"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("CREATE_CALENDAR_EVENT does not support async")