import pytest
from app.strategies import get_strategy
from app.strategies.base import BaseSource
from app.strategies.database import DatabaseSource
from app.strategies.sftp import SftpSource
from app.strategies.crawler import CrawlerSource
from app.strategies.api import ApiSource

def test_get_strategy_factory():
    config = {"host": "localhost"}
    
    # Test Database
    db_strategy = get_strategy("database", config)
    assert isinstance(db_strategy, DatabaseSource)
    
    # Test specific DB types fallback
    mysql_strategy = get_strategy("mysql", config)
    assert isinstance(mysql_strategy, DatabaseSource)
    
    # Test SFTP
    sftp_strategy = get_strategy("sftp", config)
    assert isinstance(sftp_strategy, SftpSource)
    
    # Test Crawler
    crawler_strategy = get_strategy("crawler", config)
    assert isinstance(crawler_strategy, CrawlerSource)
    
    # Test API
    api_strategy = get_strategy("api", config)
    assert isinstance(api_strategy, ApiSource)
    
    # Test Unknown
    with pytest.raises(ValueError):
        get_strategy("unknown_type", config)

def test_strategy_config():
    config = {"host": "test.com", "port": 22}
    s = get_strategy("sftp", config)
    assert s.config["host"] == "test.com"
    assert s.config["port"] == 22
