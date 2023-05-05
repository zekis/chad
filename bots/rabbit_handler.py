from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from typing import Any, Dict, List, Optional, Union
from langchain.input import print_text
from langchain.schema import AgentAction, AgentFinish, LLMResult
import pika
import re


class RabbitHandler(BaseCallbackHandler):

    message_channel = pika.BlockingConnection()


    def __init__(self, message_channel, color: Optional[str] = None, ) -> None:
        """Initialize callback handler."""
        self.message_channel = message_channel
        self.color = color

    # def on_tool_end(
    #     self,
    #     output: str,
    #     color: Optional[str] = None,
    #     observation_prefix: Optional[str] = None,
    #     llm_prefix: Optional[str] = None,
    #     **kwargs: Any,
    # ) -> None:
    #     """If not the final action, print out observation."""
    #     if observation_prefix is not None:
    #         print_text(f"\n{observation_prefix}")
    #         self.message_channel.basic_publish(exchange='',routing_key='notify',body=output)
    #     print_text(output, color=color if color else self.color)
    #     if llm_prefix is not None:
    #         print_text(f"\n{llm_prefix}")

    # def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
    #     print(outputs)
    #     self.message_channel.basic_publish(exchange='',routing_key='notify',body=outputs)
    #     """Run when chain ends running."""
    
    def on_agent_action(
        self, action: AgentAction, color: Optional[str] = None, **kwargs: Any
    ) -> Any:

        thought_pattern = r'Thought: (.*)'
        match = re.search(thought_pattern, action.log)
        if match:
            thought = match.group(1)
            #print("Thought:", thought)
            #"""Run on agent action."""
            self.message_channel.basic_publish(exchange='',routing_key='notify',body=thought)
            #print_text(action.log, color=color if color else self.color)