
import os
import re

def scan_todos_and_fixmes(root_dir):
    print(f"Scanning {root_dir} for TODO/FIXME...")
    for root, _, files in os.walk(root_dir):
        for file in files:
            if not file.endswith('.py'): continue
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if 'TODO' in line or 'FIXME' in line:
                        print(f"{path}:{i+1}: {line.strip()}")

if __name__ == "__main__":
    scan_todos_and_fixmes("app/services/openclaw")
