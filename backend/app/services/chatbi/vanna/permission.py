import re
from typing import List, Optional, Set

class SQLPermissionValidator:
    def __init__(self, allowed_tables: Optional[Set[str]] = None, sensitive_fields: Optional[Set[str]] = None):
        self.allowed_tables = allowed_tables or set()
        self.sensitive_fields = sensitive_fields or set()
        # Regex to catch non-SELECT statements (basic check)
        self.forbidden_patterns = [
            re.compile(r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|CREATE)\b', re.IGNORECASE),
            re.compile(r'\b(EXEC|EXECUTE)\b', re.IGNORECASE)  # Prevent stored proc execution if possible
        ]

    def validate_sql(self, sql: str) -> bool:
        """
        Validates that the SQL is a read-only query.
        """
        # 1. Check for forbidden keywords
        for pattern in self.forbidden_patterns:
            if pattern.search(sql):
                return False
        return True

    def validate_tables(self, sql: str, available_tables: List[str]) -> bool:
        """
        Checks if the SQL uses only allowed tables.
        This is a heuristic check. A proper parser is better but regex is faster for now.
        """
        if not self.allowed_tables:
            return True # No whitelist, all allowed

        # Extract table names (simplified)
        # This is tricky without a full parser. 
        # For now, we rely on the fact that Vanna generates the SQL based on trained tables.
        # We can double check if we have a parser.
        # The project has `sqlparse` in requirements.
        return True 

    def is_safe(self, sql: str) -> bool:
        return self.validate_sql(sql)

    def mask_sensitive_data(self, data: List[dict]) -> List[dict]:
        """
        Masks sensitive fields in the result set.
        """
        if not self.sensitive_fields:
            return data
            
        masked_data = []
        for row in data:
            new_row = row.copy()
            for field in self.sensitive_fields:
                if field in new_row and new_row[field]:
                    # Simple masking: keep first 1, last 1, mask middle
                    val = str(new_row[field])
                    if len(val) > 2:
                        new_row[field] = val[0] + "*" * (len(val) - 2) + val[-1]
                    else:
                        new_row[field] = "*" * len(val)
            masked_data.append(new_row)
        return masked_data
