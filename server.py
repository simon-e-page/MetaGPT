#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import time as t
import os
from io import StringIO
import traceback
from typing import Callable
from concurrent.futures import ThreadPoolExecutor

import anvil.server
from anvil import BlobMedia

from metagpt.jbteam import Team
from metagpt.roles import (
    Architect,
    Engineer,
    ProductManager,
    ProjectManager,
    DesignApprover,
    ProductApprover,
    TaskApprover,
    QaEngineer,
    StageGovernance,
)


# TODO: configure Config from frontend
# TODO: set git settings on workspaces / projects

company: Team = None
task = None
executor = ThreadPoolExecutor(max_workers=1)
task_state = {}

class LogSink:
    """ Helper class to act as an internal log sink and replay messages to the client
        Expect that we pull from the cache in batches until no lines are left.
        Returns an empty list if there are no new log entries
    """
    def __init__(self):
        self.stream = StringIO()
        self.position = self.stream.tell()
        self.cache = []

    def get_lines(self, max_lines=100) -> tuple:
        """ Returns lines from the stream up to max and a flag True if there is more to retrieve """
        self._tail()
        if len(self.cache) <= max_lines:
            ret = self.cache
            more = False
            self.cache = []
        else:
            ret = self.cache[0:max_lines]
            self.cache = self.cache[max_lines:]
            more = True
        return ret, more
            
    def _tail(self) -> str:
        """ Returns new text from the stream and adds to the cache"""
        self.stream.seek(self.position)
        new_data = self.stream.read()
        if new_data:
            self.position = self.stream.tell()
            self.cache += new_data.splitlines()

        
log_stream = LogSink()

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
        if task_state.get('Waiting', False):
            stage = task_state.get('stage', "Requirements")
            status = "Waiting"
        elif task.running():
            stage = task_state.get('stage', "Requirements")
            status = "Runnimg"
        else:
            if task.done():
                try:
                    result = task.result()
                    print(result)
                    status = "Idle"
                except Exception:
                    traceback.print_exc()
                    status = "Idle"
                    error = traceback.format_exc()
                    status = "Idle"
                task = None
    else:
        status = "Idle"
    return (status, stage, error)

def run_project_background(n_round: int = 5,
                           start_stage: str = "Requirements",
                           end_stage:str = "Requirements"
                           ) -> str:

    """ Child thread main task launcher """
    history: str = asyncio.run(company.run(n_round=n_round, start_stage=start_stage, end_stage=end_stage))
    return history

@authenticated_callable
def run_project(
    product_name, 
    investment=5.0, 
    stage="Requirements",
    end_stage="Requirements"
    ) -> str:

    """ Main execution launcher """
    
    global task
    
    if company is None:
        return "Error! Company not initiated!"

    if task is None:
        try:
            n_round = startup(
                product_name=product_name,
                investment=investment, 
                stage=stage,
                end_stage=end_stage
                )
        except FileNotFoundError:
            ret = "Error: Call Create Project first!"
            return ret

        task = executor.submit(run_project_background, n_round, start_stage=stage, end_stage=end_stage)
        check_status()
        ret = "OK"
    else:
        ret = "Error: Already running!"
     
    return ret

def update_stage(stage: str):
    """ Called by child thread with current stage being worked on"""
    task_state['stage'] = stage


def startup(
    product_name, 
    investment=5.0, 
    stage="Requirements",
    end_stage = "Requirements"        
) -> int:
    
    api_callback: Callable = prompt_approval

    company.invest(investment)
    company.start_project(product_name, stage=stage, end_stage=end_stage)
    company.set_stage_callback(update_stage)
    company.set_log_output(log_stream.stream)

    company.hire(
        [
            ProductManager(),
            Architect(),
            ProjectManager(),
            DesignApprover(callback = api_callback),
            ProductApprover(callback = api_callback),
            TaskApprover(callback = api_callback),
            StageGovernance()
        ]
    )

    # n_round is now ignored!
    n_round = 2

    if end_stage == "Design":
        n_round = 4

    # if implement or code_review
    if end_stage == 'Build':
        # developing features: implement the idea
        company.hire([Engineer(n_borg=5, use_code_review=True)])
        n_round = 6

    if end_stage == 'Test':
        # developing features: run tests on the spot and identify bugs
        # (bug fixing capability comes soon!)
        company.hire([Engineer(n_borg=5, use_code_review=True), QaEngineer()])
        n_round = 7
    
    return n_round


# This function is called from the background task!
def prompt_approval(action: str, stage: str):
    """ Endpoint called from the child task to wait for API approval message or advance to next stage"""

    if action == 'approve':
        print(f"Child: Submitting approval request for {stage}")
        task_state['Waiting'] = True
        task_state['Stage'] = stage
        task_state['Approval'] = None
        ret = None
    elif action == 'advance':
        print(f"Child: Signalling advance to {stage}")
        task_state['Waiting'] = False
        task_state['Stage'] = stage
        task_state['Approval'] = None
        ret = None
    elif action == "check":
        print(f"Child: Looking for approval response for {stage}")
        approval = task_state['Approval']
        if approval is not None:
            print(f"Child: Got approval response of: {approval}")
            task_state['Waiting'] = False
        ret = approval
    else:
        # Unknown action
        pass
    return ret


@authenticated_callable
def approve_stage(stage, approval=None) -> str:
    """ Approve the Stage Deliverable """
    ret: str = "OK"

    if task_state is None or task_state.get('Waiting'):
        print(f"Got approval message for {stage}")
        task_state['Approval'] = approval
    else:
        # Do nothing!
        ret = f"Error: task is not waiting for {stage} approval"
    return ret

@authenticated_callable
def get_logs(max_lines=100) -> tuple:
    """ Retrieve new log messages since the last call """
    return log_stream.get_lines(max_lines)


@authenticated_callable
def get_deliverable(stage: str) -> str:
    """ Retrieve new deliverable document for the specified stage"""

    if  task_state.get('Waiting', False) and stage == task_state.get('stage', "Requirements"):
        print(f"Retrieving deliverable for {stage}")
        content = company.get_deliverable(stage)
    else:
        content = "Error: No content for this stage available!"
    return content

@authenticated_callable
def update_deliverable(stage: str, content: str) -> str:
    """ Retrieve new deliverable document for the specified stage"""

    if  task_state.get('Waiting', False) and stage == task_state.get('stage', "Requirements"):
        print(f"Updating approved deliverable for {stage}")
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