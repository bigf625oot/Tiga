import sys
import os
sys.path.append(os.getcwd())
try:
    from app.main import app
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
