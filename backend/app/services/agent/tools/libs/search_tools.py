try:
    from agno.tools.exa import ExaTools as AgnoExaTools
except ImportError:
    class AgnoExaTools:
        def __init__(self, *args, **kwargs):
            raise ImportError("exa-py is required. Please install it.")
try:
    from agno.tools.tavily import TavilyTools as AgnoTavilyTools
except ImportError:
    class AgnoTavilyTools:
        def __init__(self, *args, **kwargs):
            raise ImportError("tavily-python is required. Please install it.")
from pydantic import BaseModel, Field
import time
import json
from agno.utils.log import logger

class ExaTools(AgnoExaTools):
    _name = "exa"
    _label = "Exa 搜索"
    _description = "强大的 AI 搜索引擎"
    """
    使用 ExaTools 进行语义搜索。
    """
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: str = Field(..., description="Exa API Key")

class TavilyTools(AgnoTavilyTools):
    _name = "tavily"
    _label = "Tavily 搜索"
    _description = "针对 LLM 优化的搜索引擎"
    """
    使用 TavilyTools 进行搜索。具备 P10 级高可用重试机制。
    """
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    def web_search_using_tavily(self, query: str, max_results: int = 5) -> str:
        """
        [P10 架构] 重写原生检索方法，注入指数退避重试策略。
        屏蔽底层网络抖动 (Connection aborted, RemoteDisconnected 等)，保证全链路稳定性。
        """
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                # 调用父类的原生实现
                return super().web_search_using_tavily(query=query, max_results=max_results)
            except Exception as e:
                # 捕获 ConnectionError / ReadTimeout 等网络异常
                is_last_attempt = attempt == max_retries - 1
                if is_last_attempt:
                    logger.error(f"[TavilyTools] 网络请求彻底失败 (已重试 {max_retries} 次): {str(e)}")
                    return json.dumps({
                        "error": "Tavily search failed after multiple retries due to network instability.",
                        "details": str(e),
                        "query": query
                    })
                
                delay = base_delay * (2 ** attempt)
                logger.warning(f"[TavilyTools] 网络异常 (尝试 {attempt + 1}/{max_retries})，将在 {delay}s 后重试: {str(e)}")
                time.sleep(delay)

    class Config(BaseModel):
        api_key: str = Field(..., description="Tavily API Key")
