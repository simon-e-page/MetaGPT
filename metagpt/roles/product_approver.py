#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : product_manager.py
"""
from metagpt.actions.write_product_approval import WriteProductApproval
from metagpt.actions import WritePRD
from metagpt.roles import Role


class ProductApprover(Role):
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
        self._watch([WritePRD])