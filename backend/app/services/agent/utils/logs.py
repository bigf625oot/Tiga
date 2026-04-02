import logging
import sys
from typing import Optional

class EAHLogger:
    """
    Expert AI Hub (EAH) 专用日志配置器
    提供统一的日志格式和级别管理
    """
    
    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EAHLogger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化日志配置"""
        # 创建 logger
        self._logger = logging.getLogger("eah_agent")
        self._logger.setLevel(logging.INFO)
        
        # 避免重复添加 handler
        if not self._logger.handlers:
            # 创建控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # 定义日志格式
            # [时间] [级别] [模块] - 消息
            formatter = logging.Formatter(
                fmt='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            
            # 添加处理器
            self._logger.addHandler(console_handler)

    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """
        获取 logger 实例
        Args:
            name: 子模块名称，例如 'builder', 'workflow'
        """
        base_logger = cls()._logger
        if name:
            return base_logger.getChild(name)
        return base_logger

    @classmethod
    def set_level(cls, level: int):
        """设置日志级别"""
        cls()._logger.setLevel(level)
        for handler in cls()._logger.handlers:
            handler.setLevel(level)

# 便捷使用的单例
logger = EAHLogger.get_logger()

def get_logger(name: str) -> logging.Logger:
    """获取带子模块名的 logger"""
    return EAHLogger.get_logger(name)
