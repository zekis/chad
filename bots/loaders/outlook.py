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

from teams.card_factories import create_list_card, create_email_card
from bots.utils import encode_message, decode_message
from bots.utils import validate_response, parse_input, sanitize_email
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



# This function returns a summary of the given email using OpenAI's GPT-3 API.
def get_email_summary(email):
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    query = f"Please provide a detailed summary, ignoring capability statements and confidentiality disclaimers for the following email: {email}"
    print(f"Function Name: get_email_summary | Query: {query}")
    return chat([HumanMessage(content=query)]).content

def reply_to_email_summary(summary):
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    query = f"""Given this email summary: {summary}, please create a reasonable email response from the perspective of {config.OFFICE_USER}.
    Response is to be HTML formatted and must include an informal 'To' salutation and opening line at the start and signature from the {config.EMAIL_SIGNATURE} at the end."""
    email_response = chat([HumanMessage(content=query)]).content
    print(f"Function Name: reply_to_email_summary | Query: {query}")
    return email_response

# def get_email_chain(ConversationID):
#     account = authenticate()
#     mailbox = account.mailbox()
#     inbox = mailbox.inbox_folder()

#     query = inbox.new_query().on_attribute('conversationid').equals(ConversationID)
#     print(f"Function Name: get_email_chain | Query: {query}")
#     emails = inbox.get_messages(limit=5,query=query)
    
#     count = 0
#     if emails:
#         final_response = ""
#         for email in emails:
#             count = count + 1
#             final_response = final_response + format_email_summary_only(email)
#         return final_response
#     return None

def get_conversation(ConversationID):
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    query = inbox.new_query().on_attribute('conversationid').equals(ConversationID)
    print(f"Function Name: get_conversation | Query: {query}")
    returned_emails = inbox.get_messages(limit=1,query=query)
    
    count = 0
    if returned_emails:
        emails = list(returned_emails)
        return emails[0]
    return None

# This function takes an `ObjectID` as input and returns the email associated with that ID.
def get_message(ObjectID):
    print(f"Function Name: get_message | ObjectID: {ObjectID}")
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()
    # Fetches a single email matching the given `ObjectID` from the inbox.
    returned_email = inbox.get_message(ObjectID)
    return returned_email

# # This function takes an `ObjectID` as input and returns the email associated with that ID.
# def get_email(ObjectID):
#     print(f"Function Name: get_email | ObjectID: {ObjectID}")
#     account = authenticate()
#     mailbox = account.mailbox()
#     inbox = mailbox.inbox_folder()
#     # Fetches a single email matching the given `ObjectID` from the inbox.
#     email = inbox.get_message(ObjectID)
#     final_response = format_email(email)        
#     return final_response

def mark_read(ObjectID):
    print(f"Function Name: mark_read | ObjectID: {ObjectID}")
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()
    # Fetches a single email matching the given `ObjectID` from the inbox and marks it as read.
    email = inbox.get_message(ObjectID)
    email.mark_as_read()  
    return True

def search_emails_return_unique_conv(search_query):
    print(f"Function Name: search_emails_return_unique_conv | Search Query: {search_query}")
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    query = inbox.new_query().search(search_query)

    emails = inbox.get_messages(limit=5, query=query)

    count = 0
    if emails:
        final_response = []
        conversation_ids = set()  # Using a set to keep track of unique conversation_ids
        for email in emails:
            if email.conversation_id not in conversation_ids:  # Check if conversation_id is unique
                conversation_ids.add(email.conversation_id)  # Add the unique conversation_id to the set
                final_response.append(format_email_header(email))  # Only append if conversation_id is unique
        return final_response
    return None

def search_emails(search_query):
    print(f"Function Name: search_emails | Search Query: {search_query}")
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    query = inbox.new_query().search(search_query)

    emails = inbox.get_messages(limit=5, query=query)

    count = 0
    if emails:
        return emails
    return None

def create_email_reply(ConversationID, body):
    print(f"Function Name: create_email_reply | Conversation ID: {ConversationID} | Body: {body}")
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    query = inbox.new_query().on_attribute('conversationid').equals(ConversationID)
    
    emails = list(inbox.get_messages(limit=1, query=query))
    email = emails[0]

    email.mark_as_read()
    reply_msg = email.reply()

    reply_msg.body = body

    reply_msg.save_draft()
    return "Email Reply Created"

def create_email_forward(ConversationID, recipient, body):
    print(f"Function Name: create_email_forward | Conversation ID: {ConversationID} | Recipient: {recipient} | Body: {body}")
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    query = inbox.new_query().on_attribute('conversationid').equals(ConversationID)

    emails = list(inbox.get_messages(limit=1, query=query))
    email = emails[0]
    

    email.mark_as_read()
    reply_msg = email.reply()
    reply_msg.to.clear()
    reply_msg.cc.clear()
    reply_msg.to.add(recipient)
    reply_msg.body = body
    
    reply_msg.save_draft()
    return "Forward Email Created"


def draft_email(recipient, subject, body):
    print(f"Function Name: draft_email | Recipient: {recipient} | Subject: {subject}")
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    if body or body != "":
        message = mailbox.new_message()
        message.to.add(recipient)
        message.subject = subject
        message.body = body
        message.save_draft()
        publish_card("Draft Email", message, message.body)
        publish(preview_email(message))
        return "Email Created and Sent"
    else:
        return "email must contain a body. Perhaps work out what content you need to send first"

def clean_html(html):
    remove_strings = [
        "SG Controls - Capability Statement",
        "SG Controls - Case Studies",
        "SG Controls - Technical Services",
        "SG Controls Pty Ltd is ISO 9001 Quality certified, safety aware and environmentally conscious.",
        "This email contains material, which may be confidential, legally privileged, and/or the subject of copyright.",
        "If you are not an intended recipient, please advise the sender and delete it.",
        "Confidentiality and privilege are not waived.",
        "The views or opinions expressed in this email may be the sender",
        "own and not necessarily shared / authorised by SG Controls Pty Ltd.",
        "No liability for loss or damage resulting from your receipt of / dealing with this email is accepted.",
        "INTERNAL EMAIL: This email originated from inside the SG Controls network.",
        "CAUTION: This email originated from outside of the organisation. Do not click links or open attachments unless you recognise the sender and know the content is safe."]
    soup = BeautifulSoup(html, 'html.parser')
    # Remove unnecessary tags
    for tag in soup(['style', 'script', 'img']):
        tag.decompose()
    clean_text = soup.get_text()
    for s in remove_strings:
        clean_text = clean_text.replace(s, '')
    #finally truncate the message to avoid token errors
    clean_text = clean_text[:8000]
    return clean_text

# def format_email(email, include_summary=True):
#     clean_email = ""
#     header = f"""```
# Subject: {email.subject}
# From: {email.sender.address}
# To: {', '.join([recipient.address for recipient in email.to[:5]])} {f"Cc: {', '.join([recipient.address for recipient in email.cc[:5]])}" if email.cc else ""} {f"Bcc: {', '.join([recipient.address for recipient in email.bcc[:5]])}" if email.bcc else ""}
# Importance: {email.importance.value}
# Is Read: {email.is_read}
# Has Attachment: {email.has_attachments}
# Date: {email.received.strftime('%Y-%m-%d %H:%M:%S')}
# """
#     if include_summary:
#         summary = header + "\nSummary: " + get_email_summary(clean_html(email.body)) + "\n"
#     else:
#         summary = header

#     summary = summary + "```\n"
#     return summary

def format_email_summary_only(email, summary):
    email_s = f"""```
From: {email.sender.address}
Subject: {email.subject}
Date: {email.received.strftime('%Y-%m-%d %H:%M:%S')}
Summary: {summary}
```
"""
    return email_s

# def preview_email(email):
#     clean_email = ""
#     preview = f"""```
# To: {', '.join([recipient.address for recipient in email.to[:5]])}
# Subject: {email.subject}
# Body: {email.body}
# ```
# """
#     return preview


def format_email_header(email):
    header = { 'object_id': email.object_id, 'conversationid': email.conversation_id, 'subject': email.subject, 'from': email.sender.address }
    return header

def scheduler_check_emails():
    # connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    # notify_channel = connection.channel()
    # notify_channel.queue_declare(queue='message')

    current_date_time = datetime.now().strftime('%Y-%m-%d')
    query = f"isread:no received:{current_date_time}"
    
    #print(query)
    emails = search_emails(query)
    
    if emails:
        for email in emails:
            summary = get_email_summary(clean_html(email.body))
            publish_card("Email", email, summary)
            ai_summary = format_email_summary_only(email, summary)
            email.mark_as_read()
            return ai_summary
    return None

def publish(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    notify_channel = connection.channel()
    notify_channel.queue_declare(queue='notify')
    message = encode_message("prompt", message)
    notify_channel.basic_publish(exchange='',routing_key='notify',body=message)

def publish_list(message,strings_values):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    notify_channel = connection.channel()
    notify_channel.queue_declare(queue='notify')
    
    #convert string to dict (hopefully our AI has formatted it correctly)
    try:
        cards = create_list_card(message,strings_values)
        #cards = create_list_card("Choose an option:", [("Option 1", "1"), ("Option 2", "2"), ("Option 3", "3")])
    except Exception as e:
        traceback.print_exc()
        cards = None
    
    message = encode_message("cards", message, cards)
    notify_channel.basic_publish(exchange='',routing_key='notify',body=message)

def publish_card(message,email,summary):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    notify_channel = connection.channel()
    notify_channel.queue_declare(queue='notify')
    
    #convert string to dict (hopefully our AI has formatted it correctly)
    try:
        cards = create_email_card(message,email,summary)
    except Exception as e:
        traceback.print_exc()
        cards = None
    
    message = encode_message("cards", message, cards)
    notify_channel.basic_publish(exchange='',routing_key='notify',body=message)


class MSSearchEmailsId(BaseTool):
    name = "SEARCH_EMAILS_RETURN_IDS"
    description = """useful for when you need to search through emails and get their IDs.
    This tool only returns 5 emails maximum.
    To use the tool you must provide the following search parameter "query"
    query must use the Keyword Query Language (KQL) syntax. Example query: from:Dan AND received:2023-05-19..2023-05-20
    """
    return_direct= True
    def _run(self, query: str, index: int = 1, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            print(query)
            emails = search_emails_return_unique_conv(query)
            #response = validate_response(emails)
            ai_summary = ""
            human_summary = []
            if emails:
                for email in emails:
                    ai_summary = ai_summary + "From: " + email['from'] + ", Subject: " + email['subject'] + ", EmailID: " + email['object_id'] + ", ConversatonID: " + email['conversationid'] + "\n"
                    #human_summary.append(email['from'] + ": " + email['subject'] + ", EmailID: " + email['object_id'])
                    title = email['from'] + ": " + email['subject']
                    value = "Please use the GET_EMAIL_CHAIN using EmailID: " + email['object_id']
                    human_summary.append((title, value))
                #Attempt at sending cards
                #create_list_card("Choose an option:", [("Option 1", "1"), ("Option 2", "2"), ("Option 3", "3")])
                
                publish_list(f"Choose an option:", human_summary)
                
            else:
                return "No emails found"

            #return ai_summary
            return "Let me know if their is anything else I can do."

        except Exception as e:
            traceback.print_exc()
            return f'To use the tool you must provide the following search parameter "query" and "index"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("SEARCH_EMAILS does not support async")

# class MSSearchEmails(BaseTool):
#     name = "SEARCH_EMAILS"
#     description = """useful for when you need to search through emails and get summaries.
#     To use the tool you must provide the following search parameter "query"
#     query must use the Keyword Query Language (KQL) syntax. Example query: from:Dan AND received:2023-05-19..2023-05-20
#     """
#     #return_direct= True
#     def _run(self, query: str, notify: bool = True, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
#         """Use the tool."""
#         try:
#             print(query)
#             emails = search_emails_return_unique_conv(query)
#             ai_summary = ""
#             human_summary = []
#             if emails:
#                 for email in emails:
#                     summary = summary + "From: " + email['from'] + ", Subject: " + email['subject'] + ", EmailID: " + email['object_id'] + ", ConversatonID: " + email['conversationid'] + "\n"
#                     human_summary.append(email['from'] + ", Subject: " + email['subject'])
#                      #Attempt at sending cards
                
#                 if notify:
#                     publish_card(f"{len(emails)} Email/s", human_summary)
#                 response = []
#                 for email in emails:
#                     email_chain = get_email_chain(email['conversationid'])
#                     response.append(email_chain)
#                     publish(email_chain)
#             else:
#                 return "No emails found"  
                
#             return ai_summary
            
#         except Exception as e:
#             traceback.print_exc()
#             return f'To use the tool you must provide the following search parameter "query" and "index"'
    
#     async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
#         """Use the tool asynchronously."""
#         raise NotImplementedError("SEARCH_EMAILS_RETURN_SUMMARY does not support async")

class MSGetEmailDetail(BaseTool):
    name = "GET_EMAIL_CHAIN"
    description = """useful for when you need to get the email content for a single email or email chain.
    To use the tool you must provide one of the following parameters "EmailID" or "ConversationID"
    You can get the Email ID or conversation IDs by using the SEARCH_EMAILS tool
    Input should be a json string with one key: "ConversationID"
    Be careful to always use double quotes for strings in the json string
    Returns email headers and the body. 
    """
    return_direct= True
    def _run(self, EmailID: str = None, ConversationID: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
           
            if EmailID is not None:
                #response = get_email(EmailID)
                email = get_message(EmailID)

            if ConversationID is not None:
                #response = get_email_chain(ConversationID)
                email = get_conversation(ConversationID)

            if email:
                summary = get_email_summary(clean_html(email.body))
                publish_card("Email", email, summary)
                ai_summary = format_email_summary_only(email, summary)
                return "Let me know if their is anything else I can do."
            
            return "No emails"

        except Exception as e:
            traceback.print_exc()
            return f'To use the tool you must provide one of the following parameters "EmailID" or "ConversationID"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GET_EMAIL_CHAIN does not support async")


class MSCreateEmail(BaseTool):
    name = "CREATE_EMAIL"
    description = f"""useful for when you need to create a new email.
    Input should be a json string with three keys: "recipient" "subject" and "body"
    recipient should be a valid email address.
    body should be html formatted and must include a salutation and opening line at the start and signature from the {config.EMAIL_SIGNATURE} at the end.
    Be careful to always use double quotes for strings in the json string 
    """
    return_direct= True
    def _run(self, recipient: str, subject: str, body: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            response = draft_email(recipient, subject, body)
            return validate_response(response)
        except Exception as e:
            traceback.print_exc()
            return f'Input should be a json string with three keys: "recipient" "subject" and "body"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("CREATE_EMAIL does not support async")

class MSSendEmail(BaseTool):
    name = "SEND_EMAIL"
    description = f"""useful for when you need to send a new email.
    Input should be a json string with three keys: "recipient" "subject", "body"
    recipient should be a valid email address.
    body should be html formatted must include a salutation and opening line at the start and signature from the {config.EMAIL_SIGNATURE} at the end.
    Be careful to always use double quotes for strings in the json string 
    """

    return_direct= True
    def _run(self, recipient: str, subject: str, body: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            response = draft_email(recipient, subject, body)
            return validate_response(response)
        except Exception as e:
            traceback.print_exc()
            return f'Input should be a json string with three keys: "recipient" "subject", "body"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("CREATE_EMAIL does not support async")

class MSReplyToEmail(BaseTool):
    name = "REPLY_TO_EMAIL"
    description = """useful for when you need to create a reply to an existing email chain.
    To use the tool you must provide the following parameter "ConversationID" "body"
    body should be html formatted must include a salutation and opening line at the start and signature from the sender at the end.
    Be careful to always use double quotes for strings in the json string 
    """

    return_direct= True
    def _run(self, ConversationID: str, body: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            response = create_email_reply(ConversationID, body)
            return validate_response(response)
        except Exception as e:
            traceback.print_exc()
            return f'To use the tool you must provide the following parameter "subject" "body"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("REPLY_TO_EMAIL does not support async")

class MSForwardEmail(BaseTool):
    name = "FORWARD_EMAIL"
    description = """useful for when you need to forward an existing email chain.
    To use the tool you must provide the following parameter "ConversationID" "recipient "body"
    body should be html formatted must include a salutation and opening line at the start and signature from the sender at the end.
    Be careful to always use double quotes for strings in the json string 
    """

    return_direct= True
    def _run(self, ConversationID: str, recipient: str, body: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            response = create_email_forward(ConversationID, recipient, body)
            return validate_response(response)
        except Exception as e:
            traceback.print_exc()
            return f'To use the tool you must provide the following parameter "subject" "body"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("REPLY_TO_EMAIL does not support async")

class MSAutoReplyToEmail(BaseTool):
    name = "AUTO_REPLY_TO_EMAIL"
    description = """useful for when you need to auto reply to an existing email chain.
    To use the tool you must provide the following parameter "ConversationID"
    Be careful to always use double quotes for strings in the json string 
    """

    return_direct= True
    def _run(self, ConversationID: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            email_chain = get_conversation(ConversationID)
            summary = get_email_summary(clean_html(email.body))
            email_response = reply_to_email_summary(summary)

            response = create_email_reply(ConversationID, email_response)
            return validate_response(response)
        except Exception as e:
            traceback.print_exc()
            return f'To use the tool you must provide the following parameter "ConversationID" "body"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("REPLY_TO_EMAIL does not support async")