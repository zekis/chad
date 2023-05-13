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
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import UnstructuredHTMLLoader
from bs4 import BeautifulSoup


load_dotenv(find_dotenv())

embeddings = OpenAIEmbeddings()

### With your own identity (auth_flow_type=='credentials') ####
def authenticate():
    credentials = (config.APP_ID, config.APP_PASSWORD)
    account = Account(credentials,auth_flow_type='credentials',tenant_id=config.tenant_id, main_resource=config.OFFICE_USER)
    account.authenticate()
    return account

def get_emails(search_query):
    #returns todays email headers without the body
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    today = datetime.now()
    yesterday = today - timedelta(days=1)

    start_date = datetime(yesterday.year, yesterday.month, yesterday.day)
    end_date = datetime.now()
    
    #Generate API Query
    #TODO: add check to make sure we dont spam this API too much
    query = inbox.new_query().on_attribute('receivedDateTime').greater_equal(start_date)\
                            .chain('and').on_attribute('receivedDateTime').less(end_date)
    
    #Get emails from API
    emails = inbox.get_messages(limit=10, query=query)
    #show the body if only one email returned
    
    count = 0
    if emails:
        final_response = ""
        for email in emails:
            count = count + 1
            email_html = format_email(email, False)
            final_response = final_response + email_html
        #if only one record, response can include body
        if count == 1:
            email = emails[0]
            final_response = format_email(email, True)
        return final_response

    return "No emails found"

def get_email_chain(subject):
    #returns a search for a Vector DB with todays emails
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    today = datetime.now()
    yesterday = today - timedelta(days=1)

    start_date = datetime(yesterday.year, yesterday.month, yesterday.day)
    end_date = datetime.now()

    query = inbox.new_query().on_attribute('subject').contains(subject)
    
    #Get emails from API
    emails = inbox.get_messages(limit=4, query=query)
       

    count = 0
    if emails:
        final_response = ""
        for email in emails:
            count = count + 1
            email_html = format_email(email, True)
            final_response = final_response + email_html

        #if only one record, response can include body
        if count == 1:
            email = emails[0]
            final_response = format_email(email, True)
        return final_response

def search_emails(search_query):
    #returns a search for a Vector DB with todays emails
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    today = datetime.now()
    yesterday = today - timedelta(days=1)

    start_date = datetime(yesterday.year, yesterday.month, yesterday.day)
    end_date = datetime.now()

    query = inbox.new_query().search(search_query)
    
    #Get emails from API
    emails = inbox.get_messages(limit=10, query=query)
    
    count = 0   
    if emails:
        final_response = ""
        for email in emails:
            email_html = format_email(email, False)
            final_response = final_response + email_html

        #if only one record, response can include body
        if count == 1:
            email = emails[0]
            final_response = format_email(email, True)
        return final_response


def create_email_reply(subject, body):
    #returns a search for a Vector DB with todays emails
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    today = datetime.now()
    yesterday = today - timedelta(days=1)

    start_date = datetime(yesterday.year, yesterday.month, yesterday.day)
    end_date = datetime.now()

    query = inbox.new_query().on_attribute('subject').contains(subject)
    
    #Get emails from API
    emails = inbox.get_messages(limit=1, query=query)
    email = emails[0]

    email.mark_as_read()
    reply_msg = message.reply()

    reply_msg.body = body

    reply_msg.save_draft()
    return "Email Reply Created"

def create_email_forward(recipient, subject, body):
    #returns a search for a Vector DB with todays emails
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    today = datetime.now()
    yesterday = today - timedelta(days=1)

    start_date = datetime(yesterday.year, yesterday.month, yesterday.day)
    end_date = datetime.now()

    query = inbox.new_query().on_attribute('subject').equals(subject)
    
    #Get emails from API
    emails = inbox.get_messages(limit=1, query=query)
    email = emails[0]

    email.mark_as_read()
    reply_msg = email.reply()

    reply_msg.body = body

    reply_msg.save_draft()
    return "Forward Email Created"


def create_email(recipient, subject, body):
    #returns a search for a Vector DB with todays emails
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    today = datetime.now()
    yesterday = today - timedelta(days=1)

    start_date = datetime(yesterday.year, yesterday.month, yesterday.day)
    end_date = datetime.now()

    if body or body != "":
        message = mailbox.new_message()
        message.to.add(recipient)
        message.subject = subject
        message.body = body
        message.save_draft()
        return "Email Created"
    else:
        return "email must contain a body. Perhaps work out what content you need to send first"

def read_emails_to_loader(file):
    #Load the emails from file
    loader = UnstructuredHTMLLoader(file)
    data = loader.load()
    if data:
        # Split the text file
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(data)
        
        # Create vector DB
        db = FAISS.from_documents(docs, embeddings)
        print("FAISS object:", db)
        return db
    return None
    

def sanitize_subject(subject, max_length=50):
    # Replace slashes with hyphens
    subject = subject.replace("/", "-").replace("\\", "-")
    
    # Remove or replace other special characters
    subject = re.sub(r"[^a-zA-Z0-9\-_]+", "_", subject)
    
    # Truncate the subject to the specified length
    subject = subject[:max_length]
    
    return subject

def clean_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Remove unnecessary tags
    for tag in soup(['style', 'script', 'img']):
        tag.decompose()

    # Remove multiple spaces, new lines, and tabs
    #clean_text = re.sub(r'\s+', ' ', soup.get_text())
    clean_text = soup.get_text()

    # Remove leading and trailing spaces
    #clean_text = clean_text.strip()

    return clean_text

def format_email(email, include_body=True):
    
    clean_email = ""

    header = f"""
    Subject: {email.subject}
    From: {email.sender.address}
    To: {', '.join([recipient.address for recipient in email.to])}
    {f"Cc: {', '.join([recipient.address for recipient in email.cc])}" if email.cc else ""}
    {f"Bcc: {', '.join([recipient.address for recipient in email.bcc])}" if email.bcc else ""}
    Importance: {email.importance.value}
    Is Read: {email.is_read}
    Has Attachment: {email.has_attachments}
    Date: {email.received.strftime('%Y-%m-%d %H:%M:%S')}
    """

    if include_body:
        # Clean email body
        clean_email = clean_html(header + email.body)
    else:
        clean_email = clean_html(header)

    return clean_email

class MSGetEmails(BaseTool):
    name = "GET_EMAILS"
    description = """useful for when you need to get todays emails.
    Returns email headers without the body. 
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)
            response = get_emails(text)
            return validate_response(response)
        except Exception as e:
            traceback.print_exc()
            return f"Exception retrieving emails ({e})"
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GET_EMAILS does not support async")

class MSSearchEmails(BaseTool):
    name = "SEARCH_EMAILS"
    description = """useful for when you need to get search through emails.
    To use the tool you must provide the a string to search for.
    Returns email headers without the body. 
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)
            response = search_emails(text)
            return validate_response(response)
        except Exception as e:
            traceback.print_exc()
            return f"Exception searching emails ({e})"
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("SEARCH_EMAILS does not support async")
    

class MSGetEmailDetail(BaseTool):
    name = "GET_EMAIL_CHAIN"
    description = """useful for when you need to get the details and content of a single email chain.
    To use the tool you must provide the following parameter ["subject"]
    Input should be a json string with one key: "subject"
    Be careful to always use double quotes for strings in the json string
    Returns email headers and the body. 
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)
            data = parse_input(text)
            subject = data.get("subject")

            response = get_email_chain(subject)
            return validate_response(response)
        except Exception as e:
            traceback.print_exc()
            return f"Exception retrieving emails ({e})"
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GET_EMAIL_CHAIN does not support async")


class MSCreateEmail(BaseTool):
    name = "CREATE_EMAIL"
    description = f"""useful for when you need to create a new draft email.
    Input should be a json string with three keys: "recipient" "subject", "body"
    recipient should be a valid email address.
    body should be html formatted must include a salutation and opening line at the start and signature from the {config.EMAIL_SIGNATURE} at the end.
    Be careful to always use double quotes for strings in the json string 
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)
            data = parse_input(text)
            recipient = data.get("recipient")
            subject = data.get("subject")
            body = data.get("body")
            response = create_email(recipient, subject, body)
            return validate_response(response)
        except Exception as e:
            traceback.print_exc()
            return f"Exception creating email ({e})"
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("CREATE_EMAIL does not support async")

class MSReplyToEmail(BaseTool):
    name = "REPLY_TO_EMAIL"
    description = """useful for when you need to create a reply to an existing email chain.
    To use the tool you must provide the following parameter ["subject", "body"]
    Input should be a json string with three keys: "recipient" "subject", "body"
    body should be html formatted must include a salutation and opening line at the start and signature from the sender at the end.
    Be careful to always use double quotes for strings in the json string 
    """
    #args_schema: Type[MSTodoToolSchema] = MSTodoToolSchema

    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(text)
            data = parse_input(text)
            
            subject = data.get("subject")
            body = data.get("body")
            response = create_email_reply(subject, body)
            return validate_response(response)
        except Exception as e:
            traceback.print_exc()
            return f"Exception creating email ({e})"
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("REPLY_TO_EMAIL does not support async")