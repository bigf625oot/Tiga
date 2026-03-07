from typing import Dict, Any, List
import pandas as pd
from sqlalchemy import create_engine, inspect
import pathway as pw
from app.services.pathway.connectors.base import BaseSource
from app.services.pathway.core.exceptions import ConnectorError

class GenericSQLSource(BaseSource):
    """
    Generic SQL Source using SQLAlchemy to bridge any DB to Pathway via Pandas.
    Note: This is not a streaming source in the strict sense (snapshot/batch).
    """
    def read(self, config: Dict[str, Any]) -> pw.Table:
        connection_string = config.get("connection_string")
        query = config.get("query")
        table_name = config.get("table_name")
        
        if not connection_string:
            raise ConnectorError("connection_string is required for GenericSQLSource")
        
        try:
            engine = create_engine(connection_string)
            
            if query:
                df = pd.read_sql_query(query, engine)
            elif table_name:
                df = pd.read_sql_table(table_name, engine)
            else:
                raise ConnectorError("Either query or table_name must be provided")
            
            # Convert Pandas DataFrame to Pathway Table
            # pw.debug.table_from_pandas creates a static table
            # For "streaming" updates, one would need a custom Input Connector that polls
            return pw.debug.table_from_pandas(df)
            
        except Exception as e:
            raise ConnectorError(f"Failed to read from Generic SQL Source: {e}")

    def discover_schema(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Discover schema using SQLAlchemy Inspector.
        """
        connection_string = config.get("connection_string")
        table_name = config.get("table_name")
        
        if not connection_string:
             raise ConnectorError("connection_string is required for discovery")
             
        try:
            engine = create_engine(connection_string)
            inspector = inspect(engine)
            
            if table_name:
                columns = inspector.get_columns(table_name)
                # Convert to standardized format
                return [{"name": col["name"], "type": str(col["type"])} for col in columns]
            else:
                # If query is provided, we can't easily inspect without running it.
                # We could run "SELECT * FROM (...) LIMIT 0" or similar.
                # For now, just return table names if no table provided
                return [{"table_name": t} for t in inspector.get_table_names()]
                
        except Exception as e:
            raise ConnectorError(f"Schema discovery failed: {e}")
