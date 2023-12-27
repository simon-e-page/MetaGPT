#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : product_manager.py
"""

from typing import Callable

from metagpt.actions import WriteJBTasks, WriteTaskApproval, ManagementAction
from metagpt.roles import Role


class JBTaskApprover(Role):
    """
    Represents a Human Approver role responsible for approving the Project Management Tasks and API Spec
    for to enter the Build Stage.

    Attributes:
        name (str): Name of the task approver.
        profile (str): Role profile, default is 'Product Approver'.
        goal (str): Goal of the product approver.
        constraints (str): Constraints or limitations for the product approver.
    """

    def __init__(
        self,
        name: str = "Pointy 3",
        profile: str = "Task Approver",
        goal: str = "Review and Approve the Plan Stage Gate",
        constraints: str = "",
        callback: Callable = None
    ) -> None:
        """
        Initializes the TaskApprover role with given attributes.

        Args:
            name (str): Name of the task approver.
            profile (str): Role profile.
            goal (str): Goal of the task approver.
            constraints (str): Constraints or limitations for the task approver.
        """
        super().__init__(name, profile, goal, constraints, is_human=True)
        self._init_actions([WriteTaskApproval])
        if callback is not None:
            # Using API to receive approval
            self._actions[0].llm.set_callback(callback)
        self._watch([WriteJBTasks])
        self.autoapproval_msg = "AUTO-APPROVE: Plan"

    async def _observe(self) -> int:
        """Override to listen for Management Directives to set Auto-Approval but take no response"""
        if not self._rc.env:
            return 0
        env_msgs = self._rc.env.memory.get()

        autoapprovals = self._rc.env.memory.get_by_actions([ManagementAction])
        for msg in autoapprovals:
            if self.autoapproval_msg in msg.content:
                self._actions[0].set_autoapproval()
                
        observed = self._rc.env.memory.get_by_actions(self._rc.watch)
        
        self._rc.news = self._rc.memory.find_news(observed)  # find news (previously unseen messages) from observed messages

        for i in env_msgs:
            self.recv(i)

        news_text = [f"{i.role}: {i.content[:20]}..." for i in self._rc.news]
        #if news_text:
        #    logger.debug(f'{self._setting} observed: {news_text}')
        return len(self._rc.news)
