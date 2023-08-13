# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from dotenv import find_dotenv, load_dotenv
import sys
import traceback
import uuid
import argparse
from datetime import datetime
#from bots.langchain_openai_master import model_response, process_email_schedule, process_task_schedule, Init
from bots.langchain_openai_master import openaai_master
from common.rabbit_comms import publish, publish_action, publish_actions
from common.utils import sanitize_subject
import config
import asyncio
import threading



async def task_scheduler(bot):
    #publish("Let me check to see if I have any scheduled tasks due today.")
    while True:
        bot.process_task_schedule()
        await asyncio.sleep(config.Todo_PollingIntervalSeconds)

async def email_scheduler(bot):
    #publish("Let me check to see if I have any scheduled tasks due today.")
    while True:
        bot.process_email_schedule()
        await asyncio.sleep(config.Todo_PollingIntervalSeconds / 10)

async def ai_response(bot):
    
    publish(f"Hi {config.FRIENDLY_NAME}, How can I help you today?")
    #publish_action("Get Started", "List available tools", "BOT_RESTART")
    #buttons = [("Check my tasks", "Show me a list of my task folders"),("Check the weather", "Check the weather for my saved location"),("Check emails", "Did I get any emails today?"), ("Book a meeting", "Book a meeting for tomorrow morning"), ("Draft an email", "Draft an email"), ("Research AI news", "Research AI news"), ("Restart BOT", "bot_restart")]
    #publish_actions("How can I help you today?", buttons)
    while True:
        #model_selector()
        bot.model_response()
        await asyncio.sleep(0.5)
        #await asyncio.Event().wait()
    
async def main():
    #Create master bot
    bot = openaai_master()
    ai_tasks = []
    ai_tasks.append(asyncio.create_task(ai_response(bot)))
    ai_tasks.append(asyncio.create_task(task_scheduler(bot)))
    ai_tasks.append(asyncio.create_task(email_scheduler(bot)))
    await asyncio.gather(*ai_tasks)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Language Chain Bot")
    parser.add_argument("user_id", type=str, help="User ID")
    parser.add_argument("tenant_id", type=str, help="Tenant ID")
    parser.add_argument("user_name", type=str, help="User Name")
    parser.add_argument("email_address", type=str, help="Email Address")
    #parser.add_argument("reset_config", type=bool, help="reset config", default=False, required=False)
    parser.add_argument("--reset_config", action="store_true", help="reset config", default=False)
    args = parser.parse_args()

    print("starting bot...")
    print("user_id: " + args.user_id)
    print("tenant_id: " + args.tenant_id)
    print("user_name: " + args.user_name)
    print("email_address: " + args.email_address)
    print("reset_config: " + str(args.reset_config))


    config.USER_ID = args.user_id
    config.TENANT_ID = args.tenant_id
    config.FRIENDLY_NAME = args.user_name
    config.OFFICE_USER = args.email_address
    config.EMAIL_CACHE_FILE_NAME = "workspace/" + sanitize_subject(args.user_id,1000) + ".txt"
    config.LOCAL_MEMORY_FILE_NAME = "workspace/" + sanitize_subject(args.user_id,1000) + "txt"
    config.RESET_CONFIG = args.reset_config
    # Need to check for GPT API key here and request key before starting bot
    asyncio.run(main())