#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 16:07
@Author  : simonpage
@File    : jb_common.py
"""

import re
import ast
from typing import List, Tuple

from metagpt.utils.common import OutputParser

class ApprovalError(Exception):
    def __init__(self, message, approver=""):
        super().__init__(message)
        self.approver = approver


class JBParser(OutputParser):

    @classmethod
    def parse_simple_list(cls, text: str) -> list[str]:
        # Regular expression pattern for simple markdown lists
        pattern = r"-\s*(\[.*\])"
        match = re.search(pattern, text, re.DOTALL)
        lines = text.split('\n')
        items = []
        for line in lines:
            match = re.search(pattern, line)
            if match:
                items.append(ast.literal_eval(match.group(1)))
            else:
                items.append(line)
        return items

    @classmethod
    def parse_markdown_deliverable(cls, data, mapping):
        block_dict = cls.parse_blocks(data)
        parsed_data = {}
        for block, content in block_dict.items():
            # 尝试去除code标记
            try:
                content = cls.parse_code(text=content)
            except Exception:
                pass
            typing_define = mapping.get(block, None)
            if isinstance(typing_define, tuple):
                typing = typing_define[0]
            else:
                typing = typing_define
            if typing == List[str] or typing == List[Tuple[str, str]] or typing == List[List[str]]:
                # 尝试解析list
                try:
                    content = cls.parse_simple_list(text=content)
                    #content = cls.parse_file_list(text=content)
                except Exception:
                    pass
            # TODO: 多余的引号去除有风险，后期再解决
            elif typing == str:
            #     # 尝试去除多余的引号
                 try:
                     content = cls.parse_simple_str(text=content)
                 except Exception:
                     pass
            parsed_data[block] = content
        return parsed_data
