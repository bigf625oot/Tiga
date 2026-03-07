from typing import Dict, Any, Type
from app.strategies.base import BaseSource
from app.strategies.database import DatabaseSource
from app.strategies.sftp import SftpSource
from app.strategies.crawler import CrawlerSource
from app.strategies.api import ApiSource

STRATEGY_MAP: Dict[str, Type[BaseSource]] = {
    "database": DatabaseSource,
    "sftp": SftpSource,
    "crawler": CrawlerSource,
    "api": ApiSource,
    "mysql": DatabaseSource,
    "postgresql": DatabaseSource,
    "postgres": DatabaseSource
}

def get_strategy(source_type: str, config: Dict[str, Any]) -> BaseSource:
    """
    Factory function to get the appropriate strategy instance.
    """
    strategy_class = STRATEGY_MAP.get(source_type.lower())
    if not strategy_class:
        # Fallback for specific DB types if not mapped explicitly above
        if source_type.lower() in ['mysql', 'postgres', 'postgresql', 'sqlite']:
            return DatabaseSource(config)
        raise ValueError(f"Unknown source type: {source_type}")
    return strategy_class(config)
