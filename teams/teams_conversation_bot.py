
import traceback
from dotenv import find_dotenv, load_dotenv
from datetime import datetime
import os
from pathlib import Path
import json
import random
import requests
import subprocess
import config
import pickle

from teams.elevenlabs import speech
from common.card_factories import create_media_card
from typing import List

from teams.bot_manager import BotManager

from botbuilder.core import ActivityHandler, CardFactory, TurnContext, MessageFactory, ShowTypingMiddleware, ConversationState, UserState
from botbuilder.core.teams import TeamsActivityHandler, TeamsInfo
from botbuilder.schema import Mention, ConversationParameters, Activity, ActivityTypes
from botbuilder.schema.teams import TeamInfo, TeamsChannelAccount
#from botbuilder.schema._connector_client_enums import ActionTypes
#from bots.model_openai import model_response
from botbuilder.core import BotFrameworkAdapter
import pika
#from bots.utils import encode_message, decode_message, encode_response, decode_response
from common.rabbit_comms import publish, publish_action, consume, send_to_bot, receive_from_bot

from typing import Dict

from botbuilder.schema import ChannelAccount, ConversationReference, CardAction, ActionTypes, SuggestedActions
from botbuilder.schema import (
    ActionTypes,
    Attachment,
    HeroCard,
    CardImage,
    CardAction,
    AdaptiveCardInvokeResponse,
    AdaptiveCardInvokeValue,
    InvokeResponse
)

from teams.data_models import TaskModuleResponseFactory, ConversationData, UserProfile

from botbuilder.schema.teams import (
    TaskModuleContinueResponse,
    TaskModuleRequest,
    TaskModuleMessageResponse,
    TaskModuleResponse,
    TaskModuleTaskInfo,
    MessagingExtensionResult
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


class TeamsConversationBot(TeamsActivityHandler):
    
    load_dotenv(find_dotenv())
    # We'll make a temporary directory to avoid clutter
    # connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    # message_channel = connection.channel()
    # notify_channel = connection.channel()
    # schedule_channel = connection.channel()

    # message_channel.queue_declare(queue='message')
    # notify_channel.queue_declare(queue='notify')
    # schedule_channel.queue_declare(queue='schedule')

    #user_processes = {}

    #ADAPTER = BotFrameworkAdapter

    def __init__(self, app_id: str, app_password: str, conversation_state: ConversationState, user_state: UserState, conversation_references: Dict[str, ConversationReference]):
        self.conversation_references = conversation_references
        # Load conversation references if file exists
        self.filename = "conversation_references.pkl"
        if os.path.exists(self.filename):
            with open(self.filename, "rb") as file:
                self.conversation_references = pickle.load(file)

        #this bot id and password matches the azure id configuration.
        self._app_id = app_id
        self._app_password = app_password
        #self.ADAPTER = ADAPTER
        self.__base_url = config.BASE_URL
        self.bot_manager = BotManager()

        if conversation_state is None:
            raise TypeError(
                "[StateManagementBot]: Missing parameter. conversation_state is required but None was given"
            )
        if user_state is None:
            raise TypeError(
                "[StateManagementBot]: Missing parameter. user_state is required but None was given"
            )

        self.conversation_state = conversation_state
        self.user_state = user_state

        self.conversation_data_accessor = self.conversation_state.create_property("ConversationData")
        self.user_profile_accessor = self.user_state.create_property("UserProfile")


   
    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)

        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
        #When a member sends activity, if they are not recipient, send welcome
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    "Welcome. Type anything to get started."
                )
    async def _show_members(
        self, turn_context: TurnContext
    ):
        # Get a conversationMember from a team.
        members = await TeamsInfo.get_team_members(turn_context)
    
    

        
    async def on_message_activity(self, turn_context: TurnContext):
        #global process
        # Get the state properties from the turn context.
        user_profile = await self.user_profile_accessor.get(turn_context, UserProfile)
        conversation_data = await self.conversation_data_accessor.get(turn_context, ConversationData)
        self._add_conversation_reference(turn_context.activity)

        value = turn_context.activity.value
        text = turn_context.activity.text
        
        conversation_reference = TurnContext.get_conversation_reference(turn_context.activity)
        user_id = conversation_reference.user.id

        print(f"Message - User ID: {user_id}")
        if value:
            print(f"Got Activity: {turn_context.activity}")
            # Get the input value. This will be in turn_context.activity.value['acDecision'].
            selected_value = turn_context.activity.value.get('acDecision', None)
            suggestions_value = turn_context.activity.value.get('suggestions', None)
            create_tts = turn_context.activity.value.get('create_tts', None)
            # You can then use the selected value to trigger the imBack event.
            if selected_value:
                
                if suggestions_value:
                    print(selected_value)
                    print(suggestions_value)
                    feedback = f"user_improvements: {suggestions_value}, {selected_value}"
                    send_to_bot(user_id, feedback)
                else:
                    print(selected_value)
                    feedback = f"{selected_value}"
                    send_to_bot(user_id, feedback)

                return await turn_context.send_activities([
                        Activity(
                            type=ActivityTypes.typing
                        )])
            if create_tts:
                reply = Activity(type=ActivityTypes.message)
                reply.text = "This is an internet attachment."
                reply.attachments = [self._get_internet_attachment()]
                return await turn_context.send_activity(reply)
        if text:
            if text.lower() == "ping":
                #Channel Test
                await turn_context.send_activities([
                    Activity(
                        type=ActivityTypes.typing
                    ),
                    Activity(
                        type="delay",
                        value=3000
                    )])
                publish(f"pong", user_id)

            elif text.lower() == "bot_start":
                self.bot_manager.handle_command("start", user_id)
                
            elif text.lower() == "bot_stop":
                self.bot_manager.handle_command("stop", user_id)
                
            elif text.lower() == "bot_restart":
                self.bot_manager.handle_command("restart", user_id)

            elif text.lower() == "list_bots":
                self.bot_manager.handle_command("list_bots", user_id)
                
            elif text.lower() == "stop_bots":
                self.bot_manager.handle_command("stop_bots", user_id)
                
            else:
                message = random.choice(thinking_messages)
                #response = self.message_channel.queue_declare('message', passive=True)
                # if response.method.message_count > 0:
                #     self.publish(f"Im already working on {response.method.message_count} messages")
                
                #self.notify_channel.basic_publish(exchange='',routing_key='notify',body=message)
                #self.message_channel.basic_publish(exchange='',routing_key='message',body=text)
                send_to_bot(user_id, text)
                print(text)

                return await turn_context.send_activities([
                        Activity(
                            type=ActivityTypes.typing
                        )])

    def _add_conversation_reference(self, activity: Activity):
        conversation_reference = TurnContext.get_conversation_reference(activity)
        self.conversation_references[conversation_reference.user.id] = conversation_reference
        # Save conversation references to disk
        with open(self.filename, "wb") as file:
            pickle.dump(self.conversation_references, file)

    def init_bot(self,user_id, bot_name):
        current_date_time = datetime.now().date()
        publish("Hey Bro!", user_id)
        #put more init functions here like checking settings etc

    # #Publish to the user
    # def publish(self, user_id, prompt):
    #     connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    #     notify_channel = connection.channel()
    #     notify_channel.queue_declare(queue='notify')
    #     message = encode_message(user_id, "prompt", prompt)
    #     notify_channel.basic_publish(exchange='',routing_key='notify',body=message)

    


    async def process_message(self, ADAPTER):
        #conversation_references are populated with every message recieved. It uniquly identifies the sender.
        #for conversation_reference in self.conversation_references.values():
        #print('Processing')
        
        # connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        # notify_channel = connection.channel()
        # method, properties, body = self.notify_channel.basic_get(queue='notify',auto_ack=True)
        user_id, type, body, data = receive_from_bot()

        if body:
            
            #user_id, type, body, data = decode_message(body)
            print(f"SERVER: user_id: {user_id}, type: {type}, body: {body}")

            conversation_reference = self.conversation_references.get(user_id, None)
            if conversation_reference is None:
                # Handle the case when the conversation reference is not found
                print(f"Conversation reference not found for user ID: {user_id}")
                return
            #decoded_body = body.decode("utf-8")
            decoded_body = body
            if type == "prompt":
                if body == "bot1_online":
                    self.init_bot(user_id, "AutoCHAD")
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
                if data:
                    card_data = json.loads(data)
                    print(f"CARD: {card_data}")
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
                        

    # def create_adaptive_card(self) -> Attachment:
    #     return CardFactory.adaptive_card(ADAPTIVE_CARD_CONTENT)


    def _get_internet_attachment(self) -> Attachment:
        """
        Creates an Attachment to be sent from the bot to the user from a HTTP URL.
        :return: Attachment
        """
        return Attachment(
            name="architecture-resize.mpeg",
            content_type="application/octet-stream",
            content_url="https://chatbot.tierneymorris.com.au/media.mpeg",
        )