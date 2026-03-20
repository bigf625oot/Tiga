from typing import Optional
from pydantic import BaseModel, Field
from agno.tools import Toolkit

try:
    from agno.tools.visualization import VisualizationTools as AgnoVisualizationTools
except ImportError:
    class AgnoVisualizationTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("matplotlib is required for VisualizationTools. Please install it using `pip install matplotlib`.")

class VisualizationTools(AgnoVisualizationTools):
    _name = "visualization"
    _label = "数据可视化 (Visualization)"
    _description = "使用 matplotlib 创建图表并保存为文件"
    """
    使用 VisualizationTools 生成数据可视化图表。
    """
    def __init__(self, output_dir: Optional[str] = None):
        # 如果提供了 output_dir，则使用；否则可以设置一个默认值或留空
        super().__init__(output_dir=output_dir)

    class Config(BaseModel):
        output_dir: Optional[str] = Field(None, description="图表保存的输出目录")
