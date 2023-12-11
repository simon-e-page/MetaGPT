#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : __init__.py
"""

from metagpt.roles.role import Role
from metagpt.roles.architect import Architect
from metagpt.roles.project_manager import ProjectManager
from metagpt.roles.product_manager import ProductManager
from metagpt.roles.engineer import Engineer
from metagpt.roles.qa_engineer import QaEngineer
from metagpt.roles.seacher import Searcher
from metagpt.roles.sales import Sales
from metagpt.roles.customer_service import CustomerService
from metagpt.roles.product_approver import ProductApprover
from metagpt.roles.design_approver import DesignApprover
from metagpt.roles.task_approver import TaskApprover
from metagpt.roles.stage_governance import StageGovernance

# This denotes the roles whose memories should be 'retained'
# at the commencement of each stage
# We assume Approval of the prior stage must occur before commencement

STAGE_ROLES = {
    "Requirements": [],
    "Design": [ ProductManager ],
    "Plan": [ ProductManager, ProductApprover, Architect ],
    "Build": [ ProductManager, ProductApprover, Architect, ProjectManager ],
    "Test": [ ProductManager, ProductApprover, Architect, ProjectManager, TaskApprover, Engineer ],
}

__all__ = [
    "Role",
    "Architect",
    "ProjectManager",
    "ProductManager",
    "Engineer",
    "QaEngineer",
    "Searcher",
    "Sales",
    "CustomerService",
    "ProductApprover",
    "DesignApprover",
    "TaskApprover",
    "StageGovernance"
]
