#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : advance_stage.py
"""
from typing import List
from metagpt.actions import WriteProductApproval, WriteDesignApproval, WriteTaskApproval

from metagpt.actions import Action, ActionOutput
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.utils.common import OutputParser, ApprovalError

OUTPUT_MAPPING = {
    "Advance Stage": (str, ...),
}

ADVANCE: dict = { 
            WriteProductApproval: 'Design',
            WriteDesignApproval: "Plan",
            WriteTaskApproval: "Build"
            }

class AdvanceStage(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context, *args, **kwargs) -> ActionOutput:
        """ Send an Advance Stage message to the environment """
        new_stage = None
        for msg in context:
            if msg.cause_by in ADVANCE.keys():
                new_stage = ADVANCE[msg.cause_by]
                break
            
        if new_stage is None:
            logger.warning("Could not find the Approval Message in the provided history!")
            logger.warning(context)
            ret = None
        else:
            rsp: str = f'[CONTENT]{ "Advance Stage": "{new_stage}" }[/CONTENT]'
            output_class = ActionOutput.create_model_class("stage_advance", OUTPUT_MAPPING)
            parsed_data: dict = OutputParser.parse_data_with_mapping(rsp, OUTPUT_MAPPING)
            instruct_content = output_class(**parsed_data)
            ret: ActionOutput = ActionOutput(rsp, instruct_content=instruct_content)
        return ret
