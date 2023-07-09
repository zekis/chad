from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from langchain.input import print_text
from langchain.schema import AgentAction, AgentFinish, LLMResult
from common.utils import generate_table
# import pika
import re
#import config
#from bots.utils import encode_message, decode_message
from common.rabbit_comms import publish, publish_action, consume

class RabbitHandler(BaseCallbackHandler):

    #message_channel = pika.BlockingConnection()


    def __init__(self, color: Optional[str] = None, ) -> None:
        """Initialize callback handler."""
        #self.message_channel = message_channel
        #self.color = color
    # def on_llm_start(
    #     self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    # ) -> Any:
    #     print(f"prompts: {prompts}")

    # def on_agent_action(
    #     self, action: AgentAction, color: Optional[str] = None, **kwargs: Any
    # ) -> Any:
    #     #print(f"On Agent Action: {action.log}")
    #     thought_pattern = r'Thought: (.*)'
    #     match = re.search(thought_pattern, action.log)
    #     if match:
    #         message = match.group(1)
    #         #print("Thought:", thought)
    #         #"""Run on agent action."""
    #         #message = encode_message(config.USER_ID,'prompt', message)
    #         #self.message_channel.basic_publish(exchange='',routing_key='notify',body=message)
    #         publish(f"Thought: {message}")
    #         #print_text(action.log, color=color if color else self.color)
    #     observation_pattern = r'Observation: (.*)'
    #     obs_match = re.search(observation_pattern, action.log)
    #     if obs_match:
    #         observation = obs_match.group(1)
    #         #print("Thought:", thought)
    #         #"""Run on agent action."""
    #         #message = encode_message(config.USER_ID,'prompt', observation)
    #         #self.message_channel.basic_publish(exchange='',routing_key='notify',body=message)
    #         publish(f"Observation: {message}")
    #         #print_text(action.log, color=color if color else self.color)
    

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run when tool ends running."""
        #table = generate_table(output)
        #publish(f"{table}")

    def on_tool_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when tool errors."""
        print(error)
        return str(error)

    def on_agent_finish(
        self,
        finish: AgentFinish,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        #print(f"on_agent_finish Callback {finish.return_values}")
        #print(f"on_agent_finish Callback {finish.log}")
        message = finish
        if message:
            #message = encode_message(config.USER_ID,'on_agent_finish', message)
            #self.message_channel.basic_publish(exchange='',routing_key='notify',body=message)
            print(f"Agent Finish: {message}")

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        #print(f"on_chain_end Callback {outputs}")
        #message = outputs.get("output")
        message = outputs
        text = message.get("text")
        if text:
            #message = encode_message(config.USER_ID,'prompt', message)
            #self.message_channel.basic_publish(exchange='',routing_key='notify',body=message)
            #text = text[:text.find('\n')] if '\n' in text else text
            # action_pattern = r'Action: (.*)'
            # act_match = re.search(action_pattern, text)

            # print(f"act_match: {act_match}")

            # if act_match:
            #     action_json = act_match.group(1)
            #     print(action_json)
            #     if action_json:
            #         action_json = json.loads(action_json)
            #         action = action_json.get("action")
            #         action_input = action_json.get("action_input")
            #         #if action != "Final Answer":
            #         publish(f"{action} {action_input}")
                #print("Thought:", thought)
                #"""Run on agent action."""
                #message = encode_message(config.USER_ID,'prompt', observation)
                #self.message_channel.basic_publish(exchange='',routing_key='notify',body=message)
                #publish(f"Observation: {message}")
                #print_text(action.log, color=color if color else self.color)

            publish(f"{text}")

    def on_chain_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when chain errors."""
        if error:
            #message = encode_message(config.USER_ID,'prompt', message)
            #self.message_channel.basic_publish(exchange='',routing_key='notify',body=message)
            print(f"Error: {error}")
            return str(error)