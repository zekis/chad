# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import config
import sys
import traceback
import uuid
from datetime import datetime
from http import HTTPStatus
#https://github.com/microsoft/BotBuilder-Samples


from typing import Dict
from teams.teams_rabbit import messages, process_message, tts, default

import asyncio
import threading
from aiohttp import web
from botbuilder.core.integration import aiohttp_error_middleware


async def message_queue():
    while True:
        await process_message()
        await asyncio.sleep(0.5)

async def run_server():
    APP = web.Application(middlewares=[aiohttp_error_middleware])
    APP.router.add_post("/api/messages", messages)
    APP.router.add_static("/", path="./pages/", name="pages")
    
    runner = web.AppRunner(APP)
    await runner.setup()
    await web.TCPSite(runner, host="localhost", port=config.PORT).start()
    await asyncio.Event().wait()

async def main():
    tasks = []
    tasks.append(asyncio.create_task(run_server()))
    tasks.append(asyncio.create_task(message_queue()))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())