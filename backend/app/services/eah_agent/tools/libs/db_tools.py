from typing import Optional
from agno.tools.sql import SQLTools as AgnoSQLTools
from pydantic import BaseModel, Field

class SQLTools(AgnoSQLTools):
    _name = "sql_tools"
    _label = "数据库查询 (SQL)"
    _description = "连接并查询 SQL 数据库"
    """
    使用 SQLTools 执行 SQL 查询。
    """
    def __init__(self, db_url: str):
        super().__init__(db_url=db_url)

    class Config(BaseModel):
        db_url: str = Field(..., description="Database connection URL (e.g., sqlite:///db.sqlite3)")
