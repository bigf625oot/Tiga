import sys
import os
import unittest

# Script location: d:\Tiga\backend\app\services\eah_agent\run_tests.py
script_dir = os.path.dirname(os.path.abspath(__file__))
# Target: d:\Tiga\backend
backend_root = os.path.abspath(os.path.join(script_dir, "../../.."))

if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Discover and run tests
loader = unittest.TestLoader()
start_dir = os.path.join(script_dir, 'tests')
suite = loader.discover(start_dir, pattern='test_*.py')

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

if not result.wasSuccessful():
    sys.exit(1)
