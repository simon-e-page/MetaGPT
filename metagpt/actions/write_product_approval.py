#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_prd.py
"""
from typing import List
#import json
import markdown_to_json

from metagpt.actions import Action, ActionOutput
#from metagpt.actions.search_and_summarize import SearchAndSummarize
from metagpt.config import CONFIG
from metagpt.logs import logger
#from metagpt.utils.get_template import get_template
from metagpt.utils.common import OutputParser, ApprovalError

OUTPUT_MAPPING = {
    "Approval Response": (str, ...),
}

# Schema for PRD Deliverable
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
    """
    This class represents the action of writing a product approval.

    It extends the Action class and overrides the run method to implement the product approval process. 
    The process involves asking for approval and based on the response, either proceeding with getting the product requirements document (PRD) from disk or stopping the project.

    Attributes:
        name (str): The name of the action.
        context (dict): The context in which the action is being performed.
        llm (LanguageModel): The language model being used.

    Methods:
        run(prd, *args, **kwargs): Executes the action, asking for approval and acting based on the response.
    """
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    def _get_prd_from_disk(self):
        path = CONFIG.product_root / "docs" / "prd.md"
        prd_content = path.read_text()
        logger.debug(prd_content)
        output_class = ActionOutput.create_model_class("approved_prd", PRD_OUTPUT_MAPPING)
        parsed_data = markdown_to_json.jsonify(prd_content)
        #parsed_data = OutputParser.parse_data_with_mapping(prd_content, PRD_OUTPUT_MAPPING)
        logger.debug(parsed_data)
        instruct_content = output_class(**parsed_data)
        return ActionOutput(prd_content, instruct_content)
    
    async def run(self, context, *args, **kwargs) -> ActionOutput:
        """ Wait for a Human Approval """
        prompt = "Do you approve the Product Requirements? (yes/no)"
        prd_approval = await self._aask_v1(prompt, "prd_approval", OUTPUT_MAPPING, format='json')
        
        if prd_approval.instruct_content.dict()['Approval Response'] == 'yes':
            logger.info("Got approval for Product Requirements!")
            output = self._get_prd_from_disk()
            logger.debug(output.content)
            logger.debug(output.instruct_content)
        else:
            logger.warning("No approval - stop project!")
            output = prd_approval
            # TODO: Update with proper Exception class

            raise ApprovalError("Approval Error - Product not approved", approver="ProductApprover")

        return output
