import aiohttp
import asyncio
from typing import List, AsyncGenerator, Any, Dict
from app.strategies.base import BaseSource
from app.models.domain import MetadataModel, DataChunk
from app.utils.crypto_utils import decrypt_field

class ApiSource(BaseSource):
    """
    Strategy for external API sources.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    def _get_headers(self) -> Dict[str, str]:
        headers = self.config.get('headers', {}).copy()
        api_key = self.config.get('api_key')
        
        if self.config.get('api_key_encrypted'):
             api_key = decrypt_field(self.config['api_key_encrypted'])
        
        if api_key:
            # Assume Bearer token or custom header based on config
            auth_type = self.config.get('auth_type', 'Bearer')
            if auth_type == 'Header':
                header_name = self.config.get('auth_header_name', 'X-API-Key')
                headers[header_name] = api_key
            else:
                headers['Authorization'] = f"{auth_type} {api_key}"
        return headers

    async def test_connection(self) -> Dict[str, Any]:
        url = self.config.get('url')
        if not url:
             base_url = self.config.get('base_url')
             if base_url:
                  check_endpoint = self.config.get('health_endpoint', '/')
                  url = f"{base_url.rstrip('/')}/{check_endpoint.lstrip('/')}"
             else:
                  return {"success": False, "error_type": "UNKNOWN", "message": "URL is required"}

        method = self.config.get('method', 'GET').upper()
        headers = self._get_headers() 
        body = self.config.get('body')
        
        try:
             async with aiohttp.ClientSession() as session:
                 async with session.request(method, url, headers=headers, data=body, timeout=5) as response:
                      content_bytes = await response.content.read(100)
                      content_str = content_bytes.decode('utf-8', errors='ignore')
                      
                      status = response.status
                      if 200 <= status < 400:
                           return {"success": True, "message": f"Status: {status}. Preview: {content_str}"}
                      elif 400 <= status < 500:
                           return {"success": False, "error_type": "CLIENT_ERROR", "message": f"Status: {status}. Preview: {content_str}"}
                      elif 500 <= status < 600:
                           return {"success": False, "error_type": "SERVER_ERROR", "message": f"Status: {status}. Preview: {content_str}"}
                      else:
                           return {"success": False, "error_type": "UNKNOWN", "message": f"Status: {status}"}
                           
        except asyncio.TimeoutError:
             return {"success": False, "error_type": "TIMEOUT", "message": "Request timed out"}
        except aiohttp.ClientError as e:
             return {"success": False, "error_type": "NETWORK_ERROR", "message": str(e)}
        except Exception as e:
             return {"success": False, "error_type": "UNKNOWN", "message": str(e)}

    async def fetch_metadata(self) -> List[MetadataModel]:
        # If OpenAPI spec URL is provided, fetch it
        # Otherwise return configured endpoints
        endpoints = self.config.get('endpoints', [])
        metadata_list = []
        for ep in endpoints:
            path = ep.get('path', 'unknown') if isinstance(ep, dict) else str(ep)
            desc = ep.get('description', 'API Endpoint') if isinstance(ep, dict) else None
            metadata_list.append(MetadataModel(
                name=path,
                type='endpoint',
                description=desc
            ))
        return metadata_list

    async def fetch_data(self, **kwargs) -> AsyncGenerator[DataChunk, None]:
        endpoint = kwargs.get('endpoint')
        if not endpoint:
            # Fallback to configured endpoint if single
            endpoints = self.config.get('endpoints', [])
            if len(endpoints) == 1:
                ep = endpoints[0]
                endpoint = ep.get('path') if isinstance(ep, dict) else str(ep)
            else:
                raise ValueError("endpoint is required")
            
        base_url = self.config.get('base_url', '').rstrip('/')
        url = f"{base_url}/{endpoint.lstrip('/')}"
        
        params = kwargs.get('params', {})
        
        async with aiohttp.ClientSession(headers=self._get_headers()) as session:
            try:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if isinstance(data, list):
                        # Chunk list response
                        chunk_size = kwargs.get('chunk_size', 100)
                        # Yield in chunks
                        for i in range(0, len(data), chunk_size):
                            chunk = data[i:i+chunk_size]
                            yield DataChunk(
                                data=chunk,
                                count=len(chunk),
                                has_more=(i + chunk_size < len(data))
                            )
                        if not data:
                            yield DataChunk(data=[], count=0, has_more=False)
                            
                    elif isinstance(data, dict):
                         # Single object or paginated response structure
                         # Assuming single object or standard pagination wrappers
                         # Just yield it as one item
                         yield DataChunk(data=[data], count=1, has_more=False)
                    else:
                        # Raw data?
                        yield DataChunk(data=[{'raw': str(data)}], count=1, has_more=False)
                        
            except Exception as e:
                # Log error
                yield DataChunk(data=[{'error': str(e)}], count=1, has_more=False)
