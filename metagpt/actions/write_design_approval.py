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


OUTPUT_MAPPING = {
    "Approval Response": (str, ...),
}


class WriteDesignApproval(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, design, *args, **kwargs) -> ActionOutput:
        """ Wait for a Human Approval """
        prompt = "Do you approve the System Design? (yes/no)"
        design_approval = await self._aask_v1(prompt, "design_approval", OUTPUT_MAPPING, format='json')

        if design_approval.instruct_content.dict()['Approval Response'] == 'yes':
            logger.info("Got approval for Product Requirements!")
        else:
            logger.warning("No approval - stop project!")
            exit()
            #TODO: how best to stop project?

        return design_approval
