from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
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

    def on_agent_action(
        self, action: AgentAction, color: Optional[str] = None, **kwargs: Any
    ) -> Any:
        print(f"Callback {action.log}")
        thought_pattern = r'Thought: (.*)'
        match = re.search(thought_pattern, action.log)
        if match:
            thought = match.group(1)
            #print("Thought:", thought)
            #"""Run on agent action."""
            self.message_channel.basic_publish(exchange='',routing_key='notify',body=thought)
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
            self.message_channel.basic_publish(exchange='',routing_key='notify',body=finish.return_values)

    # def on_llm_start(
    #     self,
    #     serialized: Dict[str, Any],
    #     prompts: List[str],
    #     *,
    #     run_id: UUID,
    #     parent_run_id: Optional[UUID] = None,
    #     **kwargs: Any,
    # ) -> Any:
    #     print(f"on_llm_start Callback {prompts}")


    # def on_chain_start(
    #     self,
    #     serialized: Dict[str, Any],
    #     inputs: Dict[str, Any],
    #     *,
    #     run_id: UUID,
    #     parent_run_id: Optional[UUID] = None,
    #     **kwargs: Any,
    # ) -> Any:
    #     #print(f"on_chain_start Callback {inputs}")
    #     self.message_channel.basic_publish(exchange='',routing_key='notify',body=inputs["objective"])
        

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        #print(f"on_chain_end Callback {outputs}")
        message = outputs["output"]
        if message:
            self.message_channel.basic_publish(exchange='',routing_key='notify',body=message)

    # def on_tool_start(
    #     self,
    #     serialized: Dict[str, Any],
    #     input_str: str,
    #     *,
    #     run_id: UUID,
    #     parent_run_id: Optional[UUID] = None,
    #     **kwargs: Any,
    # ) -> Any:
    #     print(f"on_tool_start Callback {input_str}")

    # def on_tool_end(
    #     self,
    #     output: str,
    #     *,
    #     run_id: UUID,
    #     parent_run_id: Optional[UUID] = None,
    #     **kwargs: Any,
    # ) -> Any:
    #     print(f"on_tool_end Callback {output}")

    # def on_text(
    #     self,
    #     text: str,
    #     *,
    #     run_id: UUID,
    #     parent_run_id: Optional[UUID] = None,
    #     **kwargs: Any,
    # ) -> Any:
    #     print(f"on_text Callback {text}")