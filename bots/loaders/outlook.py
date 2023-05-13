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
    emails = inbox.get_messages(query=query)
    if emails:
        final_response = ""
        for email in emails:
            email_html = format_email(email, False)
            final_response = final_response + email_html
        
        return final_response
    return "No emails found"

def get_email(search_query):
    #returns a search for a Vector DB with todays emails
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
    emails = inbox.get_messages(query=query)
    if emails:
        output_file = config.EMAIL_CACHE_FILE_NAME
        #Clear cache
        if os.path.exists(output_file):
            os.remove(output_file)
        
        #Write emails to cache after formatting to html
        final_response = ""
        for email in emails:
            email_html = format_email(email, False)

            final_response = final_response + email_html
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(email_html)
        
        #get Vector DB and filter with emails
        #db = read_emails_to_loader(config.EMAIL_CACHE_FILE_NAME)
        #filtered_emails = db.similarity_search(search_query, k=4)
        
        
        #final_response = " ".join([d.page_content for d in filtered_emails])
        final_response = " ".join([email for d in filtered_emails])
        return final_response

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
            return f"Exception retrieving emails ({e})"
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MSGetTasks does not support async")


    

