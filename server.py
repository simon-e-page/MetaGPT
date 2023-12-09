#!/usr/bin/env python
# -*- coding: utf-8 -*-
import anvil.server
from anvil.media import BlobMedia
import asyncio

from startup import startup
from metagpt.team import Team
import time as t
import os
import traceback

# TODO: configure Config from frontend
# TODO: set git settings on workspaces / projects

company: Team = None
task = None
status: str = "Idle"

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
def create_project(product_name: str, project_data: dict):
    # TODO: take this out of the Team structure..
    global company
    if company is None:
        company = Team()
    idea: str = project_data['IDEA']
    company.create_project(product_name, idea)

@authenticated_callable
def download_project(product_name: str) -> bytes:
    # TODO: take this out of the Team structure..
    global company
    if company is None:
        company = Team()

    zipfile: bytes = company.download_project(product_name)
    if zipfile is not None:
        media_obj = BlobMedia('application/zip', zipfile, f"{product_name}.zip")
    else:
        media_obj = None
    return media_obj


def check_status():
    global task, status, error
    if task is not None:
        # TODO: interrogate running status - Excamples
        if not task.is_running():
            if task.get_termination_status() == 'completed':
                status = "Idle"
                error = None
            else:
                status = "Error"
                error = task.get_error()
            task = None
        else:
            if task.get_state()['Waiting']:
                return "Waiting"
            else:
                status = task.get_state()['stage']
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
    ) -> str:
    
    # TODO: how to return a handle for the Team object that is created?
    global company, task
    
    if company is None:
        return "Error! Company not initiated!"

    if task is None:
        try:
            company = startup(
                product_name=product_name,
                investment=investment, 
                n_round=n_round,
                code_review=code_review,
                run_tests=run_tests,
                implement=implement,
                stage=stage
                )
        except FileNotFoundError:
            ret = "Error: Call Create Project first!"
            return ret

        task = anvil.server.launch_background_task('run_project_background' , n_round)
        check_status()
        ret = "OK"
    else:
        ret = "Error: Already running!"
     
    return ret

def prompt_approval(action: str, stage: str):
    """ Endpoint called from the slave task to wait for API approval message or advance to next stage"""
    if action == 'approve':
        anvil.server.task['Waiting'] = True
        anvil.server.task['Stage'] = stage
        anvil.server.task['Approval'] = None
    elif action == 'advance':
        anvil.server.task['Waiting'] = False
        anvil.server.task['Stage'] = stage
        anvil.server.task['Approval'] = None
    elif action == "check":
        return anvil.server.task['Approval']
    else:
        # Unknown action
        pass
    return


@authenticated_callable
def approve_stage(stage, approval=True) -> str:
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
def get_deliverable(stage: str) -> str:
    """ Retrieve new deliverable document for the specified stage"""
    if  anvil.server.task['Waiting'] and stage == anvil.server.task['stage']:
        content = company.get_deliverable(stage)
    else:
        content = "Error: No content for this stage available!"
    return content

@authenticated_callable
def update_deliverable(stage: str, content: str) -> str:
    """ Retrieve new deliverable document for the specified stage"""
    if  anvil.server.task['Waiting'] and stage == anvil.server.task['stage']:
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
        check_status()
        t.sleep(60)         