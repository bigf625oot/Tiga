from typing import Optional

from agno.tools.websearch import WebSearchTools


class DuckDuckGoTools(WebSearchTools):
    _name = "duckduckgo"
    _label = "网络搜索 (Agno)"
    _description = "基于 Agno 框架的 DuckDuckGo 搜索"
    """
    DuckDuckGo 网络搜索工具 (基于 Agno)。
    支持网页搜索和新闻搜索。
    """

    def __init__(
        self,
        enable_search: bool = True,
        enable_news: bool = True,
        modifier: Optional[str] = None,
        fixed_max_results: Optional[int] = None,
        proxy: Optional[str] = None,
        timeout: Optional[int] = 10,
        verify_ssl: bool = True,
        **kwargs,
    ):
        super().__init__(
            enable_search=enable_search,
            enable_news=enable_news,
            backend="duckduckgo",
            modifier=modifier,
            fixed_max_results=fixed_max_results,
            proxy=proxy,
            timeout=timeout,
            verify_ssl=verify_ssl,
            **kwargs,
        )

        # Backward compatibility aliases for old method names
        self.duckduckgo_search = self.web_search
        self.duckduckgo_news = self.search_news

    _category = "search"

    @classmethod
    def is_available(cls) -> bool:
        """DuckDuckGo is always available."""
        return True
