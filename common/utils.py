import traceback
import json
import re
import config
import nltk
import os

from typing import Any, Dict, Optional, Type
from langchain.text_splitter import CharacterTextSplitter
from botbuilder.schema import ChannelAccount, CardAction, ActionTypes, SuggestedActions
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

text_splitter = CharacterTextSplitter(        
    separator = "\n\n",
    chunk_size = 1000,
    chunk_overlap  = 200,
    length_function = len,
)

def validate_response(string):
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=2000, chunk_overlap=0)
    texts = text_splitter.split_text(string)
    # for text in texts:
    #     print(str(text) + "\n")
    return texts[0]


def parse_input(text: str) -> Dict[str, Any]:
    """Parse the json string into a dict."""

    clean_string = text.replace("```","")

    return json.loads(clean_string)

def sanitize_subject(subject, max_length=150):
    # Replace slashes with hyphens
    subject = subject.replace("/", "-").replace("\\", "-")
    
    # Remove or replace other special characters
    subject = re.sub(r"[^a-zA-Z0-9\-_]+", "_", subject)
    
    # Truncate the subject to the specified length
    subject = subject[:max_length]
    
    return subject

def sanitize_string(body, max_length=2000):
    # Replace slashes with hyphens
    #subject = subject.replace("/", "-").replace("\\", "-")
    # Remove single quotes
    body = re.sub(r"'+", "", body)
    # Truncate the subject to the specified length
    body = body[:max_length]
    return body

def create_email(recipient,subject,body):
    clean_subject = sanitize_string(subject)
    clean_body = sanitize_string(body)
    return '{"recipient": "' + recipient + '", "subject": "' + clean_subject + '", "body": "' + clean_body + '"}'

# def encode_message(type, prompt, actions: [CardAction] = None):
#     actions = [action.__dict__ for action in actions] if actions else []
#     message = {
#         "type": type,
#         "prompt": prompt,
#         "actions": actions
#     }
#     print(f"ENCODING: {message}")
#     return json.dumps(message)



def generate_whatif_response(text):
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    query = f"""given this information, write 2 short paragraph predicting what will happen next, one if everything went well and another if everything went wrong: {text}"""
    print(f"Function Name: generate_response | Text: {text}")
    return chat([HumanMessage(content=query)]).content

def generate_plan_response(text):
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    query = f"""given this information, what would you recommend: {text}"""
    print(f"Function Name: generate_response | Text: {text}")
    return chat([HumanMessage(content=query)]).content

def generate_response(text):
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    my_tasks = get_tasks(config.Todo_BotsTaskFolder)

    today = date.today() - timedelta(days=1)
    end_of_week = date.today() + timedelta(days=7)
    my_appointments = search_calendar(start_date=today.strftime('%Y-%m-%d'), end_date=end_of_week.strftime('%Y-%m-%d'))

    
    query = f"""My Calendar: {my_appointments} My tasks: {my_tasks} given this information, please recommend if I should create a task, add to my calander, respond with an email or ignore: {text}"""
    print(f"Function Name: generate_response | Text: {text}")
    return chat([HumanMessage(content=query)]).content

nltk.download("punkt")

def clean_and_tokenize(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'\b(?:http|ftp)s?://\S+', '', text)
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\d+', '', text)
    text = text.lower()
    return nltk.word_tokenize(text)

def format_documents(documents):
    numbered_docs = "\n".join([f"{i+1}. {os.path.basename(doc.metadata['source'])}: {doc.page_content}" for i, doc in enumerate(documents)])
    return numbered_docs

def format_user_question(question):
    question = re.sub(r'\s+', ' ', question).strip()
    return question