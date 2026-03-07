import importlib.util
import os
import sys
from typing import Callable, Dict, Any
import pathway as pw
from app.services.pathway.core.exceptions import OperatorError

def load_udf(file_path: str, function_name: str) -> Callable:
    """Load a UDF from a python file."""
    try:
        spec = importlib.util.spec_from_file_location("udf_module", file_path)
        if spec is None or spec.loader is None:
            raise OperatorError(f"Could not load UDF from {file_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules["udf_module"] = module
        spec.loader.exec_module(module)
        
        func = getattr(module, function_name)
        if not callable(func):
            raise OperatorError(f"{function_name} is not callable")
        
        return func
    except Exception as e:
        raise OperatorError(f"Failed to load UDF: {e}")

def apply_udf(table: pw.Table, config: Dict[str, Any]) -> pw.Table:
    """
    Apply a UDF to the table.
    config: {
        "file_path": "/path/to/udf.py",
        "function_name": "my_transform",
        "input_columns": ["col1", "col2"],
        "output_column": "new_col",
        "return_type": "int" 
    }
    """
    file_path = config.get("file_path")
    function_name = config.get("function_name")
    input_columns = config.get("input_columns", [])
    output_column = config.get("output_column")
    return_type_str = config.get("return_type", "str")
    
    # Map return type string to Python type
    type_map = {
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "dict": dict,
        "list": list
    }
    return_type = type_map.get(return_type_str, str)

    try:
        udf_func = load_udf(file_path, function_name)
        
        # Apply UDF
        # pw.apply takes a function and columns
        # If multiple input columns, need to pass them as args
        args = [table[col] for col in input_columns]
        
        # Using pw.apply
        result_col = pw.apply(udf_func, *args)
        
        return table.with_columns(**{output_column: result_col})
    except Exception as e:
        raise OperatorError(f"Failed to apply UDF: {e}")
