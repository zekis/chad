
import traceback
from dotenv import find_dotenv, load_dotenv
from datetime import datetime
import os
from pathlib import Path
import json
import random
import requests
import subprocess

from typing import List
from botbuilder.core import ActivityHandler, CardFactory, TurnContext, MessageFactory, ShowTypingMiddleware
from botbuilder.core.teams import TeamsActivityHandler, TeamsInfo
from botbuilder.schema import CardAction, HeroCard, Mention, ConversationParameters, Attachment, Activity, ActivityTypes
from botbuilder.schema.teams import TeamInfo, TeamsChannelAccount
#from botbuilder.schema._connector_client_enums import ActionTypes
#from bots.model_openai import model_response
from botbuilder.core import BotFrameworkAdapter
import pika
from bots.utils import encode_message, decode_message

from typing import Dict

from botbuilder.schema import ChannelAccount, ConversationReference, CardAction, ActionTypes, SuggestedActions
from botbuilder.schema import (
    ActionTypes,
    CardImage,
    CardAction
)

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

CARDS = [
    "resources/LargeWeatherCard.json"
]

ADAPTIVECARDTEMPLATE = "resources/UserMentionCardTemplate.json"


class TeamsConversationBot(ActivityHandler):
    
    load_dotenv(find_dotenv())
    # We'll make a temporary directory to avoid clutter
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    message_channel = connection.channel()
    notify_channel = connection.channel()
    schedule_channel = connection.channel()

    message_channel.queue_declare(queue='message')
    notify_channel.queue_declare(queue='notify')
    schedule_channel.queue_declare(queue='schedule')

    process = None
    #ADAPTER = BotFrameworkAdapter

    def __init__(self, app_id: str, app_password: str, conversation_references: Dict[str, ConversationReference]):
        self.conversation_references = conversation_references
        self._app_id = app_id
        self._app_password = app_password
        #self.ADAPTER = ADAPTER
    
    async def on_turn(self, turn_context: TurnContext):
        if turn_context.activity.value:
            # Get the input value. This will be in turn_context.activity.value['acDecision'].
            selected_value = turn_context.activity.value['acDecision']
            # You can then use the selected value to trigger the imBack event.
            if selected_value:
                feedback = f"Please provide more information for {selected_value}"
                self.message_channel.basic_publish(exchange='',routing_key='message',body=feedback)
                print(selected_value)
        else:
            return await self.on_message_activity(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
        global process
        self._add_conversation_reference(turn_context.activity)
        #TurnContext.remove_recipient_mention(turn_context.activity)
        

        
        text = turn_context.activity.text
        if text:
            if text.lower() == "ping":
                #start the bot
                return await turn_context.send_activities([
                    Activity(
                        type=ActivityTypes.typing
                    ),
                    Activity(
                        type="delay",
                        value=3000
                    ),
                    Activity(
                        type=ActivityTypes.message,
                        text="pong"
                    )])
                """start the bot"""
                #self.publish(f"pong")
                #process = subprocess.Popen(['python', 'ai.py'])
                #return

            
                

            elif text.lower() == "start":
                #start the bot
                """start the bot"""
                self.publish(f"Starting bot...")
                process = subprocess.Popen(['python', 'ai.py'])
                
            elif text.lower() == "stop":
                #stop the bot
                """stop the bot"""
                self.publish(f"Stopping bot...")
                process.terminate()
                self.publish(f"Stopped")
                
            elif text.lower() == "restart":
                #stop the bot
                """stop the bot"""
                self.publish(f"Stopping bot...")
                process.terminate()
                self.publish(f"Stopped")
                self.publish(f"Starting bot...")
                process = subprocess.Popen(['python', 'ai.py'])
                
            else:
                message = random.choice(thinking_messages)
                response = self.message_channel.queue_declare('message', passive=True)
                # if response.method.message_count > 0:
                #     self.publish(f"Im already working on {response.method.message_count} messages")
                
                #self.notify_channel.basic_publish(exchange='',routing_key='notify',body=message)
                self.message_channel.basic_publish(exchange='',routing_key='message',body=text)
                print(text)

            return await turn_context.send_activities([
                    Activity(
                        type=ActivityTypes.typing
                    )])

    def _add_conversation_reference(self, activity: Activity):
        conversation_reference = TurnContext.get_conversation_reference(activity)
        self.conversation_references[
            conversation_reference.user.id
        ] = conversation_reference

    def init_bot(self, bot_name):
        current_date_time = datetime.now().date()
        self.publish("Hey Bro!")
        #self.message_channel.basic_publish(exchange='',routing_key='message',body=(f"Establish a personal connection with your human by asking for their name and using it in future interactions. This will help build trust and rapport between you and your human."))
        #self.message_channel.basic_publish(exchange='',routing_key='message',body=(f"As an AI, You are keen to learn things about me, my family, likes and dislikes, so ask a random question using the human tool and save the response to memory"))
        
        #self.message_channel.basic_publish(exchange='',routing_key='message',body="List the tasks in the AutoCHAD folder and use non task tools to action each one. Once complete mark the task as completed") 
        #self.message_channel.basic_publish(exchange='',routing_key='message',body="what is the weather in ellebrook?")
        #self.message_channel.basic_publish(exchange='',routing_key='message',body="what is the latest news for Perth WA?")

    def publish(self, message):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        notify_channel = connection.channel()
        notify_channel.queue_declare(queue='notify')
        message = encode_message("prompt", message)
        notify_channel.basic_publish(exchange='',routing_key='notify',body=message)


    async def process_message(self, ADAPTER):
        for conversation_reference in self.conversation_references.values():
            method, properties, body = self.notify_channel.basic_get(queue='notify',auto_ack=True)
            if body:
                #print(f"SERVER: {body}")
                type, body, data = decode_message(body)
                #decoded_body = body.decode("utf-8")
                decoded_body = body
                if type == "prompt":
                    if body == "bot1_online":
                        self.init_bot("AutoCHAD")
                    else:
                        await ADAPTER.continue_conversation(
                            conversation_reference,
                            lambda turn_context: turn_context.send_activity(MessageFactory.text(body)),
                            self._app_id,
                        )
                        print(decoded_body)
                    
                elif type == "action":
                    #actions = message_dict.get('actions')
                    actions = [CardAction(**action) for action in data] if data else []
                    message = Activity(
                        type=ActivityTypes.message,
                        attachments=[self.create_hero_card(body, actions)]
                        
                    )
                    ##teams_actions = self.get_actions(body, actions)
                    #conversation_reference = TurnContext.
                    await ADAPTER.continue_conversation(
                        conversation_reference,
                        lambda turn_context: turn_context.send_activity(message),
                        self._app_id,
                    )
                elif type == "cards":
                    #actions = message_dict.get('actions')
                    card_data = json.loads(data)
                    message = Activity(
                        type=ActivityTypes.message,
                        attachments=[CardFactory.adaptive_card(card_data)]
                        
                    )
                    ##teams_actions = self.get_actions(body, actions)
                    #conversation_reference = TurnContext.
                    await ADAPTER.continue_conversation(
                        conversation_reference,
                        lambda turn_context: turn_context.send_activity(message),
                        self._app_id,
                    )
    
    def create_hero_card(self, prompt, actions) -> Attachment:
        card = HeroCard(
            title="",
            text=prompt,
            buttons=actions
        )
        return CardFactory.hero_card(card)
                        

    def create_adaptive_card(self) -> Attachment:
        return CardFactory.adaptive_card(ADAPTIVE_CARD_CONTENT)