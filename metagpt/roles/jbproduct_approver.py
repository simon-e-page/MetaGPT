#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : product_manager.py
"""

from typing import Callable

from metagpt.actions import WriteJBPRD, WriteProductApproval, ManagementAction
from metagpt.roles import Role
from metagpt.logs import logger


class JBProductApprover(Role):
    """
    Represents a Human Approver role responsible for approving a PRD for to enter the Design Stage.

    Attributes:
        name (str): Name of the product approver.
        profile (str): Role profile, default is 'Product Approver'.
        goal (str): Goal of the product approver.
        constraints (str): Constraints or limitations for the product approver.
    """

    def __init__(
        self,
        name: str = "Pointy 1",
        profile: str = "Product Approver",
        goal: str = "Review and Approve the Requirements Stage Gate",
        constraints: str = "",
        callback: Callable = None
    ) -> None:
        """
        Initializes the ProductApprover role with given attributes.

        Args:
            name (str): Name of the product approver.
            profile (str): Role profile.
            goal (str): Goal of the product approver.
            constraints (str): Constraints or limitations for the product approver.
        """
        super().__init__(name, profile, goal, constraints, is_human=True)
        self._init_actions([WriteProductApproval])
        if callback is not None:
            # Using API to receive approval
            self._actions[0].llm.set_callback(callback)
        self._watch([WriteJBPRD])
        self.autoapproval_msg = "AUTO-APPROVE: Requirements"
        self.approval_found = False

    async def _observe(self) -> int:
        """Override to listen for Management Directives to set Auto-Approval but take no response"""
        if not self._rc.env:
            return 0
        env_msgs: list = self._rc.env.memory.get()

        if not self.approval_found:
            autoapprovals = self._rc.env.memory.get_by_actions([ManagementAction])
            for msg in autoapprovals:
                if self.autoapproval_msg in msg.content:
                    self._actions[0].set_autoapproval()
                    self.approval_found = True

        observed: list = self._rc.env.memory.get_by_actions(self._rc.watch)
        seen: list = self._rc.memory.get_by_actions(self._rc.watch)
        seen_msgs = [f"{i.role}: {i.content[:20]}..." for i in seen]
        observed_msgs = [f"{i.role}: {i.content[:20]}..." for i in observed]

        #logger.info(f"Seen messages: {seen_msgs}")
        #logger.info(f"Observed messages: {observed_msgs}")

        news = [ i for i in observed if i not in seen ]
        self._rc.news = news
        #self._rc.news = self._rc.memory.find_news(observed)  # find news (previously unseen messages) from observed messages

        for i in env_msgs:
            self.recv(i)

        news_text = [f"{i.role}: {i.content[:20]}..." for i in self._rc.news]
        if news_text:
            logger.info(f'{self._setting} observed: {news_text}')
        return len(self._rc.news)

