#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : product_manager.py
"""
from metagpt.actions import WriteDesign, WriteDesignApproval
from metagpt.roles import Role


class DesignApprover(Role):
    """
    Represents a Human Design Approver role responsible for approving a System Design for to enter a Build Stage.

    Attributes:
        name (str): Name of the product manager.
        profile (str): Role profile, default is 'Product Manager'.
        goal (str): Goal of the product manager.
        constraints (str): Constraints or limitations for the product manager.
    """

    def __init__(
        self,
        name: str = "Pointy 2",
        profile: str = "Design Approver",
        goal: str = "Review and Approve the Design Stage Gate",
        constraints: str = "",
    ) -> None:
        """
        Initializes the DesignApprover role with given attributes.

        Args:
            name (str): Name of the design approver.
            profile (str): Role profile.
            goal (str): Goal of the design approver.
            constraints (str): Constraints or limitations for the design approver.
        """
        super().__init__(name, profile, goal, constraints, is_human=True)
        self._init_actions([WriteDesignApproval])
        self._watch([WriteDesign])
