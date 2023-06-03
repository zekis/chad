
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
from teams.elevenlabs import speech
from teams.card_factories import create_media_card
from typing import List
from botbuilder.core import ActivityHandler, CardFactory, TurnContext, MessageFactory, ShowTypingMiddleware
from botbuilder.core.teams import TeamsActivityHandler, TeamsInfo
from botbuilder.schema import Mention, ConversationParameters, Activity, ActivityTypes
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
    Attachment,
    HeroCard,
    CardImage,
    CardAction,
    AdaptiveCardInvokeResponse,
    AdaptiveCardInvokeValue,
    InvokeResponse
)

from teams.task_module_response_factory import TaskModuleResponseFactory

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
        self.__base_url = config.BASE_URL

    #async def on_teams_task_module_fetch(self, turn_context: TurnContext, task_module_request: TaskModuleRequest) -> TaskModuleResponse:

        # card_task_fetch_value = task_module_request.data.get("create_tts", None)
        # print(card_task_fetch_value)

        # url = config.BASE_URL + "/tts.html"

        # card = HeroCard(
        #     text="This is a task module card",
        #     buttons=[
        #             CardAction(
        #                 type=ActionTypes.open_url,
        #                 title="Go to URL",
        #                 value=url,
        #             )
        #         ],
        #     )

        # task_info = TaskModuleTaskInfo(
        #     title="Task",
        #     card=Attachment(content_type='application/vnd.microsoft.card.hero', content=card)
        # )

        # continue_response = TaskModuleContinueResponse(value=task_info)
        # return TaskModuleResponse(task=continue_response)
        # if card_task_fetch_value:
        #     print(card_task_fetch_value)
        #     """Create some audio using ElevenLabs"""
        #     #speech("media.mpeg", card_task_fetch_value)            
        #     task_info.url = task_info.fallback_url = url
        #     task_info.height = 1000
        #     task_info.width = 700
        #     task_info.title = "TTS"

        #     continue_response = TaskModuleContinueResponse(value=task_info)

            
        



    # async def on_turn(self, turn_context: TurnContext):
    #     print("sHELLO")
    #     if turn_context.activity.value:
    #         print(f"Got Activity: {turn_context.activity}")
    #         # Get the input value. This will be in turn_context.activity.value['acDecision'].
    #         selected_value = turn_context.activity.value.get('acDecision', None)
    #         suggestions_value = turn_context.activity.value.get('suggestions', None)
            
    #         # You can then use the selected value to trigger the imBack event.
    #         if selected_value:
                
    #             if suggestions_value:
    #                 print(selected_value)
    #                 print(suggestions_value)
    #                 feedback = f"user_improvements: {suggestions_value}, {selected_value}"
    #                 self.send(feedback)
    #             else:
    #                 print(selected_value)
    #                 feedback = f"{selected_value}"
    #                 self.send(feedback)

    #         data = turn_context.activity.value.get('data', None)
    #         if data:
    #             create_tts = data.get('create_tts', None)
    #             """Create some audio using ElevenLabs"""
    #             #speech("media.mpeg", create_tts)
    #             task_info = TaskModuleTaskInfo()
    #             task_info.url = task_info.fallback_url = (config.BASE_URL + "/tts.html")

    #             return TaskModuleResponse(task=TaskModuleMessageResponse(value=task_info))

    #     await super().on_turn(TurnContext)

    #     #     return await turn_context.send_activities([
    #     #             Activity(
    #     #                 type=ActivityTypes.typing
    #     #             )])
    #     # else:
    #     #     print(f"No Activity: {turn_context.activity}")
    #     #     return await self.on_message_activity(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
        global process
        self._add_conversation_reference(turn_context.activity)
        #TurnContext.remove_recipient_mention(turn_context.activity)
        #print(turn_context.activity.value)
        value = turn_context.activity.value
        text = turn_context.activity.text

        if value:
            print(f"Got Activity: {turn_context.activity}")
            # Get the input value. This will be in turn_context.activity.value['acDecision'].
            selected_value = turn_context.activity.value.get('acDecision', None)
            suggestions_value = turn_context.activity.value.get('suggestions', None)
            
            # You can then use the selected value to trigger the imBack event.
            if selected_value:
                
                if suggestions_value:
                    print(selected_value)
                    print(suggestions_value)
                    feedback = f"user_improvements: {suggestions_value}, {selected_value}"
                    self.send(feedback)
                else:
                    print(selected_value)
                    feedback = f"{selected_value}"
                    self.send(feedback)

                return await turn_context.send_activities([
                        Activity(
                            type=ActivityTypes.typing
                        )])
        
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

    def send(self, message):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        message_channel = connection.channel()
        message_channel.queue_declare(queue='notify')
        message = encode_message("prompt", message)
        message_channel.basic_publish(exchange='',routing_key='message',body=message)


    async def process_message(self, ADAPTER):
        for conversation_reference in self.conversation_references.values():
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            notify_channel = connection.channel()
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


        