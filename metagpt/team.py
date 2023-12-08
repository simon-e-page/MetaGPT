#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : alexanderwu
@File    : software_company.py
"""
from pydantic import BaseModel, Field
import os
import traceback
from pathlib import Path

from metagpt.actions import BossRequirement, STAGE_ACTIONS
from metagpt.config import CONFIG
import metagpt.const as CONST
from metagpt.environment import Environment
from metagpt.logs import logger, add_project_log
from metagpt.roles import Role, STAGE_ROLES
from metagpt.schema import Message
from metagpt.utils.common import NoMoneyException, ApprovalError

from metagpt.utils.serialize import serialize_batch, deserialize_batch


class Team(BaseModel):
    """
    Team: Possesses one or more roles (agents), SOP (Standard Operating Procedures), and a platform for instant messaging,
    dedicated to perform any multi-agent activity, such as collaboratively writing executable code.
    """
    environment: Environment = Field(default_factory=Environment)
    investment: float = Field(default=10.0)
    idea: str = Field(default="")

    class Config:
        arbitrary_types_allowed = True

    def hire(self, roles: list[Role]):
        """Hire roles to cooperate"""
        role_names = [ x.profile for x in roles ]
        logger.info(f"Including the following roles: {','.join(role_names)}")
        self.environment.add_roles(roles)

    def invest(self, investment: float):
        """Invest company. raise NoMoneyException when exceed max_budget."""
        self.investment = investment
        CONFIG.max_budget = investment
        logger.info(f'Investment: ${investment}.')

    def _check_balance(self):
        if CONFIG.total_cost > CONFIG.max_budget:
            raise NoMoneyException(CONFIG.total_cost, f'Insufficient funds: {CONFIG.max_budget}')


    def _map_stage_to_deliverable(self, stage: str) -> Path:
        if stage == "Requirements":
            path: Path = CONFIG.product_root / "docs" / "prd.md"
        elif stage == "Design":
            path = CONFIG.product_root / "docs" / "system_design.md"
        elif stage == "Plan":
            path = CONFIG.product_root / "docs" / "api_spec_and_tasks.md"
        else:
            path = None
        return path
    
    def get_deliverable(self, stage: str) -> str:
        path: Path = self._map_stage_to_deliverable(stage)
        content: str = ""
        if path is not None:
            try:
                content = path.read_text()
            except FileNotFoundError:
                logger.warning(f"Can't find deliverable: {path}")
        else:
            logger.warning(f"No deliverable defined for stage {stage}")
        
        return content

    def update_deliverable(self, stage: str, content: str) -> str:
        path: Path = self._map_stage_to_deliverable(stage)
        if path is not None:
            try:
                content = path.write_text(content, encoding='utf-8')
                ret = "OK"
            except FileNotFoundError:
                logger.warning(f"Can't find deliverable: {path}")
                ret = "Error"
        else:
            logger.warning(f"No deliverable defined for stage {stage}")
            ret = "Error"
        return ret


    def create_project(self, product_name: str, idea: str):
        stage = "Requirements"
        CONFIG.product_name = product_name
        os.makedirs(CONFIG.product_root, exist_ok=True)
        self.environment.create_product_config(idea, stage)

    def start_project(self, product_name: str, stage: str = None, send_to: str = ""):
        """Start a project from publishing boss requirement."""
        logger.info(f'Starting project: {product_name}')

        CONFIG.product_name = product_name

        if not os.path.exists(CONFIG.product_root):
            raise FileNotFoundError(f"Need following directory with product config to start: {CONFIG.product_root}")

        self.environment.get_product_config()

        if stage is not None:
            self.environment.set_stage(stage)
        
        stage = self.environment.stage
        add_project_log(CONST.WORKSPACE_ROOT / CONFIG.product_name, replace=True)

        logger.info(f'For product {product_name} we are commencing stage: {stage}')

    def _save(self):
        logger.info(self.json())


    def filter_messages(self, messages, keep: list):
        """ Strips all messages that are not in the list of specific actions"""
        messages = [ m for m in messages if m.cause_by in keep ]
        return messages


    def set_memory(self, stage: str=None):
        """ Resets Memory of Roles and Environment to a specific stage. 
            If None then restores to last run 
        """

        history_file = CONFIG.product_root / "history.pickle"
        if history_file.exists():
            logger.warning("Loading messages from a previous execution and replaying!")
            messages = deserialize_batch(history_file.read_bytes())
            messages = self.filter_messages(messages, STAGE_ACTIONS[stage])
            self.environment.memory.add_batch(messages)
        else:
            logger.info("Commencing project with Boss Requirement")
            self.environment.publish_message(Message(role="Human", content=self.environment.idea, cause_by=BossRequirement, send_to=""))
        
        for name, role in self.environment.get_roles().items():
            if type(role) not in STAGE_ROLES:
                logger.info(f"Clearing memory for {name}")
                role._rc.memory.clear()


    async def run(self, n_round=3, callback=None):
        """Run company until target round or no money"""
        max_round: int = n_round
        if callback is not None:
            self.environment.callback = callback
        logger.info(f"Team will execute {max_round} rounds of Tasks unless they run out of Investment funds!")

        self.set_memory(self.environment.stage)
        
        while n_round > 0:
            # self._save()
            n_round -= 1
            count: int = max_round - n_round
            logger.info(f"Entering round {count} of {max_round}")
            logger.debug(f"{n_round=}")
            self._check_balance()
            try:
                await self.environment.run()
            except ApprovalError as e:
                logger.error(f"Approval not given by {e.approver}")
                role = self.environment.get_role(e.approver)
                if role is not None:
                    logger.warning(f"Clearing memory for {e.approver}")
                    role._rc.memory.clear()
                else:
                    logger.error(f"Could not find an active role with profile={e.approver}. Should not happen!")
                n_round = 0
            except Exception as e:
                logger.error("Uncaught Exception!")
                logger.error(traceback.format_exc())
                n_round = 0
            
        history_file = CONFIG.product_root / "history.pickle"
        with open(history_file, 'wb') as file:
            file.write(serialize_batch(self.environment.memory.get()))
        
        self.environment.save_product_config()
        return self.environment.history
    