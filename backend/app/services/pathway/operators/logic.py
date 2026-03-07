import pathway as pw
from typing import Dict, Any, Union
from app.services.pathway.operators.registry import OperatorRegistry
from app.services.pathway.core.exceptions import OperatorError

@OperatorRegistry.register("filter")
def apply_filter(table: pw.Table, config: Dict[str, Any]) -> pw.Table:
    """
    Apply a filter to the table based on a Python expression.
    
    Config:
        expression (str): A python expression returning a boolean. 
                          Variables in the expression MUST refer to columns using `col('name')` or `table['name']`.
                          Example: "col('intent') == 'refund' & col('confidence') > 0.8"
    """
    expression = config.get("expression")
    if not expression:
        return table

    try:
        def col(name):
            return table[name]
        
        # Prepare environment for eval
        env = {
            "table": table, 
            "pw": pw,
            "col": col,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict
        }
        
        # Evaluate the expression
        # Note: Pathway logical operators are '&' (AND), '|' (OR), '~' (NOT)
        # Users must use these instead of 'and', 'or', 'not' for column expressions.
        # The frontend builder will generate '&', '|'.
        
        filter_expr = eval(expression, {}, env)
        
        return table.filter(filter_expr)
        
    except Exception as e:
        # Re-raise with context
        raise OperatorError(f"Filter expression evaluation failed for '{expression}': {e}")
