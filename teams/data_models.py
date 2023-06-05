# Copyright (c) Microsoft Corp. All rights reserved.
# Licensed under the MIT License.

from typing import Union

from botbuilder.schema.teams import (
    TaskModuleResponse,
    TaskModuleMessageResponse,
    TaskModuleTaskInfo,
    TaskModuleContinueResponse,
)


class TaskModuleResponseFactory:
    @staticmethod
    def create_response(value: Union[str, TaskModuleTaskInfo]) -> TaskModuleResponse:
        if isinstance(value, TaskModuleTaskInfo):
            return TaskModuleResponse(task=TaskModuleContinueResponse(value=value))
        return TaskModuleResponse(task=TaskModuleMessageResponse(value=value))

    @staticmethod
    def to_task_module_response(task_info: TaskModuleTaskInfo):
        return TaskModuleResponseFactory.create_response(task_info)

class ConversationData:
    def __init__(
        self,
        timestamp: str = None,
        channel_id: str = None,
        prompted_for_user_name: bool = False,
    ):
        self.timestamp = timestamp
        self.channel_id = channel_id
        self.prompted_for_user_name = prompted_for_user_name
        #add env variables here

class UserProfile:
    def __init__(self, name: str = None):
        self.name = name