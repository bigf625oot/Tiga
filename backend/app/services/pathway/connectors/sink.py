from typing import Dict, Any, Optional

import pathway as pw
from app.services.pathway.connectors.base import BaseSink
from app.services.pathway.core.exceptions import ConnectorError

class ClickHouseSink(BaseSink):
    def write(self, table: pw.Table, config: Dict[str, Any]) -> None:
        try:
            pw.io.clickhouse.write(
                table,
                host=config.get("host"),
                port=config.get("port"),
                user=config.get("user"),
                password=config.get("password"),
                database=config.get("database"),
                table_name=config.get("table_name"),
                columns=config.get("columns"),
                deduplication=config.get("deduplication", True)
            )
        except Exception as e:
            raise ConnectorError(f"Failed to write to ClickHouse: {e}")

class RedisSink(BaseSink):
    def write(self, table: pw.Table, config: Dict[str, Any]) -> None:
        try:
            pw.io.redis.write(
                table,
                host=config.get("host"),
                port=config.get("port"),
                key_column=config.get("key_column"),
                value_column=config.get("value_column"),
                hset=config.get("hset", True)
            )
        except Exception as e:
            raise ConnectorError(f"Failed to write to Redis: {e}")

class ElasticsearchSink(BaseSink):
    def write(self, table: pw.Table, config: Dict[str, Any]) -> None:
        try:
            pw.io.elasticsearch.write(
                table,
                host=config.get("host"),
                port=config.get("port"),
                index=config.get("index"),
                id_column=config.get("id_column"),
                doc_type=config.get("doc_type", "_doc"),
                refresh=config.get("refresh", False)
            )
        except Exception as e:
            raise ConnectorError(f"Failed to write to Elasticsearch: {e}")

SINK_REGISTRY = {
    "clickhouse": ClickHouseSink(),
    "redis": RedisSink(),
    "elasticsearch": ElasticsearchSink(),
}

def get_sink(sink_type: str) -> BaseSink:
    if sink_type not in SINK_REGISTRY:
        raise ConnectorError(f"Unknown sink type: {sink_type}")
    return SINK_REGISTRY[sink_type]
