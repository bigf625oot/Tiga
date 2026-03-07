from typing import Dict, Any, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import settings
from app.models.data_source import DataSource
from app.utils.crypto_utils import decrypt_field
from app.services.pathway.core.exceptions import ConfigurationError

# Create a synchronous database session for Pathway bridge
def get_sync_db_url(async_url: str) -> str:
    """Convert async database URL to sync URL for Pathway bridge."""
    return async_url.replace("+aiosqlite", "").replace("+asyncpg", "")

sync_engine = create_engine(get_sync_db_url(settings.database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

class DataSourceBridge:
    def __init__(self):
        pass

    def get_source_config(self, source_id: int) -> Dict[str, Any]:
        """
        Retrieve and format data source configuration from the database.
        """
        db: Session = SessionLocal()
        try:
            source = db.query(DataSource).filter(DataSource.id == source_id).first()
            if not source:
                raise ConfigurationError(f"DataSource with ID {source_id} not found")

            config = self._format_config(source)
            return config
        finally:
            db.close()

    def _format_config(self, source: DataSource) -> Dict[str, Any]:
        """
        Convert DataSource model to Pathway connector configuration.
        """
        base_config = source.config or {}
        
        # Decrypt sensitive fields
        password = decrypt_field(source.password_encrypted) if source.password_encrypted else None
        api_key = decrypt_field(source.encrypted_api_key) if source.encrypted_api_key else None
        token = decrypt_field(source.encrypted_token) if source.encrypted_token else None

        if source.type in ["mysql", "postgresql"]:
            # Construct connection string
            # Format: postgresql://user:password@host:port/dbname
            # Handle special chars in password if needed (url encoding)
            if not source.username or not source.host:
                raise ConfigurationError(f"Missing connection details for {source.name}")
            
            driver = "postgresql" if source.type == "postgresql" else "mysql+pymysql"
            # Note: Pathway might use different drivers or connection string formats depending on the io module
            # pw.io.postgres uses typical libpq or sqlalchemy style
            
            # Simple URL construction (production should use urllib.parse.quote_plus for pass)
            import urllib.parse
            encoded_pass = urllib.parse.quote_plus(password) if password else ""
            encoded_user = urllib.parse.quote_plus(source.username)
            
            port_str = f":{source.port}" if source.port else ""
            conn_str = f"{driver}://{encoded_user}:{encoded_pass}@{source.host}{port_str}/{source.database}"
            
            return {
                **base_config,
                "connection_string": conn_str,
                "table_name": base_config.get("table_name"), # Should be in config JSON
                "schema": source.db_schema
            }

        elif source.type == "sftp":
            # For SFTP, Pathway might use pw.io.fs with a specific protocol handler or local mount
            # Or we return params for a custom connector
            return {
                **base_config,
                "host": source.host,
                "port": source.port or 22,
                "username": source.username,
                "password": password,
                "private_key": decrypt_field(source.encrypted_private_key) if source.encrypted_private_key else None
            }

        elif source.type in ["api", "rest"]:
            headers = base_config.get("headers", {})
            if token:
                headers["Authorization"] = f"Bearer {token}"
            elif api_key:
                headers["X-API-Key"] = api_key
            
            return {
                **base_config,
                "url": source.url or source.host, # url field preferred
                "headers": headers,
                "method": base_config.get("method", "GET")
            }
            
        elif source.type == "kafka":
            # Kafka config usually stored in config JSON
            return {
                **base_config,
                "rdkafka_settings": {
                    "bootstrap.servers": f"{source.host}:{source.port}",
                    "security.protocol": "SASL_SSL" if base_config.get("use_ssl") else "PLAINTEXT",
                    "sasl.mechanism": "PLAIN",
                    "sasl.username": source.username,
                    "sasl.password": password,
                    **(base_config.get("rdkafka_settings", {}))
                },
                "topic": base_config.get("topic")
            }

        else:
            # Generic fallback
            return {
                **base_config,
                "host": source.host,
                "port": source.port,
                "username": source.username,
                "password": password
            }

# Singleton
bridge = DataSourceBridge()
