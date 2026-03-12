from typing import Optional
from agno.tools import Toolkit
from pydantic import BaseModel, Field

class DuckDBTools(Toolkit):
    _name = "duckdb"
    _label = "数据查询 (DuckDB)"
    _description = "高性能本地 SQL 查询引擎"
    """
    使用 DuckDB 对本地文件（CSV, Parquet, JSON）执行 SQL 查询。
    """
    def __init__(self, db_path: str = ":memory:"):
        super().__init__(name="duckdb_tools")
        self.db_path = db_path
        self.register(self.execute_sql)
        self.register(self.describe_table)

    def execute_sql(self, query: str) -> str:
        """
        Execute a SQL query using DuckDB.
        Example: SELECT * FROM 'data.csv' LIMIT 5;
        """
        try:
            import duckdb
            conn = duckdb.connect(self.db_path)
            # Run query and fetch result as markdown
            # Using fetchdf() directly
            df = conn.execute(query).fetchdf()
            conn.close()
            if df.empty:
                return "Query executed successfully. No results returned."
            return df.to_markdown(index=False)
        except ImportError:
            return "Error: duckdb package is not installed. Please install it using `pip install duckdb`."
        except Exception as e:
            return f"Error executing SQL: {str(e)}"

    def describe_table(self, table_name: str) -> str:
        """Get schema of a table or file."""
        return self.execute_sql(f"DESCRIBE SELECT * FROM '{table_name}' LIMIT 0;")

    class Config(BaseModel):
        db_path: str = Field(":memory:", description="Path to DuckDB database file (default: :memory:)")

class PandasTools(Toolkit):
    _name = "pandas"
    _label = "数据处理 (Pandas)"
    _description = "强大的数据分析与处理库"
    """
    使用 Pandas 进行数据分析和处理。
    """
    def __init__(self):
        super().__init__(name="pandas_tools")
        self.register(self.read_csv_head)
        self.register(self.get_column_stats)

    def read_csv_head(self, file_path: str, n: int = 5) -> str:
        """Read the first n rows of a CSV file."""
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            return df.head(n).to_markdown(index=False)
        except ImportError:
            return "Error: pandas package is not installed. Please install it using `pip install pandas`."
        except Exception as e:
            return f"Error reading CSV: {str(e)}"

    def get_column_stats(self, file_path: str, column: str) -> str:
        """Get basic statistics for a specific column in a CSV file."""
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            if column not in df.columns:
                return f"Column '{column}' not found."
            return str(df[column].describe())
        except ImportError:
            return "Error: pandas package is not installed. Please install it using `pip install pandas`."
        except Exception as e:
            return f"Error analyzing column: {str(e)}"

    class Config(BaseModel):
        pass
