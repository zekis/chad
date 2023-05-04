# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from dotenv import find_dotenv, load_dotenv
import os
from pathlib import Path
import json
import random
import requests

from typing import List
from botbuilder.core import CardFactory, TurnContext, MessageFactory
from botbuilder.core.teams import TeamsActivityHandler, TeamsInfo
from botbuilder.schema import CardAction, HeroCard, Mention, ConversationParameters, Attachment, Activity
from botbuilder.schema.teams import TeamInfo, TeamsChannelAccount
from botbuilder.schema._connector_client_enums import ActionTypes
#from bots.model_openai import model_response
#rabbitmq
import pika

from typing import Dict

from botbuilder.schema import ChannelAccount, ConversationReference, Activity


thinking_messages = [
    "Just a moment...",
    "Let me check on that...",
    "Hang on a sec...",
    "Give me a second...",
    "Thinking...",
    "One moment, please...",
    "Hold on...",
    "Let me see...",
    "Processing your request...",
    "Let me think for a bit...",
    "Let me get that for you...",
    "Bear with me...",
    "Almost there...",
    "Wait a moment...",
    "Checking...",
    "Calculating...",
    "Give me a moment to think...",
    "I'm on it...",
    "Searching for the answer...",
    "I need a second...",
]

ADAPTIVECARDTEMPLATE = "resources/UserMentionCardTemplate.json"

class TeamsConversationBot(TeamsActivityHandler):
    
    load_dotenv(find_dotenv())
    # We'll make a temporary directory to avoid clutter
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    message_channel = connection.channel()
    notify_channel = connection.channel()

    message_channel.queue_declare(queue='message')
    notify_channel.queue_declare(queue='notify')

    def __init__(self, app_id: str, app_password: str, conversation_references: Dict[str, ConversationReference]):
        self.conversation_references = conversation_references
        self._app_id = app_id
        self._app_password = app_password
        

    async def on_message_activity(self, turn_context: TurnContext):
        self._add_conversation_reference(turn_context.activity)
        #TurnContext.remove_recipient_mention(turn_context.activity)
        text = turn_context.activity.text.strip().lower()

        message = random.choice(thinking_messages)
        self.message_channel.basic_publish(exchange='',routing_key='notify',body=message)

        self.message_channel.basic_publish(exchange='',routing_key='message',body=text)

        print(text)

        return

    def _add_conversation_reference(self, activity: Activity):
        conversation_reference = TurnContext.get_conversation_reference(activity)
        self.conversation_references[
            conversation_reference.user.id
        ] = conversation_reference


    async def process_message(self, ADAPTER):
        method, properties, body = self.notify_channel.basic_get(queue='notify')
        if body:
            for conversation_reference in self.conversation_references.values():
                await ADAPTER.continue_conversation(
                    conversation_reference,
                    lambda turn_context: turn_context.send_activity(body.decode("utf-8")),
                    self._app_id,
                )
                print(body)