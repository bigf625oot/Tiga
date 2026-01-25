from typing import Any, Dict
import pandas as pd
from ..base import BaseTool
from ..runners.sql_runner import SqlRunner

class RunSqlTool(BaseTool):
    """
    Tool to run SQL queries against a database.
    """
    def __init__(self, sql_runner: SqlRunner):
        self.sql_runner = sql_runner
        
    def execute(self, sql: str, **kwargs) -> pd.DataFrame:
        """
        Executes the SQL query and returns a pandas DataFrame.
        """
        if not sql:
            return pd.DataFrame()
        return self.sql_runner.run_sql(sql)
