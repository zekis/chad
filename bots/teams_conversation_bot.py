# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from dotenv import find_dotenv, load_dotenv
import os
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

from typing import Dict


from botbuilder.schema import ChannelAccount, ConversationReference, Activity


from langchain.agents import load_tools
from langchain.agents import ZeroShotAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain import OpenAI, LLMChain
from langchain.llms import OpenAI
from langchain.agents import tool


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
    llm = OpenAI(temperature=0)

    tools = load_tools(["human","wikipedia", "google-search", "llm-math", "requests"], llm=llm)
    # Assuming the "human" tool is the first one in the list
    # Set the custom prompt and input functions
    

    prefix = """Have a conversation with a human, answering the following questions as best you can. You have access to the following tools:"""
    suffix = """and the windows terminal. Begin!"

    {chat_history}
    Question: {input}
    {agent_scratchpad}"""

    prompt = ZeroShotAgent.create_prompt(
        tools, 
        prefix=prefix, 
        suffix=suffix, 
        input_variables=["input", "chat_history", "agent_scratchpad"]
    )
    memory = ConversationBufferMemory(memory_key="chat_history")

    llm_chain = LLMChain(llm=OpenAI(temperature=0), prompt=prompt)
    agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True)
    agent_chain = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory) 
    


    def __init__(self, app_id: str, app_password: str, conversation_references: Dict[str, ConversationReference]):
        self._app_id = app_id
        self._app_password = app_password
        self.conversation_references = conversation_references

        self.tools[0].prompt_func = self.custom_prompt_func
        self.tools[0].input_func = self.custom_input_func

       

    async def on_conversation_update_activity(self, turn_context: TurnContext):
        self._add_conversation_reference(turn_context.activity)
        return await super().on_conversation_update_activity(turn_context)

    async def on_teams_members_added(  # pylint: disable=unused-argument
        self,
        teams_members_added: TeamsChannelAccount,
        team_info: TeamInfo,
        turn_context: TurnContext,
    ):
        for member in teams_members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    f"Welcome to the team { member.given_name } { member.surname }. "
                )

    async def on_message_activity(self, turn_context: TurnContext):
        self._add_conversation_reference(turn_context.activity)
        TurnContext.remove_recipient_mention(turn_context.activity)
        text = turn_context.activity.text.strip().lower()

        message = random.choice(thinking_messages)
        await turn_context.send_activity(message)

        response = self.model_response(text)
        await turn_context.send_activity(response)
        #await self._send_card(response, False)
        return

    async def _mention_adaptive_card_activity(self, turn_context: TurnContext):
        TeamsChannelAccount: member = None
        try:
            member = await TeamsInfo.get_member(
                turn_context, turn_context.activity.from_property.id
            )
        except Exception as e:
            if "MemberNotFoundInConversation" in e.args[0]:
                await turn_context.send_activity("Member not found.")
                return
            else:
                raise

        card_path = os.path.join(os.getcwd(), ADAPTIVECARDTEMPLATE)
        with open(card_path, "rb") as in_file:
            template_json = json.load(in_file)
        
        for t in template_json["body"]:
            t["text"] = t["text"].replace("${userName}", member.name)        
        for e in template_json["msteams"]["entities"]:
            e["text"] = e["text"].replace("${userName}", member.name)
            e["mentioned"]["id"] = e["mentioned"]["id"].replace("${userUPN}", member.user_principal_name)
            e["mentioned"]["id"] = e["mentioned"]["id"].replace("${userAAD}", member.additional_properties["aadObjectId"])
            e["mentioned"]["name"] = e["mentioned"]["name"].replace("${userName}", member.name)
        
        adaptive_card_attachment = Activity(
            attachments=[CardFactory.adaptive_card(template_json)]
        )
        await turn_context.send_activity(adaptive_card_attachment)

    async def _mention_activity(self, turn_context: TurnContext):
        mention = Mention(
            mentioned=turn_context.activity.from_property,
            text=f"<at>{turn_context.activity.from_property.name}</at>",
            type="mention",
        )

        reply_activity = MessageFactory.text(f"Hello {mention.text}")
        reply_activity.entities = [Mention().deserialize(mention.serialize())]
        await turn_context.send_activity(reply_activity)

    async def _send_card(self, turn_context: TurnContext, isUpdate):
        buttons = [
            CardAction(
                type=ActionTypes.message_back,
                title="Message all members",
                text="messageallmembers",
            ),
            CardAction(type=ActionTypes.message_back, title="Who am I?", text="whoami"),
            CardAction(type=ActionTypes.message_back, title="Find me in Adaptive Card", text="mention me"),
            CardAction(
                type=ActionTypes.message_back, title="Delete card", text="deletecard"
            ),
        ]
        if isUpdate:
            await self._send_update_card(turn_context, buttons)
        else:
            await self._send_welcome_card(turn_context, buttons)

    async def _send_welcome_card(self, turn_context: TurnContext, buttons):
        buttons.append(
            CardAction(
                type=ActionTypes.message_back,
                title="Update Card",
                text="updatecardaction",
                value={"count": 0},
            )
        )
        card = HeroCard(
            title="Welcome Card", text="Click the buttons.", buttons=buttons
        )
        await turn_context.send_activity(
            MessageFactory.attachment(CardFactory.hero_card(card))
        )

    async def _send_update_card(self, turn_context: TurnContext, buttons):
        data = turn_context.activity.value
        data["count"] += 1
        buttons.append(
            CardAction(
                type=ActionTypes.message_back,
                title="Update Card",
                text="updatecardaction",
                value=data,
            )
        )
        card = HeroCard(
            title="Updated card", text=f"Update count {data['count']}", buttons=buttons
        )

        updated_activity = MessageFactory.attachment(CardFactory.hero_card(card))
        updated_activity.id = turn_context.activity.reply_to_id
        await turn_context.update_activity(updated_activity)

    async def _get_member(self, turn_context: TurnContext):
        TeamsChannelAccount: member = None
        try:
            member = await TeamsInfo.get_member(
                turn_context, turn_context.activity.from_property.id
            )
        except Exception as e:
            if "MemberNotFoundInConversation" in e.args[0]:
                await turn_context.send_activity("Member not found.")
            else:
                raise
        else:
            await turn_context.send_activity(f"You are: {member.name}")

    async def _message_all_members(self, turn_context: TurnContext):
        team_members = await self._get_paged_members(turn_context)

        for member in team_members:
            conversation_reference = TurnContext.get_conversation_reference(
                turn_context.activity
            )

            conversation_parameters = ConversationParameters(
                is_group=False,
                bot=turn_context.activity.recipient,
                members=[member],
                tenant_id=turn_context.activity.conversation.tenant_id,
            )

            async def get_ref(tc1):
                conversation_reference_inner = TurnContext.get_conversation_reference(
                    tc1.activity
                )
                return await tc1.adapter.continue_conversation(
                    conversation_reference_inner, send_message, self._app_id
                )

            async def send_message(tc2: TurnContext):
                return await tc2.send_activity(
                    f"Hello {member.name}. I'm a Teams conversation bot."
                )  # pylint: disable=cell-var-from-loop

            await turn_context.adapter.create_conversation(
                conversation_reference, get_ref, conversation_parameters
            )

        await turn_context.send_activity(
            MessageFactory.text("All messages have been sent")
        )

    async def _get_paged_members(
        self, turn_context: TurnContext
    ) -> List[TeamsChannelAccount]:
        paged_members = []
        continuation_token = None

        while True:
            current_page = await TeamsInfo.get_paged_members(
                turn_context, continuation_token, 100
            )
            continuation_token = current_page.continuation_token
            paged_members.extend(current_page.members)

            if continuation_token is None:
                break

        return paged_members

    async def _delete_card_activity(self, turn_context: TurnContext):
        await turn_context.delete_activity(turn_context.activity.reply_to_id)


    def _add_conversation_reference(self, activity: Activity):
        """
        This populates the shared Dictionary that holds conversation references. In this sample,
        this dictionary is used to send a message to members when /api/notify is hit.
        :param activity:
        :return:
        """
        conversation_reference = TurnContext.get_conversation_reference(activity)
        self.conversation_references[
            conversation_reference.user.id
        ] = conversation_reference


    #this bot needs to provide similar commands as autoGPT except the commands are based on Check Email, Check Tasks, Load Doc, Load Code etc.
    def model_response(self, msg):
        try:
            #history.predict(input=msg)
            if msg == 'agent.template':
                response = "NA:"
                return response
            response = self.agent_chain.run(msg)
            #history.chat_memory.add_ai_message(response)
            return response
        except Exception as e:
            return f"An exception occurred: {e}"
        

    def send_request(url, data):
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers, timeout=5.0)
        return response
    

    def custom_prompt_func(prompt: str, atr ) -> None:
        print(prompt)
        print(atr)
        return atr
        
    def custom_input_func(atr) -> str:
        return atr