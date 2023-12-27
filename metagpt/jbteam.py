#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : alexanderwu
@File    : software_company.py
"""
import os
import traceback
import zipfile
import io
from typing import Callable
from pathlib import Path
import yaml
from pydantic import BaseModel, Field

from metagpt.actions import BossRequirement, AdvanceStage, ManagementAction, STAGE_ACTIONS, WriteJBCode
from metagpt.config import CONFIG
import metagpt.const as CONST
from metagpt.environment import Environment
from metagpt.logs import logger
from metagpt.roles import Role, STAGE_ROLES, STAGE_TEAM, APPROVERS
from metagpt.schema import Message
from metagpt.utils.common import NoMoneyException, ProductConfigError
from metagpt.utils.jb_common import ApprovalError
from metagpt.utils.serialize import serialize_batch, deserialize_batch



class Team(BaseModel):
    """
    Team: Possesses one or more roles (agents), SOP (Standard Operating Procedures), and a platform for instant messaging,
    dedicated to perform any multi-agent activity, such as collaboratively writing executable code.
    """

    product_name: str
    environment: Environment = Field(default_factory=Environment)
    investment: float = Field(default=10.0)
    idea: str = Field(default="")
    stage_callback: Callable = Field(default=None)
    bench: dict = Field(default={})
    
    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def download_project(cls, product_name: str) -> bytes:
        """Create a zip file of the project directory into a bytes object and return it."""

        _base_dir: Path = Path(CONFIG.workspace_root) / product_name
        
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
    def get_product_config(cls, product_name: str) -> dict:    
        _base: dict = {
            'IDEA': 'Make a simple web application that displays Hello World',
            'STAGE': 'Requirements'
        }
        
        _yaml_file: Path = Path(CONFIG.workspace_root) / product_name / "product.yaml"

        with open(_yaml_file, "r", encoding="utf-8") as file:
            yaml_data = yaml.safe_load(file)
            if yaml_data:               
                _base.update(yaml_data)
            else:
                raise ProductConfigError(f"No valid product config found at {_yaml_file}")
        return _base

    @classmethod
    def update_project(cls, product_name: str, idea: str):
        _base_dir: Path = Path(CONFIG.workspace_root) / product_name
        if _base_dir.exists():
            existing = cls.get_product_config(product_name)
            existing['IDEA'] = idea
            cls.save_product_config_to_file(product_name, existing)

    @classmethod
    def save_product_config_to_file(cls, product_name: str, config: dict):
        _base_dir: Path = Path(CONFIG.workspace_root) / product_name
        _yaml_file: Path = _base_dir / "product.yaml"
        if _base_dir.exists():
            with open(_yaml_file, "w", encoding="utf-8") as file:
                yaml.safe_dump(config, file)

    @classmethod
    def get_project_list(cls) -> list:
        projects: list = []
        path: Path = Path(CONFIG.workspace_root)
        for i in path.iterdir():
            if i.is_dir():
                try:
                    entry: dict = cls.get_product_config(i.name)
                    entry['NAME'] = i.name
                    projects.append(entry)
                except ProductConfigError:
                    logger.warning(f"Invalid product config: {i.name}")
        return projects

    @classmethod
    def create_project(cls, product_name: str, idea: str, stage='Requirements'):
        _base_dir: Path = Path(CONFIG.workspace_root) / product_name

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
            cls.save_product_config_to_file(product_name, _base)
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

    def _check_balance(self):
        if CONFIG.total_cost > CONFIG.max_budget:
            raise NoMoneyException(CONFIG.total_cost, f'Insufficient funds: {CONFIG.max_budget}')


    def _map_stage_to_deliverable(self, stage: str) -> Path:
        """ sets out deliverables for each stage """
        # TODO: extend to retrieval from the internal message history
        DELIVERABLE_MAP = {
            "Requirements": { 'name': 'prd',               'path': CONFIG.product_root / "docs" / "prd.md" },
            "Design":       { 'name': 'design',            'path': CONFIG.product_root / "docs" / "system_design.md" },
            "Plan":         { 'name': 'tasks',             'path': CONFIG.product_root / "docs" / "api_spec_and_tasks.md" },
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

        CONFIG.product_config = yaml.dump(data)
        self.save_product_config()
        
    def save_product_config(self):
        self.save_product_config_to_file(self.product_name, CONFIG.product_config)

    def load_product_config(self) -> None:
        # First set CONFIG object up
        # TODO: implement in __init__?
        CONFIG.product_name = self.product_name

        if not os.path.exists(CONFIG.product_root):
            raise FileNotFoundError(f"Need following directory with product config to start: {CONFIG.product_root}")

        CONFIG.set_product_config(self.get_product_config(self.product_name))
        
    def get_project(self) -> dict:
        deliverables: dict = {'Idea': CONFIG.idea}

        history_file = CONFIG.product_root / "history.pickle"
        if history_file.exists():
            self.set_memory('Test')
            for stage in ['Requirements', 'Design', 'Plan', 'Build', 'Test']:
                deliverables.update(self.get_deliverable(stage))

        return deliverables


    def start_project(self, product_name: str, stage: str = "Requirements", send_to: str = "", end_stage="Requirements"):
        """Start a project from the start or a specific stage (assuming prior stages have been run)"""
        logger.info(f'Starting project: {product_name}')

        #self.get_project()
        CONFIG.stage = stage
        CONFIG.end_stage = end_stage

        #add_project_log(CONFIG.product_root, replace=True)

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
        
        history_file: Path = CONFIG.product_root / "history.pickle"
        if history_file.exists():
            logger.info(f"Loading messages from a previous execution and replaying up to {stage}!")
            messages = deserialize_batch(history_file.read_bytes())
            messages = self.filter_messages(messages, STAGE_ACTIONS[stage])
            logger.info(f"Publishing {len(messages)} messages to the environment")
            news_text = [f"{i.role}: {i.content[:20]}..." for i in messages]
            logger.info(f'Replayed: {news_text}')
            self.environment.memory.add_batch(messages)

            # Only the approver roles should see a new message in the environment to kick off proceedings
            for role in self.environment.get_roles().values():
                if role in APPROVERS[stage]:
                    continue
                for message in messages:
                    role.recv(message)
            ret = True
        
        #for name, role in self.environment.get_roles().items():
        #    if type(role) not in STAGE_ROLES[stage]:
        #        logger.info(f"Clearing memory for {name}")
        #        role._rc.memory.clear()

        return ret
    
    def set_stage_callback(self, callback: Callable):
        self.stage_callback = callback

    def set_log_output(self, stream):
        logger.add(stream, level="INFO")
        
    def get_previous_stage(self, current_stage: str) -> str:
        stage_num: int = CONST.STAGES[current_stage]
        if stage_num > 0:
            new_stage: str = CONST.STAGE_LIST[stage_num-1]
        else:
            new_stage = None
        return new_stage
    
    def scan_advances(self, current_stage: str) -> str:
        advances = self.environment.memory.get_by_action(AdvanceStage)
        stage_num: int = CONST.STAGES[current_stage]
        new_stage: str = current_stage

        for m in advances:
            temp_stage: str = m.instruct_content.dict()['Advance Stage']
            temp_stage_num: int = CONST.STAGES[temp_stage]

            if temp_stage_num > stage_num:
                new_stage = temp_stage

        return new_stage         

    def set_team(self, end_stage):
        if len(self.bench)>0 is not None:
            self.environment.add_roles(self.bench.values())
            self.bench = {}

        remove = []
        for name, role in self.environment.get_roles().items():
            self.bench[name] = role
            if type(role) not in STAGE_TEAM[end_stage]:
                logger.info(f"Removing {name} from the team!")
                remove.append(name)

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
            self.environment.publish_message(Message(role="Human", content=CONFIG.idea, cause_by=BossRequirement, send_to=""))


        logger.info(f"Team will execute rounds of Tasks unless they finish the {end_stage} stage or run out of Investment funds!")

        if self.stage_callback is not None:
            self.stage_callback(stage=current_stage)

        #while n_round > 0 and (CONST.STAGES[end_stage] >= CONST.STAGES[current_stage]):
        # Failsafe to avoid infinite loop
        # TODO: change to monitor new messages in the environment??
        n_round = 20
        while n_round>0 and (CONST.STAGES[end_stage] >= CONST.STAGES[current_stage]):
            logger.info(f"Working on stage: {current_stage}")
            self._check_balance()
            try:
                await self.environment.run()
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
            
            new_stage: str = self.scan_advances(current_stage)
            if new_stage != current_stage:
                logger.info(f"Execution advanced to {new_stage} stage!")

                if self.stage_callback is not None:
                    self.stage_callback(stage=new_stage)
                current_stage = new_stage
                
            n_round -= 1
            
        history_file = CONFIG.product_root / "history.pickle"
        with open(history_file, 'wb') as file:
            file.write(serialize_batch(self.environment.memory.get()))
        
        self.save_product_config()
        logger.info("Team execution completed!")
        return self.environment.history
    
