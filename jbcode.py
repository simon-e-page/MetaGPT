#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import time as t
import os
import fire
from io import StringIO
import traceback
from typing import Callable
from concurrent.futures import ThreadPoolExecutor

import anvil.server
from anvil import BlobMedia

from metagpt.jbteam import Team
from metagpt.roles import (
    JBArchitect,
    JBEngineer,
    JBProductManager,
    JBProjectManager,
    JBDesignApprover,
    JBProductApprover,
    JBTaskApprover,
    JBQaEngineer,
    JBStageGovernance,
)


# TODO: configure Config from frontend
# TODO: set git settings on workspaces / projects
# TODO: scan project memory when loading for previously created deliverables

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
    return Team.get_project_list()

@authenticated_callable
def get_project(product_name: str, use_callback=True) -> dict:
    """ Retrieve an existing project and returns a dict of already completed stages and deliverables
        Returns None if it doesnt exist
    """
    
    global company
    if task is not None:
        print("Project running!")
        return None

    if use_callback:
        api_callback: Callable = prompt_approval
    else:
        api_callback = None
    
    try:
        company = Team(product_name=product_name)
        company.load_product_config()
        company.hire(
            [
                JBProductManager(),
                JBArchitect(),
                JBProjectManager(),
                JBDesignApprover(callback = api_callback),
                JBProductApprover(callback = api_callback),
                JBTaskApprover(callback = api_callback),
                JBStageGovernance(),
                JBEngineer(n_borg=5, use_code_review=True),
                JBQaEngineer()
            ]
        )
        deliverables: dict = company.get_project()
    except Exception:
        traceback.print_exc()
        deliverables = None
    return deliverables
    
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
    status: str = ""

    if task is not None:
        if task_state.get('Waiting', False):
            stage = task_state.get('stage', "Requirements")
            status = "Waiting"
        elif task.running():
            stage = task_state.get('stage', "Requirements")
            status = "Runnimg"
        elif task.done():
            try:
                result = task.result()
                print("###############\nCompleted task output:\n#################\n")
                print(result)
                status = "Complete"
            except Exception:
                traceback.print_exc()
                status = "Idle"
                error = traceback.format_exc()
            task = None
        else:
            status = "Unknown!"
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
    product_name: str, 
    investment: float = 5.0,
    stage: str = "Requirements",
    end_stage: str = "Requirements",
    use_callback: bool = True
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
                end_stage=end_stage,
                use_callback=use_callback
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
    product_name: str, 
    investment: float = 5.0, 
    stage: str = "Requirements",
    end_stage: str = "Requirements",
    use_callback: bool = True
) -> int:
    
    company.invest(investment)
    company.start_project(product_name, stage=stage, end_stage=end_stage)
    company.set_stage_callback(update_stage)
    company.set_log_output(log_stream.stream)

    remove_list = []
    if end_stage not in ['Build', 'Test']:
        remove_list.append('Engineer')
    elif end_stage not in ['Test']:
        remove_list.append('QaEngineer')

    if len(remove_list)>0:
        company.dehire(remove_list)

    n_round = 2
    
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
        task_state['Waiting'] = False
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



def run_server():
    """ Runs an Anvil Server backend """
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


def main(
    server: bool = False,
    create: bool = False,
    list_projects: bool = False,
    product_name: str = '',
    idea: str = '',
    investment: float = 3.0,
    start_stage: str ='Requirements',
    end_stage: str ='Plan',
    n_round: int = 7,
):
    """
    We are a software startup comprised of AI. By investing in us,
    you are empowering a future filled with limitless possibilities.
    
    Usage:
    1) As a server:
    jbteamp.py --server 
    
    2) To create a new project from the command line:
    jbteam.py --create --product_name="<New product name>" --idea="<Initial prompt>"
    
    3) To list known projects from the command line:
    jbteam.py --list_projects
    
    3) To run a project from the command line:
    jbteam.py --product_name="<Product Name>" [--investment=n.n] [--start_stage="Requirements"] [--end_stage="Plan"]
    
    The defined stages are (in order): Requirements, Design, Plan, Build, Test
    
    :param server: Exceute as a server backend for an Anvil Frontend (needs ANVIL_APP_ID environment variable).
    :param create: Creates a new project
    :param list_projects: List known projects in the workspace
    :param product_name: The name of your product and key directory name in the workspace. 
    Make sure the directory WORKSPACE_ROOT/PRODUCT_NAME exists.
    Make sure that there is a file product.yaml in that directory with at least the IDEA and STAGE defined
    :param idea: Starting prompt to use
    :param investment: As an investor, you have the opportunity to contribute
    a certain dollar amount to this AI company.
    :param n_round: not used anymore
    :oaram start_stage: what stage to start the project. Overwrites any previous deliverables for later stages 
    :param end_stage: What stage to complete before finishing. Ends at an approved deliverable or code completion
    :return:
    """

    if server:
        run_server()
        
    elif create:
        assert len(product_name)>0
        assert len(idea)>0
        create_project(product_name=product_name, project_data={'IDEA': idea})

    elif list_projects:
        print("Current known projects:")
        for project in get_projects():
            print(f"{project['NAME']}: {project['IDEA']}")

    else:
        assert len(product_name)>0
        try:
            get_project(product_name)
            run_project(
                        product_name=product_name,
                        investment=investment,
                        n_round=n_round,
                        start_stage=start_stage,
                        end_stage=end_stage,
                        use_callback=False
                        )
        except Exception:
            traceback.print_exc()

    
if __name__ == "__main__":
    fire.Fire(main)


        
    