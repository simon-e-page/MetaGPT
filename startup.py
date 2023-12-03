#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio

import fire

from metagpt.roles import (
    Architect,
    Engineer,
    ProductManager,
    ProjectManager,
    QaEngineer,
)
from metagpt.roles.design_approver import DesignApprover
from metagpt.roles.product_approver import ProductApprover
from metagpt.team import Team
from metagpt.logs import logger

async def startup(
    product_name: str,
    investment: float = 3.0,
    n_round: int = 5,
    code_review: bool = False,
    run_tests: bool = False,
    implement: bool = True,
    stage: str = "Requirements"
):
    """Run a startup. Be a boss."""
    company = Team()
    company.hire(
        [
            ProductManager(),
            Architect(),
            ProjectManager(),
            DesignApprover(),
            ProductApprover(),
        ]
    )

    logger.info("Including Product Team for Requirements Stage")
    logger.info("Including Design Team for System Design Stage")
    logger.info("Including Project Manager for Task Breakdown")

    # if implement or code_review
    if implement or code_review:
        # developing features: implement the idea
        company.hire([Engineer(n_borg=5, use_code_review=code_review)])
        logger.info("Including Engineers for Build Stage")

    if run_tests:
        # developing features: run tests on the spot and identify bugs
        # (bug fixing capability comes soon!)
        company.hire([QaEngineer()])
        logger.info("Including QA Engineers for Test Stage")

    company.invest(investment)
    company.start_project(product_name, stage)
    await company.run(n_round=n_round)


def main(
    #idea: str,
    investment: float = 3.0,
    n_round: int = 5,
    code_review: bool = True,
    run_tests: bool = False,
    implement: bool = True,
    product_name: str = "Test_Product",
    stage: str = "Requirements"
):
    """
    We are a software startup comprised of AI. By investing in us,
    you are empowering a future filled with limitless possibilities.
    :param product_name: The name of your product and key directory name in the workspace. 
    Make sure the directory WORKSPACE_ROOT/PRODUCT_NAME exists.
    Make sure that there is a file product.yaml in that directory with at least the IDEA and STAGE defined
    :param investment: As an investor, you have the opportunity to contribute
    a certain dollar amount to this AI company.
    :param n_round:
    :param code_review: Whether to use code review.
    :param implement: Whether to write the code
    :param stage: The project stage to start or resume [Design, Build, Test, Deploy]
    :return:
    """
    asyncio.run(startup(product_name, investment=investment, n_round=n_round, code_review=code_review, run_tests=run_tests, implement=implement, stage=stage))


if __name__ == "__main__":
    fire.Fire(main)
