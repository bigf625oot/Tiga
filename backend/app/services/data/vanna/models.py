from typing import List, Optional

from pydantic import BaseModel, Field


class VannaRequest(BaseModel):
    question: str = Field(..., description="The natural language question")
    sql: Optional[str] = Field(None, description="The SQL query if already generated")
    context: Optional[List[str]] = Field(None, description="Additional context")


class VannaResponse(BaseModel):
    sql: Optional[str] = None
    table_markdown: Optional[str] = None
    chart_json: Optional[str] = None
    summary: Optional[str] = None
    error: Optional[str] = None


class DbConnectionConfig(BaseModel):
    name: Optional[str] = Field(None, description="Connection Name")
    type: str = Field(..., description="Database type (postgres, mysql, sqlite, etc.)")
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    path: Optional[str] = None  # For SQLite
    db_schema: Optional[str] = Field(None, description="Schema for PostgreSQL")  # Renamed from schema to avoid conflict

    # Advanced Options
    timeout: Optional[int] = Field(30, description="Connection timeout in seconds")
    charset: Optional[str] = Field("utf8mb4", description="Charset")
    ssl_mode: Optional[str] = Field("disable", description="SSL mode")
    pool_size: Optional[int] = Field(5, description="Connection pool size")
