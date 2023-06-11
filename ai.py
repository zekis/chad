# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import config
from dotenv import find_dotenv, load_dotenv
import sys
import traceback
import uuid
import argparse
from datetime import datetime
from bots.langchain_openai_master import model_response, process_email_schedule, process_task_schedule
from common.rabbit_comms import publish, publish_action
from common.utils import sanitize_subject

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
    publish(f"Hi {config.FRIENDLY_NAME}")
    publish_action("BOT Commands", "GET_ASSISTANTS as list", "BOT_RESTART")
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
    # config.TOOL_CHANNEL_IN = f"TOOL:IN:{config.USER_ID}"
    # config.TOOL_CHANNEL_OUT = f"TOOL_OUT:{config.USER_ID}"
    #config.TOOL_COMMAND_CHANNEL = f"CMD:{toolname}:{config.USER_ID}"
    #config.TOOL_RESPONSE_CHANNEL = f"RES:{toolname}:{config.USER_ID}"
    
    config.TENANT_ID = args.tenant_id
    config.FRIENDLY_NAME = args.user_name
    config.OFFICE_USER = args.email_address
    config.EMAIL_CACHE_FILE_NAME = "workspace/" + sanitize_subject(args.user_id,1000) + ".txt"
    config.LOCAL_MEMORY_FILE_NAME = "workspace/" + sanitize_subject(args.user_id,1000) + "txt"
    asyncio.run(main())