# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from dotenv import find_dotenv, load_dotenv
import sys
import traceback
import uuid
import argparse
from datetime import datetime
from bots.langchain_openai_master import model_response, process_email_schedule, process_task_schedule, Init
from common.rabbit_comms import publish, publish_action, publish_actions
from common.utils import sanitize_subject
import config
import asyncio
import threading

async def task_scheduler():
    #publish("Let me check to see if I have any scheduled tasks due today.")
    while True:
        process_task_schedule()
        await asyncio.sleep(config.Todo_PollingIntervalSeconds)

async def email_scheduler():
    #publish("Let me check to see if I have any scheduled tasks due today.")
    while True:
        process_email_schedule()
        await asyncio.sleep(config.Todo_PollingIntervalSeconds / 10)

async def ai_response():
    Init()
    publish(f"Hi {config.FRIENDLY_NAME}")
    #publish_action("Get Started", "List available tools", "BOT_RESTART")
    buttons = [("Check my tasks", "Show me a list of my task folders"),("Check the weather", "Check the weather for my saved location"),("Check emails", "Did I get any emails today?"), ("Book a meeting", "Book a meeting for tomorrow morning"), ("Draft an email", "Draft an email"), ("Research AI news", "Research AI news"), ("Restart BOT", "bot_restart")]
    publish_actions("How can I help you today?", buttons)
    while True:
        #model_selector()
        model_response()
        await asyncio.sleep(0.5)
        #await asyncio.Event().wait()
    
async def main():
    ai_tasks = []
    ai_tasks.append(asyncio.create_task(ai_response()))
    ai_tasks.append(asyncio.create_task(task_scheduler()))
    ai_tasks.append(asyncio.create_task(email_scheduler()))
    await asyncio.gather(*ai_tasks)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Language Chain Bot")
    parser.add_argument("user_id", type=str, help="User ID")
    parser.add_argument("tenant_id", type=str, help="Tenant ID")
    parser.add_argument("user_name", type=str, help="User Name")
    parser.add_argument("email_address", type=str, help="Email Address")
    args = parser.parse_args()
    config.USER_ID = args.user_id
    config.TENANT_ID = args.tenant_id
    config.FRIENDLY_NAME = args.user_name
    config.OFFICE_USER = args.email_address
    config.EMAIL_CACHE_FILE_NAME = "workspace/" + sanitize_subject(args.user_id,1000) + ".txt"
    config.LOCAL_MEMORY_FILE_NAME = "workspace/" + sanitize_subject(args.user_id,1000) + "txt"

    # Need to check for GPT API key here and request key before starting bot
    asyncio.run(main())