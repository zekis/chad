import traceback
import config

import json
import os
import re
import pickle
from typing import Optional
from common.rabbit_comms import publish_input_card
from common.utils import tool_description, tool_error

from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain.tools import BaseTool


class Credential:
    def __init__(self, name, parameters):
        self.name = name
        self.parameters = parameters
        
    def to_dict_with_parameters(self):
        return {
            'name': self.name,
            'parameters': self.parameters
        }

    def to_dict(self):
        return {
            'name': self.name
        }

class CredentialManager:
    def __init__(self, data_dir, user_dir):
        self.credentials = []
        self.data_dir = data_dir
        self.user_dir = user_dir

        folder_path = f"{data_dir}/{user_dir}"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    
    def add_credential(self, name, parameters):
        for credential in self.credentials:
            if credential.name == name:
                return f"A credential with the name '{name}' already exists."
        self.credentials.append(Credential(name, parameters))
        return f"Credential Added"

    def get_credential(self, name):
        for credential in self.credentials:
            if credential.name == name:
                return json.dumps(credential.to_dict_with_parameters())
        return False

    def delete_credential(self, name):
        for credential in self.credentials:
            if credential.name == name:
                self.credentials.remove(credential)
                return "Credential Deleted"
            

    def save_credentials(self):
        file_path = f"{self.data_dir}/{self.user_dir}/credential_registry.pkl"
        with open(file_path, 'wb') as f:
            pickle.dump(self.credentials, f)

    def load_credentials(self):
        file_path = f"{self.data_dir}/{self.user_dir}/credential_registry.pkl"
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                self.credentials = pickle.load(f)
        #self.cleanup()
        

    def to_json(self):
        if not self.credentials:
            return "No credentials Loaded, Use the ADD_CREDENTIAL tool to commission a new credential"
        else:
            return json.dumps([credential.to_dict() for credential in self.credentials])

class GetCredentials(BaseTool):
    parameters = []
    optional_parameters = []
    name = "GET_CREDENTIALS"
    summary = """useful for when you want to retrieve a list of availabe credentials or memories. """
    
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, publish: str = "False", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            
            credentialManager = CredentialManager(config.DATA_DIR, config.USER_ID)
            credentialManager.load_credentials()
            
            if publish.lower() == "true":
                publish(credentialManager.to_json())
                return config.PROMPT_PUBLISH_TRUE
            return credentialManager.to_json()
            
        except Exception as e:
            traceback.print_exc()
            return tool_error(e, self.description)
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GET_CREDENTIALS does not support async")

class GetCredential(BaseTool):
    parameters = []
    optional_parameters = []
    name = "GET_CREDENTIAL"
    summary = """useful for when you want to retrieve the parameters for a credential or stored memory."""
    parameters.append({"name": "name", "description": "credential or memory name" })
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, name: str, publish: str = "True", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            
            credentialManager = CredentialManager(config.DATA_DIR, config.USER_ID)
            credentialManager.load_credentials()
            parameters = credentialManager.get_credential(name)
            
            if parameters:
                if publish.lower() == "true":
                    publish(parameters)
                    return config.PROMPT_PUBLISH_TRUE
                else:
                    return parameters
            else:
                raise f"Credential {name} does not exist"
            
            
        except Exception as e:
            traceback.print_exc()
            return tool_error(e, self.description)
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GET_CREDENTIAL does not support async")

class CreateCredential(BaseTool):
    parameters = []
    optional_parameters = []
    name = "CREATE_CREDENTIAL"
    summary = """useful for when you want to create a new credential."""
    parameters.append({"name": "name", "description": "credential or memory name" })
    parameters.append({"name": "parameters_value_pairs", "description": "should be json string of parameters and values" })
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, name: str, parameters_value_pairs: str, publish: str = "True", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            
            credentialManager = CredentialManager(config.DATA_DIR, config.USER_ID)
            credentialManager.load_credentials()
            response = credentialManager.add_credential(name, parameters_value_pairs)
            credentialManager.save_credentials()
            if publish.lower() == "true":
                publish(response)
                return config.PROMPT_PUBLISH_TRUE
            else:
                return response
            
        except Exception as e:
            traceback.print_exc()
            return tool_error(e, self.description)
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("CREATE_CREDENTIAL does not support async")

class RequestCredential(BaseTool):
    parameters = []
    optional_parameters = []
    name = "REQUEST_CREDENTIAL"
    summary = """useful for when you want to request credential or memory values from the human"""
    parameters.append({"name": "name", "description": "credential or memory name" })
    parameters.append({"name": "parameters", "description": "parameter name" })
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, name: str, parameters: str, publish: str = "True", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            #Send a request Card to the users
            publish_input_card(name, parameters)
            return "this tool is not finished yet"
            
            
            
        except Exception as e:
            traceback.print_exc()
            return tool_error(e, self.description)
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("CREATE_CREDENTIAL does not support async")

class DeleteCredential(BaseTool):
    parameters = []
    optional_parameters = []
    name = "DELETE_CREDENTIAL"
    summary = """useful for when you want to delete an existing credential."""
    parameters.append({"name": "name", "description": "credential or memory name" })
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, name: str, publish: str = "True", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            
            credentialManager = CredentialManager(config.DATA_DIR, config.USER_ID)
            credentialManager.load_credentials()
            response = credentialManager.delete_credential(name)
            credentialManager.save_credentials()
            if publish.lower() == "true":
                publish(response)
                return config.PROMPT_PUBLISH_TRUE
            else:
                return response
            
        except Exception as e:
            traceback.print_exc()
            return tool_error(e, self.description)
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("DELETE_CREDENTIAL does not support async")

class UpdateCredential(BaseTool):
    parameters = []
    optional_parameters = []
    name = "UPDATE_CREDENTIAL"
    summary = """useful for when you want to update an existing credential or memory."""
    parameters.append({"name": "name", "description": "credential or memory name" })
    parameters.append({"name": "parameters_value_pairs", "description": "should be json string of parameters and values" })
    description = tool_description(name, summary, parameters, optional_parameters)
    return_direct = False

    def _run(self, name: str, parameters_value_pairs: str, publish: str = "True", run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            
            credentialManager = CredentialManager(config.DATA_DIR, config.USER_ID)
            credentialManager.load_credentials()
            credentialManager.delete_credential(name)
            response = credentialManager.add_credential(name, parameters_value_pairs)
            credentialManager.save_credentials()
            if publish.lower() == "true":
                publish(response)
                return config.PROMPT_PUBLISH_TRUE
            else:
                return response
            
        except Exception as e:
            traceback.print_exc()
            return tool_error(e, self.description)
        

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("UPDATE_CREDENTIAL does not support async")