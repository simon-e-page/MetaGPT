#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : simonpage
@File    : write_project_approval.py
"""
from typing import List

from metagpt.actions import Action, ActionOutput
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.utils.jb_common import ApprovalError, JBParser

OUTPUT_MAPPING = {
    "Approval Response": (str, ...),
}

# Schema for System Design Deliverable
TASK_OUTPUT_MAPPING = {
    "Required Python third-party packages": (List[str], ...),
    "Required Other language third-party packages": (List[str], ...),
    "Full API spec": (str, ...),
    "Logic Analysis": (List[List[str]], ...),
    "Task list": (List[str], ...),
    "Shared Knowledge": (str, ...),
    "Anything UNCLEAR": (str, ...),
}


class WriteTaskApproval(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    def _get_tasks_from_disk(self):
        docs_path = CONFIG.product_root / "docs"
        system_design_file = docs_path / "api_spec_and_tasks.md"

        design_content = system_design_file.read_text()
        logger.debug(design_content)
        output_class = ActionOutput.create_model_class("approved_tasks", TASK_OUTPUT_MAPPING)
        #parsed_data = markdown_to_json.dictify(design_content)
        parsed_data = JBParser.parse_markdown_deliverable(design_content, TASK_OUTPUT_MAPPING)
        logger.debug(parsed_data)
        instruct_content = output_class(**parsed_data)
        return ActionOutput(design_content, instruct_content)

    async def run(self, context, *args, **kwargs) -> ActionOutput:
        """ Wait for a Human Approval """

        autoapprove = False
        for msg in context:
            if "AUTO-APPROVE: Plan" in msg.content:
                autoapprove = True
        
        prompt = "Do you approve the Tasks and API Spec? (yes/no)"
        task_approval = await self._aask_v1(prompt,
                                            "task_approval",
                                            OUTPUT_MAPPING,
                                            format='json',
                                            system_msgs=['Plan', autoapprove]
                                            )

        if task_approval.instruct_content.dict()['Approval Response'] == 'yes':
            logger.info("Got approval for Tasks and API Spec!")
            output = self._get_tasks_from_disk()
            
        else:
            logger.warning("No approval - stop project!")
            output = task_approval
            raise ApprovalError("Approval Error - API Spec not approved", approver="Task Approver")


        return output
