import json
import warnings

from agno.tools import Toolkit

try:
    from ddgs import DDGS
except ImportError:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None


class DuckDuckGoTools(Toolkit):
    def __init__(self, **kwargs):
        super().__init__(name="duckduckgo_search", **kwargs)
        if DDGS:
            self.register(self.search)
            self.register(self.news)

    def search(self, query: str, max_results: int = 5) -> str:
        """Searches the web using DuckDuckGo."""
        if not DDGS:
            return "DuckDuckGo search library not installed."
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))
            return json.dumps(results, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Error searching: {e}"

    def news(self, query: str, max_results: int = 5) -> str:
        """Searches for news using DuckDuckGo."""
        if not DDGS:
            return "DuckDuckGo search library not installed."
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                with DDGS() as ddgs:
                    results = list(ddgs.news(query, max_results=max_results))
            return json.dumps(results, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Error searching news: {e}"
