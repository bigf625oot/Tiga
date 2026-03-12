from abc import ABC, abstractmethod

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine


class SqlRunner(ABC):
    """
    Abstract base class for SQL Runners.
    """

    @abstractmethod
    def run_sql(self, sql: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_tables(self) -> list[str]:
        pass


class SQLAlchemyRunner(SqlRunner):
    """
    Concrete implementation of SqlRunner using SQLAlchemy.
    """

    def __init__(self, connection_string: str, **kwargs):
        self.engine: Engine = create_engine(connection_string, **kwargs)

    def run_sql(self, sql: str) -> pd.DataFrame:
        try:
            return pd.read_sql(sql, self.engine)
        except Exception as e:
            raise e

    def get_tables(self) -> list[str]:
        inspector = inspect(self.engine)
        return inspector.get_table_names()
