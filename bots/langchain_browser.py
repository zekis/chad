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
from langchain.text_splitter import CharacterTextSplitter
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
    
    #search = SerpAPIWrapper()

    def _run(self, website: str = None, query: str = None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            
            # if text:
            #     #question = text.get("question")
            #     website = text.get("website")
            
            #URL = urllib.parse.quote(website)
            print(f"{website} -> {query}")
            llm = OpenAI(temperature=0)
            embeddings = OpenAIEmbeddings()
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
            
            loader = WebBaseLoader(website)
            docs = loader.load()
            web_texts = text_splitter.split_documents(docs)

            web_db = Chroma.from_documents(web_texts, embeddings, collection_name="web")
            web = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=web_db.as_retriever())
            response = web.run(query)


            print(response)
            return response
        except Exception as e:
            traceback.print_exc()
            return """The Input should be a json string with two keys: "website", "query".
            Or there was a problem with the request."""
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("BROWSE does not support async")
