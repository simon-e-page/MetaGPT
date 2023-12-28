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

from metagpt.roles.jbproduct_approver import JBProductApprover
from metagpt.roles.jbdesign_approver import JBDesignApprover
from metagpt.roles.jbtask_approver import JBTaskApprover
from metagpt.roles.jbstage_governance import JBStageGovernance
from metagpt.roles.jbproduct_manager import JBProductManager
from metagpt.roles.jbarchitect import JBArchitect
from metagpt.roles.jbengineer import JBEngineer
from metagpt.roles.jbproject_manager import JBProjectManager
from metagpt.roles.jbqa_engineer import JBQaEngineer


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
    "JBProductApprover",
    "JBDesignApprover",
    "JBTaskApprover",
    "JBStageGovernance",
    "JBArchitect",
    "JBEngineer",
    "JBProjectManager",
    "JBQaEngineer",
    "JBProductManager",
]
