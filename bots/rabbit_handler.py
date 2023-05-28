from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from langchain.input import print_text
from langchain.schema import AgentAction, AgentFinish, LLMResult
import pika
import re
from bots.utils import encode_message, decode_message

class RabbitHandler(BaseCallbackHandler):

    message_channel = pika.BlockingConnection()


    def __init__(self, message_channel, color: Optional[str] = None, ) -> None:
        """Initialize callback handler."""
        self.message_channel = message_channel
        self.color = color

    def on_agent_action(
        self, action: AgentAction, color: Optional[str] = None, **kwargs: Any
    ) -> Any:
        #print(f"Callback {action.log}")
        thought_pattern = r'Thought: (.*)'
        match = re.search(thought_pattern, action.log)
        if match:
            message = match.group(1)
            #print("Thought:", thought)
            #"""Run on agent action."""
            message = encode_message('prompt', message)
            self.message_channel.basic_publish(exchange='',routing_key='notify',body=message)
            #print_text(action.log, color=color if color else self.color)
        observation_pattern = r'Observation: (.*)'
        obs_match = re.search(observation_pattern, action.log)
        if obs_match:
            observation = obs_match.group(1)
            #print("Thought:", thought)
            #"""Run on agent action."""
            message = encode_message('prompt', observation)
            self.message_channel.basic_publish(exchange='',routing_key='notify',body=message)
            #print_text(action.log, color=color if color else self.color)
    
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
        message = finish.return_values
        if message:
            message = encode_message('on_agent_finish', message)
            self.message_channel.basic_publish(exchange='',routing_key='notify',body=message)

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        #print(f"on_chain_end Callback {outputs}")
        message = outputs.get("output")
        if message:
            message = encode_message('prompt', message)
            self.message_channel.basic_publish(exchange='',routing_key='notify',body=message)

