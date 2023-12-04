#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_prd.py
"""
from typing import List

from metagpt.actions import Action, ActionOutput
from metagpt.actions.search_and_summarize import SearchAndSummarize
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.utils.get_template import get_template
import json
from metagpt.utils.common import OutputParser

OUTPUT_MAPPING = {
    "Approval Response": (str, ...),
}

PRD_OUTPUT_MAPPING = {
    "Original Requirements": (str, ...),
    "Product Goals": (List[str], ...),
    "User Stories": (List[str], ...),
    "Competitive Analysis": (List[str], ...),
    "Competitive Quadrant Chart": (str, ...),
    "Requirement Analysis": (str, ...),
    "Requirement Pool": (List[List[str]], ...),
    "UI Design draft": (str, ...),
    "Anything UNCLEAR": (str, ...),
}

class WriteProductApproval(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    def get_prd_from_disk(self):
        path = CONFIG.product_root / "docs" / "prd.md"
        prd_content = path.read_text()
        output_class = ActionOutput.create_model_class("approved_prd", PRD_OUTPUT_MAPPING)
        parsed_data = OutputParser.parse_data_with_mapping(prd_content, PRD_OUTPUT_MAPPING)
        instruct_content = output_class(**parsed_data)
        return ActionOutput(prd_content, instruct_content)
    
    async def run(self, prd, *args, **kwargs) -> ActionOutput:
        """ Wait for a Human Approval """
        prompt = "Do you approve the Product Requirements? (yes/no)"
        prd_approval = await self._aask_v1(prompt, "prd_approval", OUTPUT_MAPPING, format='json')
        
        if prd_approval.instruct_content.dict()['Approval Response'] == 'yes':
            logger.info("Got approval for Product Requirements!")
            output = self.get_prd_from_disk()
            logger.debug(output.content)
            logger.debug(output.instruct_content)
        else:
            logger.warning("No approval - stop project!")
            output = prd_approval
            #TODO: how to stop project?

        return output
