#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:26
@Author  : alexanderwu
@File    : design_api.py
"""
import shutil
from pathlib import Path
from typing import List

from metagpt.actions import Action, ActionOutput
from metagpt.config import CONFIG
#from metagpt.const import WORKSPACE_ROOT
import metagpt.const as CONST

from metagpt.logs import logger
from metagpt.utils.common import CodeParser
from metagpt.utils.get_template import get_template
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.utils.mermaid import mermaid_to_file

templates = {
    "json": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Format example
{format_example}
-----
Role: You are an architect; the goal is to design a SOTA PEP8-compliant python system; make the best use of good open source tools
Requirement: Fill in the following missing information based on the context, each section name is a key in json
Max Output: 8192 chars or 2048 tokens. Try to use them up.

## Implementation approach: Provide as Plain text. Analyze the difficult points of the requirements, select the appropriate open-source framework.

## Python package name: Provide as Python str with python triple quoto, concise and clear, characters only use a combination of all lowercase and underscores

## File list: Provided as Python list[str], the list of ONLY REQUIRED files needed to write the program(LESS IS MORE!). Only need relative paths, comply with PEP8 standards. ALWAYS write a main.py or app.py here

## Data structures and interface definitions: Use mermaid classDiagram code syntax, including classes (INCLUDING __init__ method) and functions (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with PEP8 standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Program call flow: Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.

## Anything UNCLEAR: Provide as Plain text. Make clear here.

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like format example,
and only output the json inside this tag, nothing else
""",
        "FORMAT_EXAMPLE": """
[CONTENT]
{
    "Implementation approach": "We will ...",
    "Python package name": "snake_game",
    "File list": ["main.py"],
    "Data structures and interface definitions": '
    classDiagram
        class Game{
            +int score
        }
        ...
        Game "1" -- "1" Food: has
    ',
    "Program call flow": '
    sequenceDiagram
        participant M as Main
        ...
        G->>M: end game
    ',
    "Anything UNCLEAR": "The requirement is clear to me."
}
[/CONTENT]
""",
    },
    "markdown": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Format example
{format_example}
-----
Role: You are an architect; the goal is to design a SOTA PEP8-compliant python system; make the best use of good open source tools
Requirement: Fill in the following missing information based on the context, note that all sections are response with code form separately
Max Output: 8192 chars or 2048 tokens. Try to use them up.
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## Implementation approach: Provide as Plain text. Analyze the difficult points of the requirements, select the appropriate open-source framework.

## Python package name: Provide as Python str with python triple quoto, concise and clear, characters only use a combination of all lowercase and underscores

## File list: Provided as Python list[str], the list of ONLY REQUIRED files needed to write the program(LESS IS MORE!). Only need relative paths, comply with PEP8 standards. ALWAYS write a main.py or app.py here

## Data structures and interface definitions: Use mermaid classDiagram code syntax, including classes (INCLUDING __init__ method) and functions (with type annotations), CLEARLY MARK the RELATIONSHIPS between classes, and comply with PEP8 standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design. 

## Program call flow: Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.

## Anything UNCLEAR: Provide as Plain text. Make clear here.

""",
        "FORMAT_EXAMPLE": """
---
## Implementation approach
We will ...

## Python package name
```python
"snake_game"
```

## File list
```python
[
    "main.py",
]
```

## Data structures and interface definitions
```mermaid
classDiagram
    class Game{
        +int score
    }
    ...
    Game "1" -- "1" Food: has
```

## Program call flow
```mermaid
sequenceDiagram
    participant M as Main
    ...
    G->>M: end game
```

## Anything UNCLEAR
The requirement is clear to me.
---
""",
    },
}

OUTPUT_MAPPING = {
    "Implementation approach": (str, ...),
    "Python package name": (str, ...),
    "File list": (List[str], ...),
    "Data structures and interface definitions": (str, ...),
    "Program call flow": (str, ...),
    "Anything UNCLEAR": (str, ...),
}


class WriteJBDesign(Action):
    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = (
            "Based on the PRD, think about the system design, and design the corresponding APIs, "
            "data structures, library tables, processes, and paths. Please provide your design, feedback "
            "clearly and in detail."
        )

    def recreate_workspace(self, workspace: Path) -> None:
        """ Delete and recreate directories - unused?"""
        try:
            shutil.rmtree(workspace)
        except FileNotFoundError:
            pass  # Folder does not exist, but we don't care
        workspace.mkdir(parents=True, exist_ok=True)

    async def _save_system_design(self, docs_path, resources_path, system_design):
        """ Save system design to output workspace """
        data_api_design = system_design.instruct_content.dict()[
            "Data structures and interface definitions"
        ]  # CodeParser.parse_code(block="Data structures and interface definitions", text=content)
        seq_flow = system_design.instruct_content.dict()[
            "Program call flow"
        ]  # CodeParser.parse_code(block="Program call flow", text=content)
        await mermaid_to_file(data_api_design, resources_path / "data_api_design")
        await mermaid_to_file(seq_flow, resources_path / "seq_flow")
        system_design_file: Path = docs_path / "system_design.md"
        logger.info(f"Saving System Designs to {system_design_file}")
        markdown: str = json_to_markdown(system_design.instruct_content.dict())
        logger.info(markdown)
        system_design_file.write_text((markdown))

    async def _save(self, context, system_design) -> None:
        """ Save system design to output workspace """
        workspace: Path = CONFIG.product_root
        docs_path: Path = workspace / "docs"
        resources_path: Path = workspace / "resources"
        await self._save_system_design(docs_path, resources_path, system_design)

    async def run(self, context, format=CONFIG.prompt_format):
        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(context=context, format_example=format_example)
        # system_design = await self._aask(prompt)
        system_design = await self._aask_v1(prompt, "system_design", OUTPUT_MAPPING, format=format)
        # fix Python package name, we can't system_design.instruct_content.python_package_name = "xxx" since "Python package name" contain space, have to use setattr
        setattr(
            system_design.instruct_content,
            "Python package name",
            system_design.instruct_content.dict()["Python package name"].strip().strip("'").strip('"'),
        )
        await self._save(context, system_design)
        return system_design
