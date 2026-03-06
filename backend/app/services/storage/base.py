import abc
from typing import Optional, BinaryIO

class StorageProvider(abc.ABC):
    @abc.abstractmethod
    async def upload_file(self, file_obj: BinaryIO, object_name: str) -> bool:
        """Upload a file object."""
        pass

    @abc.abstractmethod
    def upload_file_sync(self, key: str, data: bytes) -> str:
        """Upload bytes synchronously (legacy support)."""
        pass
    
    @abc.abstractmethod
    def download_file(self, key: str, file_path: str):
        """Download file to local path."""
        pass

    @abc.abstractmethod
    def delete_file(self, key: str) -> bool:
        """Delete file."""
        pass

    @abc.abstractmethod
    def generate_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        """Generate a public/presigned URL."""
        pass
