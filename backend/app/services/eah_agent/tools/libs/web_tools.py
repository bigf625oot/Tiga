try:
    from agno.tools.website import WebsiteTools as AgnoWebsiteTools
except ImportError:
    class AgnoWebsiteTools:
        def __init__(self, *args, **kwargs): pass
try:
    from agno.tools.arxiv import ArxivTools as AgnoArxivTools
except ImportError:
    class AgnoArxivTools:
        def __init__(self, *args, **kwargs): pass
try:
    from agno.tools.wikipedia import WikipediaTools as AgnoWikipediaTools
except ImportError:
    class AgnoWikipediaTools:
        def __init__(self, *args, **kwargs): pass
from pydantic import BaseModel
import httpx

class WebsiteTools(AgnoWebsiteTools):
    _name = "website_tools"
    _label = "网页工具 (Website)"
    _description = "读取网页内容、提取文本"
    """
    使用 WebsiteTools 读取网页内容。
    """
    def __init__(self):
        super().__init__()

    # Override read_url to add headers for strict sites
    def read_url(self, url: str) -> str:
        """This function reads a url and returns the content.

        :param url: The url of the website to read.
        :return: Relevant documents from the website.
        """
        import json
        from agno.knowledge.reader.website_reader import WebsiteReader
        from agno.utils.log import log_debug

        website = WebsiteReader()
        
        log_debug(f"Reading website: {url}")
        
        # We need to monkey patch httpx.get locally to add User-Agent to WebsiteReader
        original_get = httpx.get
        original_async_get = httpx.AsyncClient.get
        
        def patched_get(*args, **kwargs):
            headers = kwargs.get('headers', {})
            if 'User-Agent' not in headers:
                headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
                headers['Accept-Language'] = 'en-US,en;q=0.5'
                headers['Sec-Fetch-Dest'] = 'document'
                headers['Sec-Fetch-Mode'] = 'navigate'
                headers['Sec-Fetch-Site'] = 'none'
                headers['Sec-Fetch-User'] = '?1'
                headers['Upgrade-Insecure-Requests'] = '1'
            kwargs['headers'] = headers
            return original_get(*args, **kwargs)

        try:
            httpx.get = patched_get
            relevant_docs = website.read(url=url)
            return json.dumps([doc.to_dict() for doc in relevant_docs])
        except Exception as e:
            # Fallback to pure requests if httpx patch doesn't bypass 403
            import requests
            from bs4 import BeautifulSoup
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1'
                }
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")
                for unwanted in soup.find_all(["script", "style", "nav", "header", "footer"]):
                    unwanted.decompose()
                text = soup.get_text(strip=True, separator=" ")
                return json.dumps([{"name": url, "id": url, "meta_data": {"url": url}, "content": text}])
            except Exception as inner_e:
                # Try Jina AI reader as a last resort
                try:
                    jina_url = f"https://r.jina.ai/{url}"
                    jina_res = requests.get(jina_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
                    if jina_res.status_code == 200:
                        return json.dumps([{"name": url, "id": url, "meta_data": {"url": url, "source": "jina"}, "content": jina_res.text}])
                except Exception:
                    pass
                    
                # Try a final naive fetch using urllib with spoofed headers
                try:
                    import urllib.request
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        if resp.status == 200:
                            html = resp.read().decode('utf-8', errors='ignore')
                            soup = BeautifulSoup(html, "html.parser")
                            for unwanted in soup.find_all(["script", "style", "nav", "header", "footer"]):
                                unwanted.decompose()
                            return json.dumps([{"name": url, "id": url, "meta_data": {"url": url}, "content": soup.get_text(strip=True, separator=" ")}])
                except Exception:
                    pass

                # We will return the fallback error as text so the LLM knows it failed but doesn't crash the tool.
                return f"Error reading website {url}. The site may be blocking scrapers (403 Forbidden). Details: {str(inner_e)}"
        finally:
            httpx.get = original_get

    class Config(BaseModel):
        pass

class ArxivTools(AgnoArxivTools):
    _name = "arxiv"
    _label = "学术搜索 (Arxiv)"
    _description = "搜索 Arxiv 论文并获取摘要"
    """
    使用 ArxivTools 搜索学术论文。
    """
    def __init__(self):
        super().__init__()

    class Config(BaseModel):
        pass

class WikipediaTools(AgnoWikipediaTools):
    _name = "wikipedia"
    _label = "百科搜索 (Wikipedia)"
    _description = "搜索维基百科条目"
    """
    使用 WikipediaTools 获取维基百科信息。
    """
    def __init__(self):
        super().__init__()

    class Config(BaseModel):
        pass
