import asyncssh
import base64
import os
import asyncio
from typing import List, AsyncGenerator, Any, Dict, Tuple
from app.strategies.base import BaseSource
from app.models.domain import MetadataModel, DataChunk
from app.utils.crypto_utils import decrypt_field

class SftpSource(BaseSource):
    """
    Strategy for SFTP sources using asyncssh.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    def _get_connection_params(self) -> Tuple[str, int, Dict[str, Any]]:
        host = self.config.get('host')
        port = self.config.get('port', 22)
        username = self.config.get('username')
        password = self.config.get('password')
        if self.config.get('password_encrypted'):
            password = decrypt_field(self.config['password_encrypted'])
        
        # In production, known_hosts should be handled. 
        # For this task, we skip check (equivalent to TrustAll) if not provided.
        options = {
            'username': username,
            'password': password,
            'known_hosts': None 
        }
        
        # Support private key
        private_key = self.config.get('private_key')
        if self.config.get('private_key_encrypted'):
             private_key = decrypt_field(self.config['private_key_encrypted'])
        
        if private_key:
             options['client_keys'] = [asyncssh.import_private_key(private_key)]

        return host, port, options

    async def test_connection(self) -> Dict[str, Any]:
        host, port, options = self._get_connection_params()
        try:
            # Set login timeout to 5s
            options['login_timeout'] = 5
            async with asyncssh.connect(host, port=port, **options) as conn:
                async with conn.start_sftp_client() as sftp:
                    # Timeout for command execution
                    files = await asyncio.wait_for(sftp.listdir('/'), timeout=5.0)
                    top_10 = files[:10]
                    # asyncssh listdir returns list of filenames (str) or SFTPName?
                    # According to docs, listdir returns list of strings (filenames).
                    # But if it returns SFTPName, we should cast to str.
                    # Let's assume strings based on common usage, but handle if objects.
                    file_names = [str(f) for f in top_10]
                    return {
                        "success": True, 
                        "message": f"Successfully connected. Top 10 files: {', '.join(file_names)}"
                    }
        except asyncssh.PermissionDenied:
             return {"success": False, "error_type": "AUTH_FAILED", "message": "Authentication failed"}
        except (asyncssh.ConnectionLost, OSError, asyncssh.DisconnectError) as e:
             # Check if it's a timeout
             if isinstance(e, asyncio.TimeoutError):
                 return {"success": False, "error_type": "TIMEOUT", "message": "Connection timed out"}
             return {"success": False, "error_type": "NETWORK_ERROR", "message": str(e)}
        except asyncio.TimeoutError:
             return {"success": False, "error_type": "TIMEOUT", "message": "Operation timed out"}
        except Exception as e:
             return {"success": False, "error_type": "UNKNOWN", "message": str(e)}

    async def fetch_metadata(self) -> List[MetadataModel]:
        host, port, options = self._get_connection_params()
        path = self.config.get('path', '.')
        
        async with asyncssh.connect(host, port=port, **options) as conn:
            async with conn.start_sftp_client() as sftp:
                files = await sftp.scandir(path)
                
                metadata_list = []
                for file_attr in files:
                    is_dir = getattr(file_attr, 'isdir', False) or (hasattr(file_attr, 'attrs') and file_attr.attrs.permissions and str(file_attr.attrs.permissions).startswith('d'))
                    # asyncssh SFTPAttrs logic might differ slightly, scandir returns SFTPName
                    # SFTPName has filename and attrs
                    
                    # Check if it is a directory using attribute helpers if available, or mode
                    # asyncssh.SFTPName has .attrs which is SFTPAttrs.
                    # SFTPAttrs has .permissions (int).
                    
                    # Using helper method from asyncssh if available, otherwise check mode
                    is_directory = False
                    if hasattr(file_attr, 'attrs'):
                         # standard unix check
                         import stat
                         if file_attr.attrs.permissions:
                             is_directory = stat.S_ISDIR(file_attr.attrs.permissions)
                    
                    size = file_attr.attrs.size if hasattr(file_attr, 'attrs') and file_attr.attrs.size is not None else 0
                    
                    metadata_list.append(MetadataModel(
                        name=file_attr.filename,
                        type='directory' if is_directory else 'file',
                        description=f"Size: {size} bytes"
                    ))
                return metadata_list

    async def fetch_data(self, **kwargs) -> AsyncGenerator[DataChunk, None]:
        filename = kwargs.get('filename')
        if not filename:
            raise ValueError("filename is required")
            
        host, port, options = self._get_connection_params()
        chunk_size = kwargs.get('chunk_size', 8192)
            
        async with asyncssh.connect(host, port=port, **options) as conn:
            async with conn.start_sftp_client() as sftp:
                async with sftp.open(filename, 'rb') as f:
                    while True:
                        data = await f.read(chunk_size)
                        if not data:
                            break
                        
                        # Data might be bytes or str depending on open mode, but 'rb' means bytes
                        if isinstance(data, str):
                             data = data.encode('utf-8')
                             
                        content_b64 = base64.b64encode(data).decode('utf-8')
                        
                        yield DataChunk(
                            data=[{'content_b64': content_b64}],
                            count=len(data),
                            has_more=True
                        )
                    
                    yield DataChunk(data=[], count=0, has_more=False)
