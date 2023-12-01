#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 22:12
@Author  : alexanderwu
@File    : environment.py
"""
import asyncio
from typing import Iterable
import yaml

from pydantic import BaseModel, Field

from metagpt.memory import Memory
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.config import CONFIG
from metagpt.const import STAGES
from pathlib import Path

class Environment(BaseModel):
    """环境，承载一批角色，角色可以向环境发布消息，可以被其他角色观察到
       Environment, hosting a batch of roles, roles can publish messages to the environment, and can be observed by other roles
    
    """

    roles: dict[str, Role] = Field(default_factory=dict)
    memory: Memory = Field(default_factory=Memory)
    history: str = Field(default='')

    class Config:
        arbitrary_types_allowed = True

    def add_role(self, role: Role):
        """增加一个在当前环境的角色
           Add a role in the current environment
        """
        role.set_env(self)
        self.roles[role.profile] = role

    def add_roles(self, roles: Iterable[Role]):
        """增加一批在当前环境的角色
            Add a batch of characters in the current environment
        """
        for role in roles:
            self.add_role(role)

    def publish_message(self, message: Message):
        """向当前环境发布信息
          Post information to the current environment
        """
        # self.message_queue.put(message)
        self.memory.add(message)
        self.history += f"\n{message}"

    def set_stage(self, stage: str = "Next"):
        """ Start execution from a specific stage """

        # Ensure history has been loaded
        # Test prerequisites:
        #   If set stage < product config: remove later items from the History
        # Set stage
        # Or raise Exception

        stages = list(STAGES.keys())
        if stage == "Next":
            try:
                index: int = stages.index(self.stage)
                if index < len(stages):
                    index += 1                
            except ValueError:
                index = 0
            stage = stages[index]
        else:
            if stage not in stages:
                stage = stages[0]
        
        CONFIG.product_config['STAGE'] = stage

    def save_product_config(self):
        _yaml_file: Path = CONFIG.product_root / "product.yaml"
        with open(_yaml_file, "w", encoding="utf-8") as file:
            yaml.safe_dump(CONFIG.product_config, file)

    def get_product_config(self) -> None:
        _product_config: dict = {
            'IDEA': 'Make a simple web application that displays Hello World',
            'STAGE': 'Requirements'
        }
        
        _yaml_file: Path = CONFIG.product_root / "product.yaml"

        with open(_yaml_file, "r", encoding="utf-8") as file:
            yaml_data = yaml.safe_load(file)
            if yaml_data:               
                _product_config.update(yaml_data)
                CONFIG.set_product_config(_product_config)
            else:
                raise FileNotFoundError(f"No valid product config found at {self._yaml_file}")

    @property
    def idea(self) -> str:
        return CONFIG.product_config.get('IDEA', '')
    
    @property
    def stage(self) -> str:
        return CONFIG.product_config.get('STAGE', None)
    

    async def run(self, k=1):
        """处理一次所有信息的运行
        Process all Role runs at once
        """
        # while not self.message_queue.empty():
        # message = self.message_queue.get()
        # rsp = await self.manager.handle(message, self)
        # self.message_queue.put(rsp)
        for _ in range(k):
            futures = []
            for role in self.roles.values():
                future = role.run()
                futures.append(future)

            await asyncio.gather(*futures)

    def get_roles(self) -> dict[str, Role]:
        """获得环境内的所有角色
           Process all Role runs at once
        """
        return self.roles

    def get_role(self, name: str) -> Role:
        """获得环境内的指定角色
           get all the environment roles
        """
        return self.roles.get(name, None)
