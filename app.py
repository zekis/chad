# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import config
import sys
import traceback
import uuid
from datetime import datetime
from http import HTTPStatus
from typing import Dict
from bots.chad import messages, notify

from aiohttp import web
from botbuilder.core.integration import aiohttp_error_middleware

APP = web.Application(middlewares=[aiohttp_error_middleware])
APP.router.add_post("/api/messages", messages)
APP.router.add_get("/api/notify", notify)

if __name__ == "__main__":
    try:
        web.run_app(APP, host="localhost", port=config.PORT)
    except Exception as error:
        raise error