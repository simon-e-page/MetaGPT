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
        self._watch([WriteJBPRD, ManagementAction])
