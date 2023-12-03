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
#    "Original Requirements": (str, ...),
#    "Product Goals": (List[str], ...),
#    "User Stories": (List[str], ...),
#    "Competitive Analysis": (List[str], ...),
#    "Competitive Quadrant Chart": (str, ...),
#    "Requirement Analysis": (str, ...),
#    "Requirement Pool": (List[List[str]], ...),
#    "UI Design draft": (str, ...),
#    "Anything UNCLEAR": (str, ...),
}


class WriteProductApproval(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, prd, *args, **kwargs) -> ActionOutput:
        """ Wait for a Human Approval """
        #sas = SearchAndSummarize()
        # rsp = await sas.run(context=requirements, system_text=SEARCH_AND_SUMMARIZE_SYSTEM_EN_US)
        #rsp = ""
        #info = f"### Search Results\n{sas.result}\n\n### Search Summary\n{rsp}"
        #if sas.result:
        #    logger.info(sas.result)
        #    logger.info(rsp)

        #prompt_template, format_example = get_template(templates, format)
        #prompt = prompt_template.format(
        #    requirements=requirements, search_information=info, format_example=format_example
        #)
        #logger.debug(prompt)
        # prd = await self._aask_v1(prompt, "prd", OUTPUT_MAPPING)
        prompt = "Do you approve the Product Requirements? (yes/no)"
        prd_approval = await self._aask_v1(prompt, "prd_approval", OUTPUT_MAPPING, format=format)

        print(prd_approval.content)
        print(prd_approval.instruct_content)

        if prd_approval.content == 'yes':
            logger.info("Got approval for Product Requirements!")
        else:
            logger.warning("No approval - stop project!")
            #TODO: how to stop project?

        return prd
