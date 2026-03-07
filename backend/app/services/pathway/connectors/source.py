from typing import Dict, Any, Optional

import pathway as pw
from app.services.pathway.connectors.base import BaseSource
from app.services.pathway.core.exceptions import ConnectorError
from app.services.pathway.connectors.generic_sql import GenericSQLSource
from app.services.pathway.connectors.bridge import bridge

class KafkaSource(BaseSource):
    def read(self, config: Dict[str, Any]) -> pw.Table:
        # Resolve config from DB if source_id is present
        if config.get("source_id"):
            config = bridge.get_source_config(config.get("source_id"))
            
        try:
            return pw.io.kafka.read(
                rdkafka_settings=config.get("rdkafka_settings"),
                topic=config.get("topic"),
                format=config.get("format", "json"),
                value_columns=config.get("columns")
            )
        except Exception as e:
            raise ConnectorError(f"Failed to read from Kafka: {e}")

class DatabaseSource(BaseSource):
    def read(self, config: Dict[str, Any]) -> pw.Table:
        if config.get("source_id"):
            config = bridge.get_source_config(config.get("source_id"))
            
        try:
            # Check for specific driver preference in config or default to postgres
            # For MySQL, we might need a different pw.io method if available, 
            # but usually pw.io.mysql or generic sql via connection string works.
            # Pathway 0.x often uses pw.io.postgres for postgres CDC.
            
            # If "mysql" in connection string, we might need to handle differently if Pathway has specific mysql connector
            # Currently assuming postgres/generic
            return pw.io.postgres.read(
                connection_string=config.get("connection_string"),
                table_name=config.get("table_name"),
                columns=config.get("columns")
            )
        except Exception as e:
            raise ConnectorError(f"Failed to read from Database: {e}")

class S3Source(BaseSource):
    def read(self, config: Dict[str, Any]) -> pw.Table:
        if config.get("source_id"):
            config = bridge.get_source_config(config.get("source_id"))
            
        try:
            return pw.io.s3.read(
                bucket_name=config.get("bucket_name"),
                object_key=config.get("object_key"),
                aws_access_key_id=config.get("aws_access_key_id"),
                aws_secret_access_key=config.get("aws_secret_access_key"),
                region=config.get("region"),
                format=config.get("format", "json"),
                schema=config.get("schema")
            )
        except Exception as e:
            raise ConnectorError(f"Failed to read from S3: {e}")

class RESTSource(BaseSource):
    def read(self, config: Dict[str, Any]) -> pw.Table:
        if config.get("source_id"):
            config = bridge.get_source_config(config.get("source_id"))
            
        try:
            return pw.io.http.read(
                url=config.get("url"),
                method=config.get("method", "GET"),
                headers=config.get("headers"),
                format=config.get("format", "json"),
                schema=config.get("schema")
            )
        except Exception as e:
            raise ConnectorError(f"Failed to read from REST API: {e}")

class FileSystemSource(BaseSource):
    """
    Reads from local filesystem (can be used for FTP/SFTP mounted paths).
    """
    def read(self, config: Dict[str, Any]) -> pw.Table:
        if config.get("source_id"):
            config = bridge.get_source_config(config.get("source_id"))
            
        try:
            return pw.io.fs.read(
                path=config.get("path"),
                format=config.get("format", "json"),
                schema=config.get("schema"),
                mode=config.get("mode", "streaming") # streaming or static
            )
        except Exception as e:
            raise ConnectorError(f"Failed to read from FileSystem: {e}")

SOURCE_REGISTRY = {
    "kafka": KafkaSource(),
    "database": DatabaseSource(),
    "s3": S3Source(),
    "rest": RESTSource(),
    "generic_sql": GenericSQLSource(),
    "fs": FileSystemSource(),
    "filesystem": FileSystemSource()
}

def get_source(source_type: str) -> BaseSource:
    if source_type not in SOURCE_REGISTRY:
        raise ConnectorError(f"Unknown source type: {source_type}")
    return SOURCE_REGISTRY[source_type]
