import json
import os
import tempfile
from typing import Any, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.security import decrypt_password
from app.crud.crud_data_source import data_source as crud_data_source
from app.crud.crud_graph_export import graph_export_config
from app.db.session import get_db
from app.schemas.graph_export import (
    AIGenerateRequest,
    GraphExportConfig,
    GraphExportConfigCreate,
    GraphExportConfigUpdate,
)
from app.services.rag.engines.lightrag import lightrag_engine


def get_database_schema(url: str) -> str:
    from sqlalchemy import create_engine, inspect, text

    try:
        # Create engine
        engine = create_engine(url)
        inspector = inspect(engine)

        schema_text = []
        table_names = inspector.get_table_names()

        # Limit tables to avoid context overflow
        if len(table_names) > 20:
            schema_text.append(f"Note: Too many tables ({len(table_names)}). Analyzing first 20 tables.")
            table_names = table_names[:20]

        for table_name in table_names:
            try:
                columns = inspector.get_columns(table_name)
                pk = inspector.get_pk_constraint(table_name)
                fks = inspector.get_foreign_keys(table_name)

                col_strs = []
                for col in columns:
                    col_name = col["name"]
                    col_type = str(col["type"])
                    is_pk = "PK" if col_name in pk.get("constrained_columns", []) else ""
                    col_strs.append(f"{col_name} ({col_type}) {is_pk}")

                fk_strs = []
                for fk in fks:
                    fk_strs.append(
                        f"FK: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}"
                    )

                # Sample data (Limit 3 rows)
                samples = []
                try:
                    with engine.connect() as conn:
                        result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 3"))
                        keys = result.keys()
                        for row in result:
                            row_dict = dict(zip(keys, row))
                            # Truncate long values
                            clean_row = {
                                k: (str(v)[:50] + "..." if len(str(v)) > 50 else v) for k, v in row_dict.items()
                            }
                            samples.append(str(clean_row))
                except Exception:
                    pass

                schema_text.append(f"Table: {table_name}")
                schema_text.append(f"  Columns: {', '.join(col_strs)}")
                if fk_strs:
                    schema_text.append(f"  Foreign Keys: {'; '.join(fk_strs)}")
                if samples:
                    schema_text.append(f"  Sample Data: {samples}")
                schema_text.append("")
            except Exception as e:
                schema_text.append(f"Error analyzing table {table_name}: {e}")

        return "\n".join(schema_text)
    except Exception as e:
        return f"Error introspecting database: {str(e)}"


router = APIRouter()


@router.post("/ai_generate")
async def ai_generate_config(*, db: AsyncSession = Depends(get_db), req: AIGenerateRequest) -> Any:
    """
    Generate graph export configuration using AI based on database schema.
    """
    # 1. Ensure LLM service is initialized
    try:
        await lightrag_engine.ensure_initialized(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Service unavailable: {e}")

    # 2. Resolve Database URL
    url = req.database_url
    if req.data_source_id:
        ds = await crud_data_source.get(db, id=req.data_source_id)
        if ds:
            password = decrypt_password(ds.password_encrypted) if ds.password_encrypted else ""
            if ds.type == "sqlite":
                path = ds.database if ds.database else ds.host
                url = f"sqlite:///{path}"
            else:
                type_map = {"mysql": "mysql+pymysql", "postgresql": "postgresql"}
                driver = type_map.get(ds.type, ds.type)
                port_str = f":{ds.port}" if ds.port else ""
                pass_str = f":{password}" if password else ""
                db_str = f"/{ds.database}" if ds.database else ""
                url = f"{driver}://{ds.username}{pass_str}@{ds.host}{port_str}{db_str}"

    if not url:
        raise HTTPException(status_code=400, detail="Database URL or Data Source ID is required")

    # 3. Introspect Schema
    schema_info = await run_in_threadpool(get_database_schema, url)

    if "Error" in schema_info and len(schema_info) < 200:
        raise HTTPException(status_code=400, detail=f"Database Inspection Failed: {schema_info}")

    # 4. Call LLM
    prompt = f"""
    You are a Knowledge Graph configuration expert.
    Based on the following Database Schema, please generate a configuration JSON for exporting data to a Knowledge Graph.
    
    Database Schema:
    {schema_info}
    
    Existing Config (if any):
    {json.dumps(req.existing_config) if req.existing_config else "{}"}
    
    Requirements:
    1. Analyze the tables and foreign keys to identify Entities (Nodes) and Relationships (Edges).
    2. Nodes:
       - "table": source table name.
       - "label": meaningful Chinese label for the node (e.g. "用户" for users table).
       - "id_col": primary key column.
       - "properties": list of important columns to include as node properties.
    3. Edges:
       - "source_table", "source_col": foreign key column.
       - "target_table", "target_col": referenced primary key.
       - "relation": meaningful Chinese relation name (e.g. "下单" for user->order).
    4. Output:
       - "output_dir": "./data/lightrag_store"
       - "update_mode": "merge"
       - "lightrag_format": true
    5. Processing:
       - "max_workers": 4
       - "batch_size": 5000
       
    6. IMPORTANT: Return ONLY the JSON object. Do NOT include markdown code blocks (```json ... ```).
    7. Do NOT include the "database" field in the JSON as it is already configured.
    
    Format example:
    {{
        "graph": {{
            "nodes": [ ... ],
            "edges": [ ... ]
        }},
        "output": {{ ... }},
        "processing": {{ ... }}
    }}
    """

    try:
        response = await lightrag_engine.call_llm(
            prompt=prompt,
            system_prompt="You are a helpful assistant that generates JSON configurations for Knowledge Graphs. Output strictly valid JSON.",
        )

        # Clean response
        clean_json = response.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()

        return json.loads(clean_json)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI generated invalid JSON. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Generation Failed: {str(e)}")


@router.get("/", response_model=List[GraphExportConfig])
async def read_graph_export_configs(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve graph export configurations.
    """
    configs = await graph_export_config.get_multi(db, skip=skip, limit=limit)
    return configs


@router.post("/", response_model=GraphExportConfig)
async def create_graph_export_config(
    *,
    db: AsyncSession = Depends(get_db),
    config_in: GraphExportConfigCreate,
) -> Any:
    """
    Create new graph export configuration.
    """
    config = await graph_export_config.get_by_name(db, name=config_in.name)
    if config:
        raise HTTPException(status_code=400, detail="The config with this name already exists in the system.")
    config = await graph_export_config.create(db, obj_in=config_in)
    return config


@router.put("/{id}", response_model=GraphExportConfig)
async def update_graph_export_config(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    config_in: GraphExportConfigUpdate,
) -> Any:
    """
    Update a graph export configuration.
    """
    config = await graph_export_config.get(db, id=id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    config = await graph_export_config.update(db, db_obj=config, obj_in=config_in)
    return config


@router.get("/{id}", response_model=GraphExportConfig)
async def read_graph_export_config(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
) -> Any:
    """
    Get graph export configuration by ID.
    """
    config = await graph_export_config.get(db, id=id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config


@router.delete("/{id}", response_model=GraphExportConfig)
async def delete_graph_export_config(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
) -> Any:
    """
    Delete a graph export configuration.
    """
    config = await graph_export_config.get(db, id=id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    config = await graph_export_config.delete(db, id=id)
    return config


def run_export_task(config_data: dict):
    # Import here to avoid circular imports or early loading
    import yaml
    # from backend.scripts.export_graph_data import GraphExporter # Incorrect import

    # Correct import path relative to app execution context
    try:
        from app.scripts.export_graph_data import GraphExporter
    except ImportError:
        # Fallback for direct script execution or different python path
        import sys

        sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))
        from backend.scripts.export_graph_data import GraphExporter

    # Create temp config file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
        yaml.dump(config_data, tmp, allow_unicode=True)
        tmp_path = tmp.name

    try:
        exporter = GraphExporter(tmp_path)
        exporter.run()
    except Exception as e:
        print(f"Export failed: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/{id}/run")
async def run_graph_export(*, db: AsyncSession = Depends(get_db), id: int, background_tasks: BackgroundTasks) -> Any:
    """
    Run graph export process in background.
    """
    config = await graph_export_config.get(db, id=id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    # Process config to inject database credentials if data_source_id is present
    export_config = config.config_json
    # Ensure it's a dict
    if isinstance(export_config, str):
        try:
            export_config = json.loads(export_config)
        except:
            pass

    if isinstance(export_config, dict):
        # Create a copy to avoid modifying the DB object in memory if it's attached
        export_config = export_config.copy()

        db_conf = export_config.get("database", {})
        ds_id = db_conf.get("data_source_id")

        if ds_id:
            ds = await crud_data_source.get(db, id=ds_id)
            if ds:
                password = decrypt_password(ds.password_encrypted) if ds.password_encrypted else ""

                # Construct URL
                url = ""
                if ds.type == "sqlite":
                    # For SQLite, database or host might be path
                    # Based on DatabaseManagement.vue: path is saved in 'path' but mapped to model?
                    # DataSource model has: host, database. No 'path' field.
                    # In DatabaseManagement.vue:
                    # if sqlite: configForm.path -> passed to connect.
                    # Let's check DataSourceCreate schema again. It inherits DataSourceBase.
                    # DataSourceBase has: name, type, host, port, username, database, schema.
                    # It seems 'path' is likely stored in 'host' or 'database' for SQLite.
                    # Let's assume 'database' stores the path as per common convention if host is localhost.
                    # Or 'host' stores the path.
                    # Let's try both: if database looks like a path, use it.
                    path = ds.database if ds.database else ds.host
                    url = f"sqlite:///{path}"
                else:
                    type_map = {"mysql": "mysql+pymysql", "postgresql": "postgresql"}
                    driver = type_map.get(ds.type, ds.type)
                    port_str = f":{ds.port}" if ds.port else ""
                    pass_str = f":{password}" if password else ""
                    db_str = f"/{ds.database}" if ds.database else ""
                    url = f"{driver}://{ds.username}{pass_str}@{ds.host}{port_str}{db_str}"

                # Inject URL
                # Ensure database dict exists in copy
                if "database" not in export_config:
                    export_config["database"] = {}
                export_config["database"]["url"] = url
            else:
                print(f"Warning: Data source {ds_id} not found")

    # We pass the config json to the background task
    background_tasks.add_task(run_in_threadpool, run_export_task, export_config)

    return {"message": "Export task started in background"}
