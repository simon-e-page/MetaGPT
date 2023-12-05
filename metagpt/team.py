#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : alexanderwu
@File    : software_company.py
"""
from pydantic import BaseModel, Field
import os

from metagpt.actions import BossRequirement
from metagpt.config import CONFIG
import metagpt.const as CONST
from metagpt.environment import Environment
from metagpt.logs import logger, add_project_log
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.common import NoMoneyException

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

    def start_project(self, product_name: str, stage: str = None, send_to: str = ""):
        """Start a project from publishing boss requirement."""
        logger.info(f'Starting project: {product_name}')

        CONFIG.product_name = product_name

        if not os.path.exists(CONFIG.product_root):
            raise FileNotFoundError(f"Need following directory with product config to start: {CONFIG.product_root}")

        self.environment.get_product_config()

        #idea: str = self.environment.idea
        if stage is not None:
            self.environment.set_stage(stage)
        
        stage = self.environment.stage
        add_project_log(CONST.WORKSPACE_ROOT / CONFIG.product_name, replace=True)

        #TODO:
        # Load History into the evironment if option to restart is provided?

        #self.environment.publish_message(Message(role="Human", content=f'For product {product_name} we are commencing stage: {stage}', cause_by=BossRequirement, send_to=send_to))
        logger.info(f'For product {product_name} we are commencing stage: {stage}')

    def _save(self):
        logger.info(self.json())

    async def run(self, n_round=3):
        """Run company until target round or no money"""
        max_round: int = n_round
        logger.info(f"Team will execute {max_round} rounds of Tasks unless they run out of Investment funds!")

        # Do we need to test if we have recovered memory?
        self.environment.publish_message(Message(role="Human", content=self.environment.idea, cause_by=BossRequirement, send_to=""))
        
        while n_round > 0:
            # self._save()
            n_round -= 1
            count: int = max_round - n_round
            logger.info(f"Entering round {count} of {max_round}")
            logger.debug(f"{n_round=}")
            self._check_balance()
            await self.environment.run()

        history_file = CONFIG.product_root / "history.txt"
        with open(history_file, 'w', encoding='utf-8') as file:
            file.write(self.environment.history)
        return self.environment.history
    