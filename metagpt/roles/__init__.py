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

# This denotes the roles whose memories should be 'retained'
# at the commencement of each stage
# We assume Approval of the prior stage must occur before commencement

STAGE_ROLES = {
    "Requirements": [],
    "Design": [ JBProductManager ],
    "Plan": [ JBProductManager, JBProductApprover, JBArchitect ],
    "Build": [ JBProductManager, JBProductApprover, JBArchitect, JBDesignApprover, JBProjectManager ],
    "Test": [ JBProductManager, JBProductApprover, JBArchitect, JBDesignApprover, JBProjectManager, JBTaskApprover, JBEngineer ],
}

STAGE_TEAM = {
    "Requirements": [JBProductManager, JBProductApprover, JBStageGovernance],
    "Design": [ JBProductManager, JBProductApprover, JBArchitect, JBDesignApprover, JBStageGovernance ],
    "Plan": [JBProductManager, JBProductApprover, JBArchitect, JBDesignApprover, JBProjectManager, JBTaskApprover, JBStageGovernance ],
    "Build": [JBProductManager, JBProductApprover, JBArchitect, JBDesignApprover, JBProjectManager, JBTaskApprover, JBEngineer, JBStageGovernance ],
    "Test": [ JBProductManager, JBProductApprover, JBArchitect, JBDesignApprover, JBProjectManager, JBTaskApprover, JBEngineer, JBQaEngineer, JBStageGovernance ],
}

# This works by triggering the action from the Approver of the Previous Stage
APPROVERS: dict = {
    "Requirements": [],
    "Design": [ JBProductApprover, JBStageGovernance ],
    "Plan": [ JBDesignApprover, JBStageGovernance ],
    "Build": [ JBTaskApprover, JBStageGovernance ],
    "Test": [ JBEngineer, JBStageGovernance ],
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
