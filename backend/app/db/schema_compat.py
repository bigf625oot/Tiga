from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.dialects.sqlite import dialect as sqlite_dialect

logger = logging.getLogger(__name__)


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _sql_literal(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return None


def _extract_default_sql(column) -> str | None:
    server_default = getattr(column, "server_default", None)
    if server_default is not None:
        try:
            arg = getattr(server_default, "arg", None)
            if arg is None:
                return None
            return str(arg)
        except Exception:
            return None

    default = getattr(column, "default", None)
    if default is None:
        return None
    try:
        arg = default.arg
    except Exception:
        return None
    return _sql_literal(arg)


async def ensure_sqlite_schema_compat(conn: AsyncConnection) -> None:
    try:
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        existing_tables = {row[0] for row in result.all()}
    except Exception:
        return

    try:
        from app.db.base import Base
        tables = list(Base.metadata.sorted_tables)
    except Exception:
        return

    dialect = sqlite_dialect()

    for table in tables:
        if table.name not in existing_tables:
            continue

        try:
            info = await conn.execute(text(f"PRAGMA table_info('{table.name}')"))
            existing_cols = {row["name"] for row in info.mappings().all()}
        except Exception:
            continue

        for column in table.columns:
            if column.name in existing_cols:
                continue
            if getattr(column, "primary_key", False):
                continue

            try:
                col_type_sql = column.type.compile(dialect=dialect)
            except Exception:
                continue

            default_sql = _extract_default_sql(column)
            parts = [
                "ALTER TABLE",
                _quote_ident(table.name),
                "ADD COLUMN",
                _quote_ident(column.name),
                col_type_sql,
            ]
            if default_sql is not None:
                parts.extend(["DEFAULT", default_sql])
                if getattr(column, "nullable", True) is False:
                    parts.append("NOT NULL")

            stmt = " ".join(parts)
            try:
                await conn.execute(text(stmt))
                logger.info("SQLite schema compat applied: %s", stmt)
            except Exception as e:
                logger.warning("SQLite schema compat failed: %s (%s)", stmt, e)
