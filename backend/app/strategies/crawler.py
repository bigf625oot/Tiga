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
        if not url:
            raise ValueError("URL is required for crawling")
            
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    content = await response.text()
                    # In a real crawler, we would parse HTML, extract links, etc.
                    # Here we return the page content.
                    yield DataChunk(
                        data=[{
                            'url': url,
                            'status': response.status,
                            'content': content,
                            'headers': dict(response.headers)
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
