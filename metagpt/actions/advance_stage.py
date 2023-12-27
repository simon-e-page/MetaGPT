#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : simonpage
@File    : advance_stage.py
"""

from metagpt.actions import WriteProductApproval, WriteDesignApproval, WriteTaskApproval
from metagpt.actions import Action, ActionOutput
from metagpt.logs import logger
from collections import OrderedDict

OUTPUT_MAPPING = {
    "Advance Stage": (str, ...),
}

ADVANCE: OrderedDict = { 
            WriteProductApproval: {'index': 0, 'stage': 'Design'},
            WriteDesignApproval:  {'index': 1, 'stage': "Plan"  },
            WriteTaskApproval:    {'index': 2, 'stage': "Build" },
            }


class AdvanceStage(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context, *args, **kwargs) -> ActionOutput:
        """ Send an Advance Stage message to the environment """

        # Look for the latest (most advanced) approval message
        new_stage = None
        new_index = -1
        for msg in context:
            if msg.cause_by in ADVANCE.keys():
                temp_index = ADVANCE[msg.cause_by]['index']
                if temp_index > new_index:
                    new_stage = ADVANCE[msg.cause_by]['stage']
                    new_index = temp_index

        if new_stage is None:
            logger.warning("Could not find the Approval Message in the provided history!")
            logger.warning(context)
            ret = None
        else:
            rsp: str = f'[CONTENT]{{ "Advance Stage": "{new_stage}" }}[/CONTENT]'
            output_class = ActionOutput.create_model_class("stage_advance", OUTPUT_MAPPING)
            parsed_data: dict = { "Advance Stage": new_stage }
            instruct_content = output_class(**parsed_data)
            ret: ActionOutput = ActionOutput(rsp, instruct_content=instruct_content)
        return ret
