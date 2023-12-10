#!/usr/bin/env python
# -*- coding: utf-8 -*-
import anvil.server
from anvil import BlobMedia
import asyncio
import time as t
import os
import traceback
from typing import Callable

from metagpt.team import Team
from metagpt.roles import (
    Architect,
    Engineer,
    ProductManager,
    ProjectManager,
    DesignApprover,
    ProductApprover,
    TaskApprover,
    QaEngineer,
)


# TODO: configure Config from frontend
# TODO: set git settings on workspaces / projects

company: Team = None
task = None

# TODO: add auth to the frontend
#authenticated_callable = anvil.server.callable(require_user=True)
authenticated_callable = anvil.server.callable()

@authenticated_callable
def get_projects() -> list:
    """ Retrieve existing projects and return a list of names"""
    global company
    if company is None:
        company = Team()
    projects: str = company.get_projects()
    return projects


@authenticated_callable
def get_project(product_name: str) -> str:
    """ Retrieve an existing project and return the Idea, or None if it doesnt exist"""
    global company
    if company is None:
        company = Team()
    try:
        idea: str = company.get_project(product_name)
    except Exception:
        traceback.print_exc()
        idea = None
    return idea
    
@authenticated_callable
def update_project(product_name: str, project_data: dict):
    # TODO: take this out of the Team structure..
    global company
    if company is None:
        company = Team()
    idea: str = project_data['IDEA']
    company.update_project(product_name, idea)


@authenticated_callable
def create_project(product_name: str, project_data: dict) -> bool:
    # TODO: take this out of the Team structure..
    global company
    if company is None:
        company = Team()
    idea: str = project_data['IDEA']
    return company.create_project(product_name, idea)

@authenticated_callable
def download_project(product_name: str) -> bytes:
    # TODO: take this out of the Team structure..
    global company
    if company is None:
        company = Team()

    zipfile = None
    try:
        zipfile: bytes = company.download_project(product_name)
    except Exception:
        traceback.print_exc()

    if zipfile is not None:
        media_obj = BlobMedia('application/zip', zipfile, f"{product_name}.zip")
    else:
        media_obj = None
    return media_obj


def check_status() -> tuple:
    global task
    stage: str = ""
    error: str = ""
    stage: str = ""
    if task is not None:
        if task.get_state() is None:
            # This seems to be the case when the child process sleeps..
            status = "Waiting"
        elif task.get_state().get('Waiting', False):
            stage = task.get_state().get('stage', "Requirements")
            status = "Waiting"
        elif task.is_running():
            stage = task.get_state().get('stage', "Requirements")
            status = "Runnimg"
        else:
            if task.get_termination_status() == 'completed':
                status = "Idle"
            else:
                status = "Error"
                error = task.get_error()
                print(f"Found error: {error}")
            task = None
    else:
        status = "Idle"
    return (status, stage, error)

@anvil.server.background_task
def run_project_background(n_round: int = 5) -> str:
    history: str = asyncio.run(company.run(n_round=n_round))
    return history

@authenticated_callable
def run_project(
    product_name, 
    investment=5.0, 
    stage="Requirements"
    ) -> str:
    
    # TODO: how to return a handle for the Team object that is created?
    global company, task
    
    if company is None:
        return "Error! Company not initiated!"

    if task is None:
        try:
            n_round = startup(
                product_name=product_name,
                investment=investment, 
                stage=stage
                )
        except FileNotFoundError:
            ret = "Error: Call Create Project first!"
            return ret

        task = anvil.server.launch_background_task('run_project_background' , n_round)
        task.get_state()['stage'] =  stage
        check_status()
        ret = "OK"
    else:
        ret = "Error: Already running!"
     
    return ret

def startup(
    product_name, 
    investment=5.0, 
    stage="Requirements"        
) -> int:
    
    global company

    api_callback: Callable = prompt_approval

    company = Team()
    company.invest(investment)
    company.start_project(product_name, stage)

    company.hire(
        [
            ProductManager(),
            Architect(),
            ProjectManager(),
            DesignApprover(),
            ProductApprover(callback = api_callback),
            TaskApprover()
        ]
    )

    n_round = 2

    if stage == "Design":
        n_round = 4

    # if implement or code_review
    if stage == 'Build':
        # developing features: implement the idea
        company.hire([Engineer(n_borg=5, use_code_review=True)])
        n_round = 6

    if stage == 'Test':
        # developing features: run tests on the spot and identify bugs
        # (bug fixing capability comes soon!)
        company.hire([Engineer(n_borg=5, use_code_review=True), QaEngineer()])
        n_round = 7
    
    return n_round


# This function is called from the background task!
def prompt_approval(action: str, stage: str):
    """ Endpoint called from the slave task to wait for API approval message or advance to next stage"""
    if action == 'approve':
        print(f"Submitting approval request for {stage}")
        anvil.server.task_state['Waiting'] = True
        anvil.server.task_state['Stage'] = stage
        anvil.server.task_state['Approval'] = None
    elif action == 'advance':
        print(f"Signalling advance to {stage}")
        anvil.server.task_state['Waiting'] = False
        anvil.server.task_state['Stage'] = stage
        anvil.server.task_state['Approval'] = None
    elif action == "check":
        #print(f"Looking for approval response for {stage}")
        return anvil.server.task_state['Approval']
    else:
        # Unknown action
        pass
    return


@authenticated_callable
def approve_stage(stage, approval=True) -> str:
    """ Approve the Stage Deliverable """
    ret: str = "OK"
    if task.get_state() is None or task.get_state().get('Waiting'):
        print(f"Got approval message for {stage}")
        task.get_state()['Approval'] = approval
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
def get_deliverable(stage: str) -> str:
    """ Retrieve new deliverable document for the specified stage"""
    if  task.get_state().get('Waiting', False) and stage == task.get_state().get('stage', "Requirements"):
        content = company.get_deliverable(stage)
    else:
        content = "Error: No content for this stage available!"
    return content

@authenticated_callable
def update_deliverable(stage: str, content: str) -> str:
    """ Retrieve new deliverable document for the specified stage"""
    if  task.get_state().get('Waiting', False) and stage == task.get_state().get('stage', "Requirements"):
        ret: str = company.update_deliverable(stage, content)
    else:
        ret = f"Error: Cannot update content for {stage} right now!"
    return ret

@authenticated_callable
def get_status():
    """ Retrieve the running status of the main event loop """
    return check_status()


if __name__ == "__main__":
    anvil_id = os.environ.get("ANVIL_APP_ID", None)
    if anvil_id:
        try:
            anvil.server.connect(anvil_id)
        except Exception:
            print("Could not connect to Anvil!")
            traceback.print_exc()
            exit(1)
    else:
        print("Please set your Anvil Application ID in the environment variable ANVIL_APP_ID")
        exit(1)

    while True:
        print(check_status())
        t.sleep(60)         