'''
Filename: MetaGPT/metagpt/provider/human_provider.py
Created Date: Wednesday, November 8th 2023, 11:55:46 pm
Author: garylin2099
'''
from typing import Optional, Callable
from metagpt.provider.base_gpt_api import BaseGPTAPI
from metagpt.logs import logger
import time as t

class HumanProvider(BaseGPTAPI):
    """Humans provide themselves as a 'model', which actually takes in human input as its response.
    This enables replacing LLM anywhere in the framework with a human, thus introducing human interaction
    """

    def __init__(self) -> None:
        self.callback: Callable = None

    def set_callback(self, callback: Callable) -> None:
        self.callback = callback

    def ask(self, msg: str, stage: str) -> str:
        logger.info("It's your turn, please type in your response. You may also refer to the context below\n")
        if self.callback is not None:
            # API Input
            rsp: str = self.callback(action="approve", stage=stage)
            # Block until we get a response!
            while self.callback(action="check", stage=stage) is None:
                t.sleep(10)
        else:
            # Direct Human input
            rsp = input(msg)

        if rsp in['yes', 'y']:
            logger.debug("Received an approval")
            rsp = '[CONTENT]{ "Approval Response": "yes" }[/CONTENT]'
        elif rsp in ['no', 'n', 'exit', 'quit']:
            logger.debug('This stage is NOT approved')
            rsp = '[CONTENT]{ "Approval Response": "no" }[/CONTENT]'
        else:
            # Unknown input
            rsp = '[CONTENT]{ "Approval Response": "no" }[/CONTENT]'

        return rsp

    async def aask(self, msg: str, system_msgs: Optional[list[str]] = None) -> str:
        stage = system_msgs[0]
        return self.ask(msg, stage)

    def completion(self, messages: list[dict]):
        """dummy implementation of abstract method in base"""
        return []

    async def acompletion(self, messages: list[dict]):
        """dummy implementation of abstract method in base"""
        return []

    async def acompletion_text(self, messages: list[dict], stream=False) -> str:
        """dummy implementation of abstract method in base"""
        return []
