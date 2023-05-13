import json
from typing import Any, Dict, Optional, Type
from langchain.text_splitter import CharacterTextSplitter

text_splitter = CharacterTextSplitter(        
    separator = "\n\n",
    chunk_size = 1000,
    chunk_overlap  = 200,
    length_function = len,
)

def validate_response(string):
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_text(string)
    for text in texts:
        print(str(text) + "\n")
    return texts[0]


def parse_input(text: str) -> Dict[str, Any]:
    """Parse the json string into a dict."""
    return json.loads(text)