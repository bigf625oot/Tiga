import ast
import os
import hashlib
from collections import defaultdict

def normalize_code(node):
    """Normalize AST to ignore variable names/docs but keep structure"""
    # This is a simplified approach: just use the string representation of the AST dump
    # Better approach would be to traverse and anonymize names
    return ast.dump(node, include_attributes=False)

def find_duplicates(root_dir):
    hashes = defaultdict(list)
    
    for root, _, files in os.walk(root_dir):
        for file in files:
            if not file.endswith('.py'): continue
            path = os.path.join(root, file)
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        # Ignore very small functions
                        if node.end_lineno - node.lineno < 5:
                            continue
                            
                        # Get source segment
                        lines = content.splitlines()[node.lineno-1:node.end_lineno]
                        # Remove docstrings and comments roughly
                        code_body = '\n'.join([l.strip() for l in lines if l.strip() and not l.strip().startswith('#')])
                        
                        # Use hash of code body
                        code_hash = hashlib.md5(code_body.encode('utf-8')).hexdigest()
                        hashes[code_hash].append({
                            'path': path,
                            'name': node.name,
                            'lines': f"{node.lineno}-{node.end_lineno}"
                        })
            except Exception as e:
                pass
                
    print(f"Scanned {root_dir}")
    count = 0
    for h, occurrences in hashes.items():
        if len(occurrences) > 1:
            count += 1
            print(f"\n--- Duplicate Block Found ({len(occurrences)} copies) ---")
            for occ in occurrences:
                print(f"  {occ['path']}:{occ['lines']} ({occ['name']})")
                
    if count == 0:
        print("No significant duplicates found.")

if __name__ == "__main__":
    find_duplicates("app/services/openclaw")
