from typing import Optional, List
from agno.tools.shell import ShellTools as AgnoShellTools
from pydantic import BaseModel, Field

class ShellTools(AgnoShellTools):
    _name = "shell"
    _label = "命令行 (Shell)"
    _description = "执行本地 Shell 命令"
    """
    使用 ShellTools 执行系统命令。
    """
    def __init__(self):
        super().__init__()

    class Config(BaseModel):
        pass
