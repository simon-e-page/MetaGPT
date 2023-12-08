#!/usr/bin/env python
# -*- coding: utf-8 -*-
import anvil.server
import asyncio

from startup import startup
from metagpt.team import Team
import time as t

company: Team = None
task = None
status: str = "Idle"

authenticated_callable = anvil.server.callable(require_user=True)

@authenticated_callable
def create_project(product_name: str, idea: str):
    # TODO: take this out of the Team structure..
    global company
    if company is None:
        company = Team()
    company.create_project(product_name, idea)

def check_status():
    global status
    if task is not None:
        # TODO: interrogate running status - Excamples
        if task.is_completed():
            status = "Idle"
            task = None
        elif task.:
            status = "Running"
        # TODO: how to get stage from the running process?
    else:
        status = "Idle"
    return status

@anvil.server.background_task
def run_project_background(n_round: int = 5) -> str:
    history: str = asyncio.run(company.run(n_round=n_round, callback=prompt_approval))
    return history

@authenticated_callable
def run_project(
    product_name, 
    investment=5.0, 
    n_round=5, 
    code_review=False, 
    run_tests=False, 
    implement=False, 
    stage="Requirements"
    ) -> bool:
    
    # TODO: how to return a handle for the Team object that is created?
    global company, future
    
    if task is None:
        company.registerAPI(stage, ready_to_approve)
        company = startup(
            product_name=product_name,
            investment=investment, 
            n_round=n_round,
            code_review=code_review,
            run_tests=run_tests,
            implement=implement,
            stage=stage
            )
        
        #TODO: this needs to be kicked off in a separate thread?
        task = anvil.server.launch_background_task('run_project_background' , n_round)
        check_status()
        ret = True
    else:
        ret = False
     
    return ret

def prompt_approval(stage):
    """ Endpoint called from the slave task to wait for API approval message """
    anvil.server.task['Waiting'] = True
    anvil.server.task['Stage'] = stage
    anvil.server.task['Approval'] = None
    return

@authenticated_callable
def approve_stage(stage, approval=True):
    """ Approve the Stage Deliverable """
    ret: str = "OK"
    if  anvil.server.task['Waiting'] and stage == anvil.server.task['stage']:
        anvil.server.task['Approval'] = approval
    else:
        # Do nothing!
        ret = f"Error: task is not waiting for {stage} approval"
    return ret

@authenticated_callable
def get_logs(max=100):
    """ Retrieve new log messages since the last call """
    # TODO: how to get a handle on the log output
    pass

@authenticated_callable
def get_deliverable(stage: str):
    """ Retrieve new deliverable document for the specified stage"""
    # TODO: use the Team object to get the required ActionOutput and file
    pass

@authenticated_callable
def update_deliverable(stage: str, deliverable):
    """ Retrieve new deliverable document for the specified stage"""
    # TODO: use the Team object to save the file in the correct location with the correct filename
    pass

@authenticated_callable
def get_status():
    """ Retrieve the running status of the main event loop """
    return check_status()


if __name__ == "__main__":
    anvil.server.connect("your-anvil-app-id")
    while True:
        check_status()
        t.sleep(60)         