from typing import Dict, Any, Optional

import pathway as pw
from app.services.pathway.connectors.base import BaseSource
from app.services.pathway.core.exceptions import ConnectorError
from app.services.pathway.connectors.generic_sql import GenericSQLSource

class KafkaSource(BaseSource):
    def read(self, config: Dict[str, Any]) -> pw.Table:
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
        # Assuming Postgres for now, can be extended
        try:
            return pw.io.postgres.read(
                connection_string=config.get("connection_string"),
                table_name=config.get("table_name"),
                columns=config.get("columns")
            )
        except Exception as e:
            raise ConnectorError(f"Failed to read from Database: {e}")

class S3Source(BaseSource):
    def read(self, config: Dict[str, Any]) -> pw.Table:
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
        try:
            # Assuming HTTP polling or similar mechanism
            # Pathway has limited HTTP source capabilities out-of-the-box in some versions
            # Here we simulate using a custom connector or assuming pathway supports it
            return pw.io.http.read(
                url=config.get("url"),
                method=config.get("method", "GET"),
                headers=config.get("headers"),
                format=config.get("format", "json"),
                schema=config.get("schema")
            )
        except Exception as e:
            raise ConnectorError(f"Failed to read from REST API: {e}")

SOURCE_REGISTRY = {
    "kafka": KafkaSource(),
    "database": DatabaseSource(),
    "s3": S3Source(),
    "rest": RESTSource(),
    "generic_sql": GenericSQLSource(),
}

def get_source(source_type: str) -> BaseSource:
    if source_type not in SOURCE_REGISTRY:
        raise ConnectorError(f"Unknown source type: {source_type}")
    return SOURCE_REGISTRY[source_type]
