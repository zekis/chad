import traceback
import config

from datetime import datetime#, date, time, timezone, timedelta
from dateutil import parser
from typing import Any, Dict, Optional, Type
from bots.langchain_assistant import generate_response
#from teams.card_factories import create_list_card, create_email_card, create_draft_reply_email_card, create_draft_forward_email_card, create_draft_email_card
from common.rabbit_comms import publish, publish_email_card, publish_list, publish_draft_card, publish_draft_forward_card, send_to_bot, publish_event_card
#from common.utils import generate_response, generate_whatif_response, generate_plan_response
#from common.utils import validate_response, parse_input, sanitize_string
from O365 import Account#, FileSystemTokenBackend, MSGraphProtocol

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool

from bs4 import BeautifulSoup

from langchain.chat_models import ChatOpenAI

from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

### With your own identity (auth_flow_type=='credentials') ####
def authenticate():
    credentials = (config.APP_ID, config.APP_PASSWORD)
    account = Account(credentials,auth_flow_type='credentials',tenant_id=config.TENANT_ID, main_resource=config.OFFICE_USER)
    account.authenticate()
    return account

# This function returns a summary of the given email using OpenAI's GPT-3 API.
def get_email_summary(email, body_soup):
    try:
        chat = ChatOpenAI(temperature=0, model_name="gpt-4")
        query = f"""Provide a summary of both the whole email chain and the latest message, ignoring capability statements and confidentiality disclaimers or anything after the signature for the following email
        From: {email.sender.address}
        Subject: {email.subject}
        Date: {email.received.strftime('%Y-%m-%d %H:%M:%S')}
        Body: {body_soup}"""

        print(f"Function Name: get_email_summary | Query: {query}")
        return chat([HumanMessage(content=query)]).content
    except Exception as e:
        traceback.print_exc()
        return f'Error getting email summary - Likely exceeded token limit'


def reply_to_email_summary(summary, comments=None, previous_draft=None):
    chat = ChatOpenAI(temperature=0, model_name="gpt-4")
    query = f"""Given this email summary: {summary}, please create a reasonable email response from 'Chad the AI Assistant' on behalf of {config.OFFICE_USER}.
    Response is to be HTML formatted and must include an informal 'To' salutation and opening line at the start and add a signature from 'Chad the AI Assistant'
    """
    if comments:
        query += f"Consider the following comments: {comments}"
    if previous_draft:
        query += f"Based on the previous draft: {previous_draft}"

    email_response = chat([HumanMessage(content=query)]).content
    print(f"Function Name: reply_to_email_summary | Query: {query}")
    return email_response

def forward_email_summary(summary, comments=None, previous_draft=None):
    chat = ChatOpenAI(temperature=0, model_name="gpt-4")
    query = f"""Given this email summary: {summary}, please create a reasonable email from 'Chad the AI Assistant' on behalf of {config.OFFICE_USER}.
    Response is to be HTML formatted and must include an informal 'To' salutation and opening line at the start and add a signature from 'Chad the AI Assistant'
    """
    if comments:
        query += f"Consider the following comments: {comments}"
    if previous_draft:
        query += f"Based on the previous draft: {previous_draft}"

    email_response = chat([HumanMessage(content=query)]).content
    print(f"Function Name: forward_email_summary | Query: {query}")
    return email_response

def modify_draft(body, comments, previous_draft=None):
    chat = ChatOpenAI(temperature=0, model_name="gpt-4")
    query = f"""Given this request: {body}, please create a reasonable email from 'Chad the AI Assistant' on behalf of {config.OFFICE_USER}
    Email is to be HTML formatted and must include an informal 'To' salutation and opening line at the start and add a signature from 'Chad the AI Assistant'
    """
    if comments:
        query += f"Consider the following comments: {comments}"
    if previous_draft:
        query += f"Based on the previous draft: {previous_draft}"

    email_response = chat([HumanMessage(content=query)]).content
    print(f"Function Name: modify_draft | Query: {query}")
    return email_response

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

# def mark_read(ObjectID):
#     print(f"Function Name: mark_read | ObjectID: {ObjectID}")
#     account = authenticate()
#     mailbox = account.mailbox()
#     inbox = mailbox.inbox_folder()
#     # Fetches a single email matching the given `ObjectID` from the inbox and marks it as read.
#     email = inbox.get_message(ObjectID)
#     email.mark_as_read()  
#     return True

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
    #print(f"Function Name: search_emails | Search Query: {search_query}")
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    query = inbox.new_query().search(search_query)

    emails = inbox.get_messages(limit=5, query=query)

    count = 0
    if emails:
        return emails
    return None

def create_email_reply(ConversationID, body, save=False):
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

    if save:
        #reply_msg.body += get_signature(config.EMAIL_SIGNATURE_HTML)
        reply_msg.save_draft()

    return reply_msg

def create_email_forward(ConversationID, recipient, body, save=False):
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
    
    if save:
        #reply_msg.body += get_signature(config.EMAIL_SIGNATURE_HTML)
        reply_msg.save_draft()

    return reply_msg


def draft_email(recipient, subject, body, user_improvements=None, previous_draft=None, save=True):
    print(f"Function Name: draft_email | Recipient: {recipient} | Subject: {subject}")
    account = authenticate()
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    if body or body != "":

        if user_improvements:
            body = modify_draft(body, user_improvements)
            if previous_draft:
                body = modify_draft(body, user_improvements, previous_draft)

        message = mailbox.new_message()
        message.to.add(recipient)
        message.subject = subject
        
        message.body = body

        if save:
            #message.body += get_signature(config.EMAIL_SIGNATURE_HTML)
            message.save_draft()
        
        return message
    

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

def format_email_summary_only(email, summary):
    email_s = f"""```
From: {email.sender.address}
Subject: {email.subject}
Date: {email.received.strftime('%Y-%m-%d %H:%M:%S')}
Summary: {summary}
```
"""
    return email_s

def format_email_header(email):
    header = { 'object_id': email.object_id, 'conversationid': email.conversation_id, 'subject': email.subject, 'from': email.sender.address }
    return header

def scheduler_check_emails():
    current_date_time = datetime.utcnow().strftime('%Y-%m-%d')
    query = f"isread:no received:{current_date_time}"
    
    #print(query)
    emails = search_emails(query)
    
    if emails:
        for email in emails:
            if not email.is_event_message:
                summary = get_email_summary(email, clean_html(email.body))
                publish_email_card("Email", email, summary)
                #publish a task question back to itself
                ai_summary = format_email_summary_only(email, summary)
                email.mark_as_read()
                send_to_bot(config.USER_ID,"Only If the following email requires " + config.FRIENDLY_NAME + " to perform an action such as reply, send a file, fix a problem, complete work etc, then use CREATE_TASK to create a new task in the Tasks folder. Email: " + ai_summary)
            else:
                publish_event_card("New Event", email.get_event())
                email.mark_as_read()
            #return ai_summary
    return None


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
            ai_summary = "SYSTEM:"
            human_summary = []
            if emails:
                for email in emails:
                    ai_summary = ai_summary + "From: " + email['from'] + ", Subject: " + email['subject'] + ", EmailID: " + email['object_id'] + ", ConversatonID: " + email['conversationid'] + "\n"
                    #human_summary.append(email['from'] + ": " + email['subject'] + ", EmailID: " + email['object_id'])
                    title = email['from'] + ": " + email['subject']
                    value = "Please use the GET_EMAIL_CHAIN using EmailID: " + email['object_id'] + " and create_task: False"
                    human_summary.append((title, value))
                #Attempt at sending cards
                #create_list_card("Choose an option:", [("Option 1", "1"), ("Option 2", "2"), ("Option 3", "3")])
                
                publish_list(f"Choose an option:", human_summary)
                return "Done"
            else:
                return "No emails found"

            #return ai_summary
            #return generate_response(ai_summary)

        except Exception as e:
            traceback.print_exc()
            return f'To use the tool you must provide the following search parameter "query" and "index"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("SEARCH_EMAILS does not support async")

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
    def _run(self, EmailID: str = None, ConversationID: str = None, create_task: bool = True, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
           
            if EmailID is not None:
                #response = get_email(EmailID)
                email = get_message(EmailID)

            if ConversationID is not None:
                #response = get_email_chain(ConversationID)
                email = get_conversation(ConversationID)

            if email:
                summary = get_email_summary(email, clean_html(email.body))
                publish_email_card("Email Review", email, summary)
                ai_summary = format_email_summary_only(email, summary)
                #return generate_response(ai_summary)
                #publish a task question back to itself
                if create_task:
                    send_to_bot(config.USER_ID,"Only If the following email requires " + config.FRIENDLY_NAME + " to urgently perform an action such as reply, send a file etc, then use CREATE_TASK tool to create a new task in the Tasks folder. Email: " + ai_summary)
                return "Done"
            else:
                return "No emails"

        except Exception as e:
            traceback.print_exc()
            return f'To use the tool you must provide one of the following parameters "EmailID" or "ConversationID"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GET_EMAIL_CHAIN does not support async")


class MSDraftEmail(BaseTool):
    name = "DRAFT_EMAIL"
    description = f"""useful for when you need to create a draft new email.
    Input should be a json string with three keys: "recipient" "subject" and "body" and optional "user_improvements" and "previous_draft"
    recipient should be a valid email address. user_improvements help the human direct the draft email and can be used in combination with the previous_draft.
    Be careful to always use double quotes for strings in the json string 
    """
    return_direct= True
    def _run(self, recipient: str, subject: str, body: str, user_improvements: str = None, previous_draft: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            response = draft_email(recipient, subject, body, user_improvements, previous_draft)
            #email_response = forward_email_summary(summary, user_improvements, previous_draft)
            publish_draft_card("New Draft Email", response, body, reply=False)
            response.delete()
            #return generate_response(response)
        except Exception as e:
            traceback.print_exc()
            return f'Input should be a json string with three keys: "recipient" "subject" and "body"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("CREATE_EMAIL does not support async")

class MSSendEmail(BaseTool):
    name = "SEND_EMAIL"
    description = f"""useful for when you need to send a draft email.
    Input should be a json string with three keys: "recipient" "subject", "body"
    recipient should be a valid email address.
    Be careful to always use double quotes for strings in the json string 
    """

    return_direct= True
    def _run(self, recipient: str, subject: str, body: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            response = draft_email(recipient, subject, body, save=True)
            publish("Email saved - Please manually send from outlook")
            return "Done"
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
    Be careful to always use double quotes for strings in the json string 
    """

    return_direct= True
    def _run(self, ConversationID: str, body: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            #create a draft email card and sends to the user for approval
            response = create_email_reply(ConversationID, body, True)
            publish("Email saved - Please manually send from outlook")
            return "Done"
        except Exception as e:
            traceback.print_exc()
            return f'To use the tool you must provide the following parameter "subject" "body"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("REPLY_TO_EMAIL does not support async")

class MSForwardEmail(BaseTool):
    name = "FORWARD_EMAIL"
    description = """useful for when you need to create a forward email to an existing email chain.
    To use the tool you must provide the following parameters "ConversationID" "body" "recipients"
    Be careful to always use double quotes for strings in the json string 
    """

    return_direct= True
    def _run(self, ConversationID: str, body: str,recipients: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            #create a draft email card and sends to the user for approval
            forward_email = create_email_forward(ConversationID, recipients, body, True)
            publish("Email saved - Please manually send from outlook")
            return "Done"
        except Exception as e:
            traceback.print_exc()
            return f'To use the tool you must provide the following parameter "subject" "body"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("REPLY_TO_EMAIL does not support async")

class MSDraftForwardEmail(BaseTool):
    name = "DRAFT_FORWARD_TO_EMAIL"
    description = """useful for when you need to generate a forward email to an existing email chain.
    To use the tool you must provide the following parameter "ConversationID" "recipients" and optional "user_improvements" and "previous_draft"
    user_improvements help the human direct the draft email and can be used in combination with the previous_draft.
    Be careful to always use double quotes for strings in the json string 
    """

    return_direct= True
    def _run(self, ConversationID: str, recipients: str, user_improvements: str = None, previous_draft: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            email_chain = get_conversation(ConversationID)
            summary = get_email_summary(clean_html(email_chain.body))
            email_response = forward_email_summary(summary, user_improvements, previous_draft)

            forward_email = create_email_forward(ConversationID, recipients, email_response, False)
            
            publish_draft_forward_card("New Forward Draft Email", forward_email, email_response)
            forward_email.delete()
            return "Done"
        except Exception as e:
            traceback.print_exc()
            return f'To use the tool you must provide the following parameter "ConversationID" "recipients" and optional "user_improvements" and "previous_draft"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("REPLY_TO_EMAIL does not support async")

class MSDraftReplyToEmail(BaseTool):
    name = "DRAFT_REPLY_TO_EMAIL"
    description = """useful for when you need to generate a reply to an existing email chain.
    To use the tool you must provide the following parameter "ConversationID", and optional "user_improvements" and "previous_draft"
    user_improvements help the human direct the draft email response and can be used in combination with the previous_draft.
    Be careful to always use double quotes for strings in the json string 
    """

    return_direct= True
    def _run(self, ConversationID: str, user_improvements: str = None, previous_draft: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            email_chain = get_conversation(ConversationID)
            summary = get_email_summary(email_chain, clean_html(email_chain.body))
            email_response = reply_to_email_summary(summary, user_improvements, previous_draft)

            reply_email = create_email_reply(ConversationID, email_response)

            publish_draft_card("New Draft Email", reply_email, email_response, True)
            reply_email.delete()
            return "Done"
        except Exception as e:
            traceback.print_exc()
            return f'To use the tool you must provide the following parameter "ConversationID", and optional "user_improvements" and "previous_draft"'
    
    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("REPLY_TO_EMAIL does not support async")
