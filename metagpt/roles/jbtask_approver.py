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
        self._watch([WriteJBTasks, ManagementAction])