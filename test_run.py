#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fire
import server

def main(
    #idea: str,
    investment: float = 3.0,
    n_round: int = 7,
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
    #asyncio.run(startup(product_name, investment=investment, n_round=n_round, code_review=code_review, run_tests=run_tests, implement=implement, stage=stage))
    server.main(product_name=product_name,
                investment=investment,
                n_round=n_round,
                code_review=code_review,
                run_tests=run_tests,
                implement=implement,
                stage=stage
                )

    while server.status() == "RUNNING":
        print(server.get_logs())
    
if __name__ == "__main__":
    l = server.get_projects()
    print(l)

    i = server.get_project(l[0])
    print(i)
    #fire.Fire(main)
