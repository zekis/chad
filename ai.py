# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import config
from dotenv import find_dotenv, load_dotenv
import sys
import traceback
import uuid

from datetime import datetime
from bots.langchain_openai_master import model_response, process_schedule, publish

import asyncio
import threading

async def task_scheduler():
    #publish("Let me check to see if I have any scheduled tasks due today.")
    while True:
        await process_schedule()
        await asyncio.sleep(config.Todo_PollingIntervalSeconds)
        
async def ai_response():
    publish("bot1_online")
    while True:
        #model_selector()
        await model_response()
        await asyncio.sleep(0.5)
        #await asyncio.Event().wait()
    
async def main2():
    ai_tasks = []
    ai_tasks.append(asyncio.create_task(ai_response()))
    ai_tasks.append(asyncio.create_task(task_scheduler()))
    await asyncio.gather(*ai_tasks)



if __name__ == "__main__":
    asyncio.run(main2())