# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import config
from dotenv import find_dotenv, load_dotenv
import sys
import traceback
import uuid
from datetime import datetime
from bots.langchain_openai import *

if __name__ == "__main__":
    model_response()