#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : simonpage
@File    : jbteam.py
"""
import os
import traceback
import zipfile
import io
import re
from typing import Callable
from pathlib import Path
import yaml
import ast
from pydantic import BaseModel, Field, PrivateAttr

from metagpt.actions import BossRequirement, AdvanceStage, ManagementAction, WriteJBCode, WriteJBPRD, WriteProductApproval, WriteJBDesign, WriteDesignApproval, WriteJBTasks, WriteTaskApproval, WriteCodeReview
from metagpt.config import CONFIG
from metagpt.product_config import PRODUCT_CONFIG
import metagpt.const as CONST
from metagpt.environment import Environment
from metagpt.logs import logger
from metagpt.roles import Role, JBProductManager, JBProductApprover, JBArchitect, JBDesignApprover, JBProjectManager, JBTaskApprover, JBEngineer, JBQaEngineer, JBStageGovernance
from metagpt.schema import Message
from metagpt.utils.common import NoMoneyException
from metagpt.utils.jb_common import ApprovalError, ProductConfigError
from metagpt.utils.serialize import serialize_message, deserialize_message

STAGE_LIST = [ "Requirements", "Design", "Plan", "Build", "Test"]

STAGES: dict = { "Requirements": 0,
                 "Design": 1,
                 "Plan": 2,
                 "Build": 3,
                 "Test": 4
                }

STAGE_ACTIONS = {
    'Requirements': [BossRequirement],
    'Design': [BossRequirement, WriteJBPRD],
    'Plan': [BossRequirement, WriteJBPRD, WriteProductApproval, WriteJBDesign],
    'Build': [BossRequirement, WriteJBPRD, WriteProductApproval, WriteJBDesign, WriteDesignApproval, WriteJBTasks],
    'Test': [BossRequirement, WriteJBPRD, WriteProductApproval, WriteJBDesign, WriteDesignApproval, WriteJBTasks, WriteTaskApproval, WriteJBCode, WriteCodeReview],
}

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
    "Requirements": [ JBProductManager, JBProductApprover, JBStageGovernance, JBArchitect, JBDesignApprover, JBProjectManager, JBTaskApprover, JBEngineer, JBQaEngineer],
    "Design": [ JBProductApprover, JBStageGovernance, JBArchitect, JBDesignApprover, JBProjectManager, JBTaskApprover, JBEngineer, JBQaEngineer ],
    "Plan": [ JBDesignApprover, JBStageGovernance, JBProjectManager, JBTaskApprover, JBEngineer, JBQaEngineer ],
    "Build": [ JBTaskApprover, JBStageGovernance,JBEngineer, JBQaEngineer ],
    "Test": [ JBEngineer, JBStageGovernance, JBQaEngineer ],
}


class Team(BaseModel):
    """
    Team: Possesses one or more roles (agents), SOP (Standard Operating Procedures), and a platform for instant messaging,
    dedicated to perform any multi-agent activity, such as collaboratively writing executable code.
    """

    product_name: str
    environment: Environment = Field(default_factory=Environment)
    investment: float = Field(default=10.0)
    idea: str = Field(default="")
    _stage_callback: Callable = PrivateAttr(None)
    _bench: dict = PrivateAttr({})
    _log_stream: bool = PrivateAttr(False)
    
    class Config:
        arbitrary_types_allowed = True

    
    @classmethod
    def generate_folder_name(cls, email) -> str:
        # Replace @ with __at__
        cleaned_email = re.sub(r'@', '__at__', email)
        # Remove invalid characters from the email address
        cleaned_email = re.sub(r'[^\w.-]', '', cleaned_email)
        # Replace dots with underscores
        folder_name = re.sub(r'[.]+', '_', cleaned_email)
        return folder_name

    @classmethod
    def download_project(cls, email: str, product_name: str) -> bytes:
        """Create a zip file of the project directory into a bytes object and return it."""

        _base_dir: Path = Path(CONFIG.workspace_root) / cls.generate_folder_name(email) / product_name
        
        zip_file_bytes = io.BytesIO()
        cwd = os.getcwd()
        if _base_dir.exists():
            os.chdir(_base_dir)
            with zipfile.ZipFile(zip_file_bytes, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk("."):
                    for file in files:
                        zipf.write(os.path.join(root, file))
            os.chdir(cwd)
            ret = zip_file_bytes.getvalue()
        else:
            ret = None
        return ret

    @classmethod
    def reset_project(cls, email: str, product_name: str) -> None:
        """Remove all files/dirs except the Product Config"""

        _base_dir: Path = Path(CONFIG.workspace_root) / cls.generate_folder_name(email) / product_name

        if not _base_dir.exists():
            return

        _current_config: dict = cls.get_product_config(email=email, product_name=product_name)
        
        for root, dirs, files in os.walk(_base_dir, topdown=False):
            for file in files:
                file_path: str = os.path.join(root, file)
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Error deleting file: {file_path} - {e}")

            for dir_name in dirs:
                dir_path: str = os.path.join(root, dir_name)
                try:
                    os.rmdir(dir_path)
                except Exception as e:
                    logger.warning(f"Error deleting directory: {dir_path} - {e}")

        os.makedirs(_base_dir, exist_ok=True)
        _current_config['STAGE'] = 'Requirements'
        cls.save_product_config_to_file(email=email, product_name=product_name, config=_current_config)



    @classmethod
    def get_product_config(cls, email: str, product_name: str) -> dict:    
        _base: dict = {
            'IDEA': 'Make a simple web application that displays Hello World',
            'STAGE': 'Requirements'
        }
        
        _yaml_file: Path = Path(CONFIG.workspace_root) / cls.generate_folder_name(email) / product_name / "product.yaml"

        if not _yaml_file.exists():
            logger.warning(f"No config found at {_yaml_file}!")
            return _base
        
        with open(_yaml_file, "r", encoding="utf-8") as file:
            yaml_data = yaml.safe_load(file)
            if yaml_data:               
                _base.update(yaml_data)
            else:
                raise ProductConfigError(f"No valid product config found at {_yaml_file}")
        return _base

    @classmethod
    def update_project(cls, email: str, product_name: str, idea: str):
        _base_dir: Path = Path(CONFIG.workspace_root) / cls.generate_folder_name(email) / product_name
        if _base_dir.exists():
            existing = cls.get_product_config(email, product_name)
            existing['IDEA'] = idea
            cls.save_product_config_to_file(email=email, product_name=product_name, config=existing)

    @classmethod
    def save_product_config_to_file(cls, email: str, product_name: str, config: dict):
        _base_dir: Path = Path(CONFIG.workspace_root) / cls.generate_folder_name(email) / product_name
        _yaml_file: Path = _base_dir / "product.yaml"
        if _base_dir.exists():
            with open(_yaml_file, "w", encoding="utf-8") as file:
                yaml.safe_dump(config, file)

    @classmethod
    def get_project_list(cls, email: str) -> list:
        projects: list = []
        path: Path = Path(CONFIG.workspace_root) / cls.generate_folder_name(email)
        if path.exists():
            for i in path.iterdir():
                if i.is_dir():
                    try:
                        entry: dict = cls.get_product_config(email=email, product_name=i.name)
                        entry['NAME'] = i.name
                        projects.append(entry)
                    except ProductConfigError:
                        logger.warning(f"Invalid product config: {i.name}")
        return projects

    @classmethod
    def create_project(cls, email: str, product_name: str, idea: str, stage='Requirements'):
        _base_dir: Path = Path(CONFIG.workspace_root) / cls.generate_folder_name(email) / product_name

        _base: dict = {
            'IDEA': idea,
            'STAGE': stage
        }

        ret = True
        try:
            os.makedirs(_base_dir)
        except OSError:
            logger.warning("Project already exists!")
            ret = False
            
        if ret:
            cls.save_product_config_to_file(email, product_name, _base)
        return ret


        
    def hire(self, roles: list[Role]):
        """Hire roles to cooperate"""
        role_names = [ x.profile for x in roles ]
        logger.info(f"Including the following roles: {','.join(role_names)}")
        self.environment.add_roles(roles)

    def dehire(self, profiles: list) -> None:
        """ Remove a role from the environment based on its profile string"""
        # TODO: better to be done in the environment object?
        env_roles: dict = self.environment.roles
        for profile in profiles:
            if profile in env_roles.keys():
                del env_roles[profile]

    def invest(self, investment: float):
        """Invest company. raise NoMoneyException when exceed max_budget."""
        self.investment = investment
        CONFIG.max_budget = investment
        logger.info(f'Investment: ${investment}.')

    def get_balance(self) -> float:
        return CONFIG.total_cost

    def _check_balance(self):
        if CONFIG.total_cost > CONFIG.max_budget:
            raise NoMoneyException(CONFIG.total_cost, f'Insufficient funds: {CONFIG.max_budget}')

    def get_messages(self, k=0) -> list:
        msgs: list = self.environment.memory.get(k)
        return msgs
    
    def _map_stage_to_deliverable(self, stage: str) -> Path:
        """ sets out deliverables for each stage """
        DELIVERABLE_MAP = {
            "Requirements": { 'name': 'prd',               'path': PRODUCT_CONFIG.product_root / "docs" / "prd.md" },
            "Design":       { 'name': 'design',            'path': PRODUCT_CONFIG.product_root / "docs" / "system_design.md" },
            "Plan":         { 'name': 'tasks',             'path': PRODUCT_CONFIG.product_root / "docs" / "api_spec_and_tasks.md" },
            "Build":        { 'name': 'code_review',       'path': WriteJBCode },
            "Test":         { 'name': 'test_build_report', 'path': None },

        }
        return DELIVERABLE_MAP.get(stage, None)
    
    def get_deliverable(self, stage: str) -> str:
        path = self._map_stage_to_deliverable(stage)['path']
        name: str = self._map_stage_to_deliverable(stage)['name']
        content = None

        if isinstance(path, Path):
            try:
                content = path.read_text()
            except FileNotFoundError:
                logger.warning(f"Can't find deliverable: {path}")
        
        elif path is not None:
            memories = self.environment.memory.get_by_actions([path])
            content = { x.role: x.content for x in memories }
        else:
            logger.warning(f"No deliverable defined for stage {stage}")
        
        return { name: content }

    def update_deliverable(self, stage: str, content: str) -> str:
        path: Path = self._map_stage_to_deliverable(stage)['path']
        if isinstance(path, Path):
            try:
                content = path.write_text(content, encoding='utf-8')
                ret = "OK"
            except FileNotFoundError:
                logger.warning(f"Can't find deliverable: {path}")
                ret = "Error"
        else:
            logger.warning(f"No deliverable defined for stage {stage}")
            ret = "Error"
        return ret

    def create_product_config(self, idea, stage):
        data = {
            'IDEA': idea,
            'STAGE': stage
        }

        PRODUCT_CONFIG.product_config = yaml.dump(data)
        self.save_product_config()
        
    def save_product_config(self):
        self.save_product_config_to_file(PRODUCT_CONFIG.email, self.product_name, PRODUCT_CONFIG.product_config)

    def load_product_config(self, email: str) -> None:
        # First set CONFIG object up
        # TODO: implement in __init__?
        PRODUCT_CONFIG.email = email
        PRODUCT_CONFIG.product_name = self.product_name
        PRODUCT_CONFIG.product_root = Path(CONFIG.workspace_root) / self.generate_folder_name(email) / self.product_name

        if not os.path.exists(PRODUCT_CONFIG.product_root):
            raise FileNotFoundError(f"Need following directory with product config to start: {PRODUCT_CONFIG.product_root}")

        PRODUCT_CONFIG.set_product_config(self.get_product_config(email, self.product_name))
        
    def get_project(self) -> dict:
        deliverables: dict = PRODUCT_CONFIG.product_config.copy()
        deliverables['NAME'] = PRODUCT_CONFIG.product_name

        history_file: Path = PRODUCT_CONFIG.product_root / "history.pickle"
        if history_file.exists():
            self.set_memory('Test')
            for stage in ['Requirements', 'Design', 'Plan', 'Build', 'Test']:
                deliverables.update(self.get_deliverable(stage))

        return deliverables


    def start_project(self, product_name: str, stage: str = "Requirements", send_to: str = "", end_stage="Requirements"):
        """Start a project from the start or a specific stage (assuming prior stages have been run)"""
        logger.info(f'Starting project: {product_name}')
        PRODUCT_CONFIG.stage = stage
        PRODUCT_CONFIG.end_stage = end_stage
        logger.info(f'For product {product_name} we are commencing stage: {stage}')

    

    def _save(self):
        logger.info(self.json())


    def filter_messages(self, messages, keep: list):
        """ Strips all messages that are not in the list of specific actions"""
        messages = [ m for m in messages if m.cause_by in keep ]
        return messages
        

    def set_memory(self, stage: str=None):
        """ Resets Memory of Roles and Environment to a specific stage. 
            If None then continues from last run
        """

        ret = False
        
        if stage is None:
            # Setting to the last stage means we dont remove any memories
            stage = "Test"

        logger.info("Clearing all memory to reset history")
        self.environment.memory.clear()
        for name, role in self.environment.get_roles().items():
            role._rc.memory.clear()
        
        history_file: Path = PRODUCT_CONFIG.product_root / "history.pickle"
        if history_file.exists():
            logger.info(f"Loading messages from a previous execution and replaying up to {stage}!")
            messages = deserialize_batch(history_file.read_bytes())
            messages = self.filter_messages(messages, STAGE_ACTIONS[stage])
            logger.info(f"Publishing {len(messages)} messages to the environment")
            self.environment.memory.add_batch(messages)

            # Only the approver roles should see a new message in the environment to kick off proceedings
            for name, role in self.environment.get_roles().items():
                if type(role) not in APPROVERS[stage]:
                    logger.info(f"And including fast forward memory recall for {name}")
                    for message in messages:
                        role.recv(message)
            ret = True
        
        return ret
    
    def set_stage_callback(self, callback: Callable) -> None:
        self._stage_callback = callback

    def set_log_output(self, stream) -> None:
        """ Handler to direct log output to a stream (for API retrieval)"""
        # Only do once!
        logger.info(f"Attempting to add a log stream with current value: {self._log_stream}")
        if not self._log_stream:
            logger.add(stream, level="INFO")
            self._log_stream = True
        
    def get_previous_stage(self, current_stage: str) -> str:
        stage_num: int = STAGES[current_stage]
        if stage_num > 0:
            new_stage: str = STAGE_LIST[stage_num-1]
        else:
            new_stage = None
        return new_stage
    
    def scan_advances(self, current_stage: str) -> str:
        advances = self.environment.memory.get_by_action(AdvanceStage)
        stage_num: int = STAGES[current_stage]
        new_stage: str = current_stage

        for m in advances:
            temp_stage: str = m.instruct_content.dict()['Advance Stage']
            temp_stage_num: int = STAGES[temp_stage]

            if temp_stage_num > stage_num:
                new_stage = temp_stage

        return new_stage         

    def set_team(self, end_stage):
        if len(self._bench)>0:
            self.environment.add_roles(self._bench.values())
            self._bench = {}

        remove = []
        for name, role in self.environment.get_roles().items():
            self._bench[name] = role
            if type(role) not in STAGE_TEAM[end_stage]:
                remove.append(name)
            else:
                logger.info(f"Confirming {name} in the team for this execution")

        for name in remove:
            del self.environment.get_roles()[name]

    async def run(self, n_round=3, start_stage="Requirements", end_stage="Requirements"):
        """Run company until target stage or no money"""

        current_stage: str = start_stage
        self.set_team(end_stage)
        
        if self.set_memory(start_stage):
            prev_stage = self.get_previous_stage(start_stage)
            
            while prev_stage is not None:
                self.environment.publish_message(Message(role="Human", content=f"AUTO-APPROVE: {prev_stage}", cause_by=ManagementAction, send_to=""))
                prev_stage = self.get_previous_stage(prev_stage)
                
        else:
            logger.info("Commencing project with Boss Requirement")
            self.environment.publish_message(Message(role="Human", content=PRODUCT_CONFIG.idea, cause_by=BossRequirement, send_to=""))


        logger.info(f"Team will execute rounds of Tasks unless they finish the {end_stage} stage or run out of Investment funds!")

        if self._stage_callback is not None:
            self._stage_callback(stage=current_stage)

        n_round = 3
        while n_round>0 and (STAGES[end_stage] >= STAGES[current_stage]):
            logger.info(f"Working on stage: {current_stage}")
            start_msgs: int = len(self.environment.memory.get())

            try:
                self._check_balance()
                await self.environment.run()
            except NoMoneyException as e:
                logger.error("Ran out of money! Cannot continue!")
                logger.error(f"Total spent: {e.amount} out of {CONFIG.max_budget}")
                n_round = 0
            except ApprovalError as e:
                logger.error(f"Approval not given by {e.approver}")
                role = self.environment.get_role(e.approver)
                if role is not None:
                    logger.warning(f"Clearing memory for {e.approver}")
                    role._rc.memory.clear()
                else:
                    logger.error(f"Could not find an active role with profile={e.approver}. Should not happen!")
                n_round = 0
            except Exception:
                logger.error("Uncaught Exception!")
                logger.error(traceback.format_exc())
                n_round = 0
            
            end_msgs: int = len(self.environment.memory.get())
                
            new_stage: str = self.scan_advances(current_stage)
            if new_stage != current_stage:
                logger.info(f"Execution advanced to {new_stage} stage!")

                if self._stage_callback is not None:
                    self._stage_callback(stage=new_stage)
                current_stage = new_stage

            elif start_msgs == end_msgs:
                logger.warning("No action taken during round! Aborting after three rounds!")
                n_round -= 1
            
        history_file = PRODUCT_CONFIG.product_root / "history.pickle"
        with open(history_file, 'wb') as file:
            file.write(serialize_batch(self.environment.memory.get()))
        
        self.save_product_config()
        logger.info("Team execution completed!")
        return self.environment.history
    
# Not probably the best wayy to do this!
# But the underlying serialize module only handles one message at a time

def serialize_batch(messages: list) -> str: 
    """ Takes a list of messages and returns a string representation of a list of pickle objects """
    msg_ser = [ serialize_message(x) for x in messages ]
    return str(msg_ser)

def deserialize_batch(message_set: str) -> list:
    """ Takes a string representation of a list of pickle objects and returns a list of messages """
    x = ast.literal_eval(message_set)
    messages = [ deserialize_message(m) for m in x ] 
    return messages
