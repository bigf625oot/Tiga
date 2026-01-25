from typing import Any, Optional
import pandas as pd
import plotly
import plotly.express as px
import json
from ..base import BaseTool

class VisualizeDataTool(BaseTool):
    """
    Tool to generate Plotly charts from data.
    """
    def execute(self, df: pd.DataFrame, question: str = "", **kwargs) -> Optional[str]:
        """
        Generates a Plotly JSON string from the DataFrame.
        """
        if df is None or df.empty:
            return None
            
        try:
            # Simple heuristic for chart generation
            # 1. If we have at least 1 dimension and 1 measure
            if len(df.columns) >= 2:
                col1 = df.columns[0]
                col2 = df.columns[1]
                
                # Check types
                is_col1_numeric = pd.api.types.is_numeric_dtype(df[col1])
                is_col2_numeric = pd.api.types.is_numeric_dtype(df[col2])
                
                if not is_col1_numeric and is_col2_numeric:
                    # Bar chart: Categorical x, Numeric y
                    fig = px.bar(df, x=col1, y=col2, title=question)
                    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
                elif is_col1_numeric and is_col2_numeric:
                    # Scatter plot: Numeric x, Numeric y
                    fig = px.scatter(df, x=col1, y=col2, title=question)
                    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
                elif pd.api.types.is_datetime64_any_dtype(df[col1]) and is_col2_numeric:
                    # Line chart: Time x, Numeric y
                    fig = px.line(df, x=col1, y=col2, title=question)
                    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            
            # Default to table if no chart logic matches or just return None to let frontend handle table
            return None
            
        except Exception as e:
            print(f"Visualization error: {e}")
            return None
