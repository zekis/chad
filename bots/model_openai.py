from dotenv import find_dotenv, load_dotenv

from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.agents import AgentType, Tool, ZeroShotAgent, AgentExecutor

from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain import OpenAI, LLMChain
#from langchain_app.prompts.self_healing_code_prompt import template_suffix
from langchain.llms import OpenAI
from langchain.agents import tool


import textwrap
import config
import os
import datetime
import re


load_dotenv(find_dotenv())

# chat = ChatOpenAI(model_name="gpt-3.5-turbo",temperature=0, max_tokens=256)
llm = OpenAI(temperature=0)



# async def custom_prompt_func(prompt: str) -> None:
#     print(f"Custom prompt: {prompt}")
#     await calling_instance.turn_instance.send_activity(f"{prompt}")





tools = load_tools(["wikipedia", "google-search", "llm-math", "requests", "python_repl","terminal"], llm=llm)
# Assuming the "human" tool is the first one in the list


# Set the custom prompt and input functions
# human_tool.prompt_func = custom_prompt_func


prefix = """Have a conversation with a human, answering the following questions as best you can. You have access to the following tools:"""
suffix = """and the windows terminal. Begin!"

{chat_history}
Question: {input}
{agent_scratchpad}"""

prompt = ZeroShotAgent.create_prompt(
    tools, 
    prefix=prefix, 
    suffix=suffix, 
    input_variables=["input", "chat_history", "agent_scratchpad"]
)
memory = ConversationBufferMemory(memory_key="chat_history")

llm_chain = LLMChain(llm=OpenAI(temperature=0), prompt=prompt)
agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True, return_intermediate_steps=True)
agent_chain = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory)

#this bot needs to provide similar commands as autoGPT except the commands are based on Check Email, Check Tasks, Load Doc, Load Code etc.
def chad_response(msg, self_instance):
    Calling_instance = self_instance
    
    try:
        #history.predict(input=msg)
        if msg == 'agent.template':
            response = "NA:"
            return response
        response = agent_chain.run(msg)
        #history.chat_memory.add_ai_message(response)
        return response
    except Exception as e:
        return f"An exception occurred: {e}"
    
