'''
Filename: MetaGPT/metagpt/provider/human_provider.py
Created Date: Wednesday, November 8th 2023, 11:55:46 pm
Author: garylin2099
'''

# Altered by simonpage

from typing import Optional, Callable
import time as t

from metagpt.provider.base_gpt_api import BaseGPTAPI
from metagpt.logs import logger

class HumanProvider(BaseGPTAPI):
    """Humans provide themselves as a 'model', which actually takes in human input as its response.
    This enables replacing LLM anywhere in the framework with a human, thus introducing human interaction
    """

    def __init__(self) -> None:
        self.callback: Callable = None

    def set_callback(self, callback: Callable) -> None:
        self.callback = callback

    def ask(self, msg: str, stage: str ="Requirements", autoapprove=False) -> str:
        
        if autoapprove:
            logger.info("Responding with Auto-Approval")
            rsp = "yes"
        elif self.callback is not None:
            # API Input
            logger.info("Waiting for API response.")
            self.callback(action="approve", stage=stage)
            # Block until we get a response!
            rsp  = self.callback(action="check", stage=stage)
            while rsp is None:
                t.sleep(10)
                rsp  = self.callback(action="check", stage=stage)
                logger.info(f"Approval received: {rsp}")
        else:
            # Direct Human input
            logger.info("Waiting for human response.")
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
        if len(system_msgs)>1:
            autoapprove = system_msgs[1]
        else:
            autoapprove = False
        return self.ask(msg, stage=stage, autoapprove=autoapprove)

    def completion(self, messages: list[dict]):
        """dummy implementation of abstract method in base"""
        return []

    async def acompletion(self, messages: list[dict]):
        """dummy implementation of abstract method in base"""
        return []

    async def acompletion_text(self, messages: list[dict], stream=False) -> str:
        """dummy implementation of abstract method in base"""
        return []
