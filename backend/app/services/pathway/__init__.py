import sys
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Function to check if pathway is the dummy package
def is_dummy_pathway(module: Any) -> bool:
    # The dummy package usually lacks core attributes like 'run' or 'Table'
    # and might have a specific __file__ pointing to site-packages/pathway/__init__.py
    # but not containing real logic.
    return not hasattr(module, "run") and not hasattr(module, "Table")

# Try to import pathway
try:
    import pathway
    if is_dummy_pathway(pathway):
        raise ImportError("Pathway dummy package detected")
except ImportError:
    logger.warning("Pathway package not found or is a dummy package. Using mock for Windows compatibility.")
    
    # Create a mock class for Table that supports basic operations to avoid crashes during definition
    class MockTable:
        def __init__(self, *args, **kwargs): pass
        def __getitem__(self, item): return self
        def __add__(self, other): return self
        def with_columns(self, *args, **kwargs): return self
        def filter(self, *args, **kwargs): return self
        def select(self, *args, **kwargs): return self
        def groupby(self, *args, **kwargs): return self
        def reduce(self, *args, **kwargs): return self
        def distinct(self, *args, **kwargs): return self
        def cast(self, *args, **kwargs): return self
        @property
        def dt(self): return self
        def lower(self): return self
        def upper(self): return self
        
        # Comparison operators
        def __eq__(self, other): return self
        def __ne__(self, other): return self
        def __lt__(self, other): return self
        def __le__(self, other): return self
        def __gt__(self, other): return self
        def __ge__(self, other): return self
        
        # Arithmetic operators
        def __add__(self, other): return self
        def __sub__(self, other): return self
        def __mul__(self, other): return self
        def __truediv__(self, other): return self

    class MockIO:
        class MockConnector:
            def read(self, *args, **kwargs): return MockTable()
            def write(self, *args, **kwargs): pass
        
        kafka = MockConnector()
        postgres = MockConnector()
        s3 = MockConnector()
        http = MockConnector()
        clickhouse = MockConnector()
        redis = MockConnector()
        elasticsearch = MockConnector()

    class MockReducers:
        def sum(self, *args, **kwargs): return MockTable()
        def count(self, *args, **kwargs): return MockTable()
        def avg(self, *args, **kwargs): return MockTable()
        def min(self, *args, **kwargs): return MockTable()
        def max(self, *args, **kwargs): return MockTable()
        def count_distinct(self, *args, **kwargs): return MockTable()

    class MockPathway:
        Table = MockTable
        io = MockIO()
        reducers = MockReducers()
        
        @staticmethod
        def run(*args, **kwargs):
            logger.warning("Mock Pathway run called. Nothing will happen.")
            
        @staticmethod
        def apply(func, *args, **kwargs):
            return MockTable()
            
        @staticmethod
        def coalesce(*args, **kwargs):
            return MockTable()

    # Inject mock into sys.modules
    # We need to preserve the package structure if possible, but 'pathway' is a top-level module.
    sys.modules["pathway"] = MockPathway()
