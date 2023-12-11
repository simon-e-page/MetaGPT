#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/20 17:46
@Author  : alexanderwu
@File    : management_action.py
"""
from metagpt.actions import Action


class ManagementAction(Action):
    """Management message without any implementation details"""
    async def run(self, *args, **kwargs):
        raise NotImplementedError
