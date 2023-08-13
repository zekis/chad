import traceback
import config

from typing import Any, Dict, Optional, Type

from common.rabbit_comms import publish, publish_list, publish_draft_card, publish_draft_forward_card
from common.utils import tool_description, tool_error

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool

from langchain.chat_models import ChatOpenAI

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import WebBaseLoader


class WebBot(BaseTool):
    parameters = []
    optional_parameters = []
    name = "BROWSE"
    summary = "useful for when you want to scrape a website for information after using the GOOGLE tool to find a url"
    parameters.append({"name": "website", "description": "valid url" })
    parameters.append({"name": "query", "description": "search query to filter the scraped data" })
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, website: str = None, query: str = None, publish: str = "True", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
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
            hwebsite = ensure_http_or_https(website)
            loader = WebBaseLoader(hwebsite + "")
            documents = loader.load()

            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
            splitted_documents  = text_splitter.split_documents(documents)

            embeddings = OpenAIEmbeddings()

            print(f"Web texts: {documents}")
            
            web_db = Chroma.from_documents(splitted_documents, embeddings, collection_name="web")
            #web_db.persist()

            
            #chain = RetrievalQAWithSourcesChain.from_chain_type(llm=llm, chain_type="stuff", retriever=web_db.as_retriever())
            #response = chain({"question": query}, return_only_outputs=True)
            #publish(response)
            response = web_db.similarity_search(query)

            if publish.lower() == "true":
                publish(response[0].page_content)
                return config.PROMPT_PUBLISH_TRUE
            else:
                return response[0].page_content
            
        except Exception as e:
            traceback.print_exc()
            return tool_error(e, self.description)
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("BROWSE does not support async")

def ensure_http_or_https(url):
    if not url.startswith('http://') and not url.startswith('https://'):
        # Add https:// if the URL does not start with http:// or https://
        return 'https://' + url
    # If it already starts with http:// or https://, return it as is
    return url