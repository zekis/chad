import traceback
import config
from datetime import datetime
import json
import pika
import os
import time 
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, Type

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool



class ToolManGetTools(BaseTool):
    name = "GET_ASSISTANTS"
    description = """useful for when you want to get a list of available assistants.
    """
    #return_direct= True

    def _run(self, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            attempts = 3
            while attempts > 0:
                publish_to_manager(config.USER_ID, "GET_TOOLS")
                response = get_manager_response()
                if response == 'timeout':
                    attempts -= 1
                elif response:
                    break
            if response == "timeout":
                return "timeout"
            # tools = json.loads(response)

            assistants = []
            data = json.loads(response)
            for item in data:
                summary = f"name: {item['name']}, description: {item['description']}, parameters: {item['parameters']} onboarded: {item['test_result']}\n"
                assistants.append(summary)

            return assistants
            
        except Exception as e:
            traceback.print_exc()
            return f"""{e}"""
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GET_ASSISTANTS does not support async")

class ToolManNewTool(BaseTool):
    name = "HIRE_ASSISTANT"
    description = """useful for when you want to hire a new assistant.
    To use the tool you must provide the following parameter "title", "description" and "parameters"
    Optionaly include "feedback" and test values as "parameter_value_pairs".
    parameters should be an array of parameters the assistant should use as input, for example ['filename', 'content']
    For APIs and if credentials are required use the GET_CREDENTIAL tool and pass them as additional parameters
    Be careful to always use double quotes for strings in the json string 
    """
    #return_direct= True

    def _run(self,title: str, description: str, parameters: str, feedback: str=None, parameter_value_pairs: str=None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:

            attempts = 3
            while attempts > 0:
                publish_to_manager(config.USER_ID, 'NEW_TOOL', {'toolname': title.lower(), 'description': description, 'parameters': parameters, 'feedback': feedback, 'values': parameter_value_pairs})
                response = get_manager_response(5)
                if response == "timeout":
                    attempts -= 1
                elif response:
                    break
            if response == "timeout":
                return "timeout"
            return json.dumps(response, indent=2, sort_keys=True)
            
        except Exception as e:
            traceback.print_exc()
            return f"""{e}"""
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("HIRE_ASSISTANT does not support async")

class ToolManEditTool(BaseTool):
    name = "UPDATE_ASSISTANT"
    description = """useful for when you want to change the parameters for an existing assistant
    To use the tool you must provide the following parameter "title", "description" "parameters" "changes" and optional "feedback" and testing values "parameter_value_pairs"
    feedback allows for the bot to provide comments and feedback to errors or issues that arrise.
    parameters should be an array of parameters the tool should use as input, for example ['filename', 'content']
    For APIs and if credentials are required use the GET_CREDENTIAL tool and pass them as additional parameters
    Be careful to always use double quotes for strings in the json string 
    """
    #return_direct= True

    def _run(self,title: str, description: str, parameters: str, changes: str, feedback: str=None, parameter_value_pairs: str=None, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            attempts = 1
            while attempts > 0:
                publish_to_manager(config.USER_ID, 'EDIT_TOOL', {'toolname': title.lower(), 'description': description, 'parameters': parameters, 'changes': changes, 'feedback': feedback, 'values': parameter_value_pairs})
                response = get_manager_response(5)
                if response == "timeout":
                    attempts -= 1
                elif response:
                    break
            
            return json.dumps(response, indent=2, sort_keys=True)
            
        except Exception as e:
            traceback.print_exc()
            return f"""{e}"""
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("UPDATE_ASSISTANT does not support async")

class ToolManTestTool(BaseTool):
    name = "EVALUATE_ASSISTANT"
    description = """useful for when you want to test an existing assistants abilities.
    To use the tool you must provide the following parameter "title", "parameters_value_pairs"
    feedback allows for the bot to provide comments and feedback to errors or issues that arrise.
    parameters should be json string of parameters and values that the tool needs to do the job
    For example "filename": "test.txt", "content": "hello world"
    Be careful to always use double quotes for strings in the json string 
    """
    #return_direct= True

    def _run(self,title: str, parameters_value_pairs: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            attempts = 1
            while attempts > 0:
                publish_to_manager(config.USER_ID, 'TEST_TOOL', {'toolname': title.lower(), 'values': parameters_value_pairs})
                response = get_manager_response(3)
                if response == "timeout":
                    attempts -= 1
                elif response:
                    break

            return json.dumps(response, indent=2, sort_keys=True)
            
        except Exception as e:
            traceback.print_exc()
            return f"""{e}"""
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("EDIT_TOOL does not support async")

class ToolManRemoveTool(BaseTool):
    name = "RELIEVE_ASSISTANT"
    description = """useful for when you want to relieve an existing assistant that is not working.
    To use the tool you must provide the following parameter "title"
    Be careful to always use double quotes for strings in the json string 
    """
    #return_direct= True

    def _run(self,title: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            attempts = 1
            while attempts > 0:
                publish_to_manager(config.USER_ID, 'REMOVE_TOOL', {'toolname': title.lower()})
                response = get_manager_response(1)
                if response == "timeout":
                    attempts -= 1
                elif response:
                    break

            return json.dumps(response, indent=2, sort_keys=True)
            
        except Exception as e:
            traceback.print_exc()
            return f"""{e}"""
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("EDIT_TOOL does not support async")

class ToolManStartTool(BaseTool):
    name = "ENGAGE_ASSISTANT"
    description = """useful for when you want the assistants to begin.
    To use the tool you must provide the following parameter "title", "parameters_value_pairs"
    parameters_value_pairs should be json string of parameters and values that the tool needs to do the job
    For example "filename": "test.txt", "content": "hello world"
    Be careful to always use double quotes for strings in the json string 
    """
    #return_direct= True

    def _run(self,title: str, parameters_value_pairs: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Use the tool."""
        try:
            #request toolman to start tool with the following parameters
            publish_to_manager(config.USER_ID,"START_TOOL",parameters={'toolname': title.lower()})
            #we must wait for the tool to report that it has started
            if isinstance(parameters_value_pairs, str):
                parameters_value_pairs = json.loads(parameters_value_pairs)

            if wait_for_tool(title.lower()):
                publish_to_tool(title.lower(), parameters_value_pairs)
                response = get_response(title.lower())
                return json.dumps(response, indent=2, sort_keys=True)
            return "Assistant did not respond"
            
        except Exception as e:
            traceback.print_exc()
            return f"""{e}"""
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("START_TOOL does not support async")

#callbacks
def get_manager_response(timeout_min=1):
    response_channel = config.USER_ID
    timeout = time.time() + 60*timeout_min   # 5 minutes from now
    while True:
        msg = consume(response_channel)
        if msg:
            return msg
        if time.time() > timeout:
            return "timeout"    
        time.sleep(0.5)

def get_response(toolname, timeout_min=1):
    response_channel = f"RES:{toolname.lower()}:{config.USER_ID}"
    timeout = time.time() + 60*timeout_min   # 5 minutes from now
    while True:
        msg = consume(response_channel)
        if msg:
            return msg
        if time.time() > timeout:
            return "timeout"    
        time.sleep(0.5)

def wait_for_tool(toolname):
    response_channel = f"RES:{toolname.lower()}:{config.USER_ID}"
    timeout = time.time() + 60*1   # 5 minutes from now
    while True:
        msg = consume(response_channel)
        if msg:
            state = msg.get('state')
            if state=='start':
                return True
        if time.time() > timeout:
            return False
        time.sleep(0.5)
    return False
        
#Consume tool manager messages
def consume(channel):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    tool_channel = connection.channel()
    tool_channel.queue_declare(queue=channel)
    method, properties, body = tool_channel.basic_get(queue=channel, auto_ack=True)
    tool_channel.close()
    if body:
        response = decode_message(body)
        return response
    else:
        return None

def decode_message(message):
    try:
        message = message.decode("utf-8")
        print(f"DECODING: {message}")
        message_dict = json.loads(message)

        message = message_dict.get('message')
        
        return message
    except Exception as e:
        traceback.print_exc()
        return "prompt", f"error: {e}", None

def publish_to_manager(bot_channel, command, parameters=None):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    message = encode_manager_message(bot_channel, command, parameters)

    publish_channel = connection.channel()
    publish_channel.basic_publish(exchange='',
                      routing_key=config.TOOL_CHANNEL,
                      body=message)
    #print(message)
    publish_channel.close()

def encode_manager_message(bot_channel, command, parameters=None):
    #actions = [action.__dict__ for action in actions] if actions else []
    response = {
        "bot_channel": bot_channel,
        "command": command,
        "parameters": parameters
    }
    print(f"BOT - ENCODING: {response}")
    return json.dumps(response)

def publish_to_tool(toolname, parameters):
    command_channel = f"CMD:{toolname.lower()}:{config.USER_ID}"
    response_queue = f"RES:{toolname.lower()}:{config.USER_ID}"

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    message = encode_tool_message(parameters)
    
    #Clean response channel of old messages
    response_channel = connection.channel()
    response_channel.queue_purge(response_queue)

    publish_channel = connection.channel()
    publish_channel.basic_publish(exchange='',
                      routing_key=command_channel,
                      body=message)
    #print(message)
    publish_channel.close()

def encode_tool_message(parameters):
    #actions = [action.__dict__ for action in actions] if actions else []
    response = {
        "parameters": parameters
    }
    print(f"BOT - ENCODING: {response}")
    return json.dumps(response)