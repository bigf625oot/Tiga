from typing import Dict, Any
import json
import csv
import io
import re
import pathway as pw
from app.services.pathway.core.exceptions import OperatorError
from app.services.pathway.operators.registry import OperatorRegistry

# Optional dependencies
try:
    import yaml
except ImportError:
    yaml = None

@OperatorRegistry.register("structuring")
def apply_structuring(table: pw.Table, config: Dict[str, Any]) -> pw.Table:
    """
    Apply structuring operations to parse raw text columns into structured data.
    
    Config:
        action (str): json_parse, csv_parse, markdown_parse
        input_col (str): Column containing raw text
        output_col (str): Column to store result (or prefix for multiple columns)
        params (Dict): Additional parameters
    """
    action = config.get("action")
    input_col = config.get("input_col")
    output_col = config.get("output_col") # Can be a single column name or None (for expanding)
    params = config.get("params", {})

    if not input_col:
        raise OperatorError("input_col is required for structuring")

    try:
        if action == "json_parse":
            # Parse JSON string into a struct/dict
            # Pathway UDF
            def _parse_json(text):
                try:
                    return json.loads(text) if text else None
                except:
                    return None
            
            return table.with_columns(**{output_col: pw.apply(_parse_json, table[input_col])})

        elif action == "csv_parse":
            # Parse a single CSV line
            delimiter = params.get("delimiter", ",")
            quotechar = params.get("quotechar", '"')
            
            def _parse_csv(line):
                if not line: return []
                try:
                    reader = csv.reader(io.StringIO(line), delimiter=delimiter, quotechar=quotechar)
                    return next(reader)
                except:
                    return []

            return table.with_columns(**{output_col: pw.apply(_parse_csv, table[input_col])})

        elif action == "markdown_parse":
            # Extract frontmatter and content
            # Returns a dict: {"meta": {...}, "content": "..."}
            def _parse_md(text):
                if not text: return {"meta": {}, "content": ""}
                
                meta = {}
                content = text
                
                # Simple frontmatter regex
                fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', text, re.DOTALL)
                if fm_match:
                    fm_text = fm_match.group(1)
                    content = fm_match.group(2)
                    if yaml:
                        try:
                            meta = yaml.safe_load(fm_text)
                        except:
                            pass
                    else:
                        # Simple key-value fallback
                        for line in fm_text.split('\n'):
                            if ':' in line:
                                k, v = line.split(':', 1)
                                meta[k.strip()] = v.strip()
                
                return {"meta": meta, "content": content}

            return table.with_columns(**{output_col: pw.apply(_parse_md, table[input_col])})

        else:
            raise OperatorError(f"Unknown structuring action: {action}")

    except Exception as e:
        raise OperatorError(f"Structuring '{action}' failed: {e}")
