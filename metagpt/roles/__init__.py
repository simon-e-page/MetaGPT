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

from metagpt.roles.jbproduct_approver import ProductApprover
from metagpt.roles.jbdesign_approver import DesignApprover
from metagpt.roles.jbtask_approver import TaskApprover
from metagpt.roles.stage_governance import StageGovernance
from metagpt.roles.jbarchitect import JBArchitect
from metagpt.roles.jbengineer import JBEngineer
from metagpt.roles.jbproject_manager import JBProjectManager
from metagpt.roles.jbqa_engineer import JBQaEngineer

# This denotes the roles whose memories should be 'retained'
# at the commencement of each stage
# We assume Approval of the prior stage must occur before commencement

STAGE_ROLES = {
    "Requirements": [],
    "Design": [ ProductManager ],
    "Plan": [ ProductManager, ProductApprover, JBArchitect ],
    "Build": [ ProductManager, ProductApprover, JBArchitect, JBProjectManager ],
    "Test": [ ProductManager, ProductApprover, JBArchitect, JBProjectManager, TaskApprover, JBEngineer ],
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
    "StageGovernance",
    "JBArchitect",
    "JBEngineer",
    "JBProjectManager",
    "JBQaEngineer",
]
