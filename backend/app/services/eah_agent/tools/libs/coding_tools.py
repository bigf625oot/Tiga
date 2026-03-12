from typing import Optional, List, Any
from pydantic import BaseModel, Field
from agno.tools import Toolkit

# Python Tools
try:
    from agno.tools.python import PythonTools as AgnoPythonTools
except ImportError:
    class AgnoPythonTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("pandas is required for PythonTools.")

class PythonTools(AgnoPythonTools):
    _name = "python"
    _label = "Python 解释器"
    _description = "执行 Python 代码并分析数据"
    
    def __init__(self, run_code: bool = True, pip_install: bool = False):
        super().__init__(run_code=run_code, pip_install=pip_install)

    class Config(BaseModel):
        run_code: bool = Field(True, description="Allow running code")
        pip_install: bool = Field(False, description="Allow pip install")

# CSV Toolkit
try:
    from agno.tools.csv_toolkit import CsvTools as AgnoCsvTools
except ImportError:
    class AgnoCsvTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("pandas is required for CsvTools.")

class CsvTools(AgnoCsvTools):
    _name = "csv"
    _label = "CSV 工具"
    _description = "读取、写入和分析 CSV 文件"
    
    def __init__(self, csv_url: Optional[str] = None, csv_path: Optional[str] = None):
        super().__init__(csv_url=csv_url, csv_path=csv_path)

    class Config(BaseModel):
        csv_url: Optional[str] = Field(None, description="URL of CSV file")
        csv_path: Optional[str] = Field(None, description="Path to CSV file")

# Pandas Tools
try:
    from agno.tools.pandas import PandasTools as AgnoPandasTools
except ImportError:
    class AgnoPandasTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("pandas is required for PandasTools.")

class PandasTools(AgnoPandasTools):
    _name = "pandas"
    _label = "数据分析 (Pandas)"
    _description = "使用 Pandas 处理数据框"
    
    def __init__(self):
        super().__init__()
