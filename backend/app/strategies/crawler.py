import aiohttp
import asyncio
from typing import List, AsyncGenerator, Any, Dict
from app.strategies.base import BaseSource
from app.models.domain import MetadataModel, DataChunk
from app.utils.crypto_utils import decrypt_field

class CrawlerSource(BaseSource):
    """
    Strategy for web crawling sources.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    async def test_connection(self) -> Dict[str, Any]:
        subtype = self.config.get('subtype', '').lower()
        url = self.config.get('url')

        if not url:
            if 'tavily' in subtype:
                url = "https://api.tavily.com"
            elif 'opensearch' in subtype:
                url = "https://api.opensearch.org"
        
        if not url:
             return {"success": False, "error_type": "UNKNOWN", "message": "No URL or supported subtype provided"}

        api_key = self.config.get('api_key')
        if self.config.get('api_key_encrypted'):
            api_key = decrypt_field(self.config['api_key_encrypted'])
            
        headers = {}
        if api_key:
             headers['Authorization'] = f"Bearer {api_key}"

        try:
             async with aiohttp.ClientSession() as session:
                 # Try HEAD first
                 try:
                     async with session.head(url, headers=headers, timeout=5) as response:
                         if 200 <= response.status < 300:
                             return {"success": True, "message": "Connection successful"}
                         if response.status in [401, 403]:
                             return {"success": False, "error_type": "INVALID_API_KEY", "message": "Invalid API Key"}
                 except Exception:
                     # Ignore HEAD errors and try GET
                     pass
                 
                 # Try GET
                 async with session.get(url, headers=headers, timeout=5) as response:
                     if 200 <= response.status < 300:
                         return {"success": True, "message": "Connection successful"}
                     elif response.status in [401, 403]:
                         return {"success": False, "error_type": "INVALID_API_KEY", "message": "Invalid API Key"}
                     else:
                         return {"success": False, "error_type": "NETWORK_ERROR", "message": f"Unexpected status code: {response.status}"}

        except asyncio.TimeoutError:
             return {"success": False, "error_type": "TIMEOUT", "message": "Request timed out"}
        except aiohttp.ClientError as e:
             return {"success": False, "error_type": "NETWORK_ERROR", "message": str(e)}
        except Exception as e:
             return {"success": False, "error_type": "UNKNOWN", "message": str(e)}

    async def fetch_metadata(self) -> List[MetadataModel]:
        # Return basic info about the target
        return [
            MetadataModel(
                name=self.config.get('url', 'unknown'),
                type='website',
                description="Web Crawler Target"
            )
        ]

    async def fetch_data(self, **kwargs) -> AsyncGenerator[DataChunk, None]:
        url = kwargs.get('url') or self.config.get('url')
        selector = self.config.get('selector')
        use_custom_selector = self.config.get('use_custom_selector', False)
        js_render = self.config.get('js_render', False)
        depth = self.config.get('depth', 1)

        if not url:
            raise ValueError("URL is required for crawling")
            
        # Mocking AI Auto Extraction if selector is not provided
        # In a real implementation, this would use a library like `trafilatura` or an LLM service
        # to extract the main content.
        
        async with aiohttp.ClientSession() as session:
            try:
                # If js_render is True, we would use playwright or selenium here.
                # For now, we simulate basic fetching.
                async with session.get(url) as response:
                    html_content = await response.text()
                    
                    extracted_content = html_content
                    extraction_method = "raw"

                    if not use_custom_selector:
                        # --- AI Auto Detect Simulation ---
                        # Here we would use an intelligent extractor.
                        # For demonstration, let's assume we strip scripts/styles and get body text.
                        # In production: from trafilatura import extract; extracted_content = extract(html_content)
                        try:
                            # Simple heuristic: try to find <article> or main content div
                            # This is a placeholder for "AI Auto Detect"
                            import re
                            body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
                            if body_match:
                                # Remove scripts and styles
                                clean_text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', body_match.group(1), flags=re.DOTALL | re.IGNORECASE)
                                # Remove tags
                                clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
                                # Normalize whitespace
                                extracted_content = ' '.join(clean_text.split())
                                extraction_method = "ai_auto"
                            else:
                                extracted_content = "Could not detect main content automatically."
                        except Exception:
                            extracted_content = "AI extraction failed, returning raw HTML."
                    
                    elif selector:
                        # --- Custom Selector Extraction ---
                        # We would use BeautifulSoup here.
                        # from bs4 import BeautifulSoup
                        # soup = BeautifulSoup(html_content, 'html.parser')
                        # selection = soup.select(selector)
                        # extracted_content = "\n".join([s.get_text() for s in selection])
                        extraction_method = f"selector: {selector}"
                        pass # Placeholder

                    yield DataChunk(
                        data=[{
                            'url': url,
                            'status': response.status,
                            'title': 'Page Title Detected', # Placeholder
                            'content': extracted_content,
                            'extraction_method': extraction_method,
                            'crawled_at': 'now'
                        }],
                        count=1,
                        has_more=False
                    )
            except Exception as e:
                # Yield error info or re-raise
                yield DataChunk(
                    data=[{'url': url, 'error': str(e)}],
                    count=1,
                    has_more=False
                )
