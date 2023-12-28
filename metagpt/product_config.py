#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : simonpage
@File    : product_config.py
"""

from metagpt.const import PROJECT_ROOT
from metagpt.utils.singleton import Singleton
from pathlib import Path


class ProductConfig(metaclass=Singleton):

    _instance = None

    def __init__(self):
        self.workspace_root: str = self._get("WORKSPACE_ROOT", f"{PROJECT_ROOT}/workspace")
        self._product_root: Path = None
        self._product_config: dict = None
        self._product_name: str = None
        self._email: str = ""
        
    @property
    def product_root(self) -> Path:
        return self._product_root

    @product_root.setter
    def product_root(self, value) -> None:
        self._product_root: Path = value

    @property
    def product_name(self) -> str:
        return self._product_name

    @product_name.setter
    def product_name(self, value) -> None:
        self._product_name: str = value

    @property
    def email(self) -> str:
        return self._email
    
    @email.setter
    def email(self, value: str) -> None:
        self._email = value

    def set_product_config(self, config_dict):
        self._product_config = config_dict

    @property
    def product_config(self):
        return self._product_config

    @property
    def idea(self) -> str:
        return self._product_config.get('IDEA', '')

    @idea.setter
    def idea(self, idea: str) -> None:
        self._product_config['IDEA'] = idea

    @property
    def stage(self) -> str:
        return self._product_config.get('STAGE', None)

    @stage.setter
    def stage(self, stage: str) -> None:
        self._product_config['STAGE'] = stage

    @property
    def end_stage(self) -> str:
        return self._product_config.get('END_STAGE', None)

    @end_stage.setter
    def end_stage(self, end_stage: str) -> None:
        self._product_config['END_STAGE'] = end_stage

PRODUCT_CONFIG = ProductConfig()
