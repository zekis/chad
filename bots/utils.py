import json
import re
from typing import Any, Dict, Optional, Type
from langchain.text_splitter import CharacterTextSplitter
from botbuilder.schema import ChannelAccount, CardAction, ActionTypes, SuggestedActions

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

def sanitize_email(body, max_length=2000):
    # Replace slashes with hyphens
    #subject = subject.replace("/", "-").replace("\\", "-")
    # Remove single quotes
    body = re.sub(r"'+", "", body)
    # Truncate the subject to the specified length
    body = body[:max_length]
    return body

def create_email(recipient,subject,body):
    clean_subject = sanitize_email(subject)
    clean_body = sanitize_email(body)
    return '{"recipient": "' + recipient + '", "subject": "' + clean_subject + '", "body": "' + clean_body + '"}'

def encode_message(type, prompt, actions: [CardAction] = None):
    actions = [action.__dict__ for action in actions] if actions else []
    message = {
        "type": type,
        "prompt": prompt,
        "actions": actions
    }
    print(f"ENCODING: {message}")
    return json.dumps(message)

def decode_message(message):
    message = message.decode("utf-8")
    print(f"DECODING: {message}")
    message_dict = json.loads(message)
    type = message_dict.get('type')
    prompt = message_dict.get('prompt')
    actions_data = message_dict.get('actions')
    actions = [CardAction(**action) for action in actions_data] if actions_data else []

    return type, prompt, actions