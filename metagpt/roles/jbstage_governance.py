#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : stage_governance.py
"""

from metagpt.actions import WriteProductApproval, WriteDesignApproval, WriteTaskApproval, AdvanceStage
from metagpt.roles import Role

ADVANCE: dict = { 
            WriteProductApproval: 'Design',
            WriteDesignApproval: "Plan",
            WriteTaskApproval: "Build"
            }

class JBStageGovernance(Role):
    """
    Represents an automated role responsible for advancing the execution to the next Stage

    Attributes:
        name (str): Name of the role.
        profile (str): Role profile.
        goal (str): Goal of the role.
        constraints (str): Constraints or limitations for the role.
    """

    def __init__(
        self,
        name: str = "Stage Governance Committee",
        profile: str = "Governance",
        goal: str = "Publish the advance to the next Stage",
        constraints: str = "",
        watchlist: list = [WriteProductApproval, WriteDesignApproval, WriteTaskApproval]
    ) -> None:
        """
        Initializes the Stage Governance role with given attributes.

        Attributes:
            name (str): Name of the role.
            profile (str): Role profile.
            goal (str): Goal of the role.
            constraints (str): Constraints or limitations for the role.
            watchlist: the specific Actions that can trigger a stage advancement event
        """
        super().__init__(name, profile, goal, constraints, is_human=False)
        self._init_actions([AdvanceStage])
        self._watch(watchlist)

