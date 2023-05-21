import traceback
import config
from dotenv import find_dotenv, load_dotenv
#from flask import request
import json
import os
import re
import pika
import shutil


from pydantic import BaseModel, Field
from datetime import datetime, date, time, timezone, timedelta
from dateutil import parser
from typing import Any, Dict, Optional, Type

from bots.utils import validate_response, parse_input
from O365 import Account, FileSystemTokenBackend, MSGraphProtocol

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from langchain.tools import StructuredTool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
#from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import UnstructuredHTMLLoader
from langchain.docstore.document import Document
from bs4 import BeautifulSoup

from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA

from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)


load_dotenv(find_dotenv())
embeddings = OpenAIEmbeddings()


### With your own identity (auth_flow_type=='credentials') ####
def authenticate():
    credentials = (config.APP_ID, config.APP_PASSWORD)
    account = Account(credentials,auth_flow_type='credentials',tenant_id=config.tenant_id, main_resource=config.OFFICE_USER)
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
    return events


class MSGetCalendarEvents(BaseTool):
    name = "GET_CALENDAR_EVENTS"
    description = """useful for when you need to retrieve meetings and appointments
    To use the tool you must provide the following parameters "start_date" and "end_date"
    Be careful to always use double quotes for strings in the json string 
    """

    #return_direct= True
    def _run(self, start_date: str, end_date: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            notify_channel = connection.channel()
            notify_channel.queue_declare(queue='notify')
            
            ai_summary = ""
            human_summary = ""

            events = search_calendar(start_date, end_date)
            if events:
                for event in events:
                    ai_summary = ai_summary + " - Event: " + event.subject + ", At " + event.start.strftime("%A, %B %d, %Y at %I:%M %p") + "\n"
                    human_summary = human_summary + " - Event: " + event.subject + ", At " + event.start.strftime("%A, %B %d, %Y at %I:%M %p") + "\n"
                
                notify_channel.basic_publish(exchange='',routing_key='notify',body=human_summary)
            else:
                return "No events"
            
            return ai_summary
        except Exception as e:
            traceback.print_exc()
            return f'To use the tool you must provide the following parameters "start_date" "end_date"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GET_CALENDAR_EVENTS does not support async")