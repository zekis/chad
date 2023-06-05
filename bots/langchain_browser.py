import traceback

import config
from dotenv import find_dotenv, load_dotenv
#from flask import request
import json
import os
import re
import pika
import faiss
import urllib

from pydantic import BaseModel, Field
from datetime import datetime, date, time, timezone, timedelta
from typing import Any, Dict, Optional, Type

from bots.loaders.todo import MSGetTasks, MSGetTaskFolders, MSGetTaskDetail, MSSetTaskComplete, MSCreateTask, MSDeleteTask, MSCreateTaskFolder
from bots.rabbit_handler import RabbitHandler
#from bots.utils import encode_message, decode_message, generate_response, validate_response, parse_input, sanitize_string
from common.rabbit_comms import publish, publish_list, publish_draft_card, publish_draft_forward_card
from common.utils import generate_response, generate_whatif_response, generate_plan_response

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool
from langchain.tools import StructuredTool

#from langchain import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType

from langchain.vectorstores import FAISS
from langchain.docstore import InMemoryDocstore
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain import LLMChain, PromptTemplate
from langchain.agents import load_tools, Tool
from langchain.utilities import SerpAPIWrapper
from langchain.agents import initialize_agent, AgentType

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.document_loaders import WebBaseLoader



load_dotenv(find_dotenv())


class WebBot(BaseTool):
    name = "BROWSE"
    description = """useful for when you want to browse the internet bro.
    Specify the website you want to browse and the information you are after.
    Input should be a json string with two keys: 'website', 'query'
    Do not use escape characters
    Be careful to always use single quotes for strings in the json string
    """
    return_direct= True

    def _run(self, website: str = None, query: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            
            # if text:
            #     #question = text.get("question")
            #     website = text.get("website")
            
            #URL = urllib.parse.quote(website)
            print(f"{website} -> {query}")
            llm = ChatOpenAI(temperature=0)
           
            
            # text_splitter = RecursiveCharacterTextSplitter(
            #     # Set a really small chunk size, just to show.
            #     chunk_size = 100,
            #     chunk_overlap  = 20,
            #     length_function = len,
            # )
            
            loader = WebBaseLoader(website)
            documents = loader.load()

            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
            splitted_documents  = text_splitter.split_documents(documents)

            embeddings = OpenAIEmbeddings()

            print(f"Web texts: {documents}")
            
            web_db = Chroma.from_documents(splitted_documents, embeddings, collection_name="web")
            #web_db.persist()


            chain = RetrievalQAWithSourcesChain.from_chain_type(llm=llm, chain_type="stuff", retriever=web_db.as_retriever())
            response = chain({"question": query}, return_only_outputs=True)
            publish(response)
            
            return generate_response(response)
            
        except Exception as e:
            traceback.print_exc()
            return """The Input should be a json string with two keys: "website", "query".
            Or there was a problem with the request."""
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("BROWSE does not support async")

