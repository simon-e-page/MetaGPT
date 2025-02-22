#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/1 12:41
@Author  : alexanderwu
@File    : logs.py
"""

import sys

from loguru import logger as _logger
from pathlib import Path
from metagpt.const import PROJECT_ROOT

def define_log_level(print_level="INFO", logfile_level="DEBUG"):
    """调整日志级别到level之上
       Adjust the log level to above level
    """
    _logger.remove()
    _logger.add(sys.stderr, level=print_level)
    _logger.add(PROJECT_ROOT / 'logs/metagpt.log', level=logfile_level)
    return _logger

#def add_project_log(path: Path, logfile_level: str = "INFO", replace=False):
#    logfile = path / "logs/project.log"
#    if replace and logfile.exists():
#        logfile.unlink()
#    _logger.add(logfile, level=logfile_level)

logger = define_log_level()
