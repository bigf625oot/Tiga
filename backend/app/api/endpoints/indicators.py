import io
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_indicator import crud_indicator
from app.db.session import get_db
from app.schemas.indicator import IndicatorCreate, IndicatorResponse, IndicatorUpdate

router = APIRouter()


@router.get("/", response_model=List[IndicatorResponse])
async def read_indicators(
    skip: int = 0, limit: int = 20, search: Optional[str] = None, db: AsyncSession = Depends(get_db)
):
    return await crud_indicator.get_multi(db, skip=skip, limit=limit, search=search)


@router.post("/", response_model=IndicatorResponse)
async def create_indicator(indicator_in: IndicatorCreate, db: AsyncSession = Depends(get_db)):
    # Check uniqueness
    existing = await crud_indicator.get_by_group_and_name(db, indicator_in.group, indicator_in.name)
    if existing:
        raise HTTPException(status_code=400, detail="Indicator with this name already exists in the group")
    return await crud_indicator.create(db, indicator_in)


@router.patch("/{indicator_id}", response_model=IndicatorResponse)
async def update_indicator(indicator_id: int, indicator_in: IndicatorUpdate, db: AsyncSession = Depends(get_db)):
    indicator = await crud_indicator.get(db, indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")

    if indicator_in.name or indicator_in.group:
        # If updating name/group, check uniqueness
        new_group = indicator_in.group or indicator.group
        new_name = indicator_in.name or indicator.name
        existing = await crud_indicator.get_by_group_and_name(db, new_group, new_name)
        if existing and existing.id != indicator_id:
            raise HTTPException(status_code=400, detail="Indicator with this name already exists in the group")

    return await crud_indicator.update(db, indicator, indicator_in)


@router.delete("/{indicator_id}", response_model=IndicatorResponse)
async def delete_indicator(indicator_id: int, db: AsyncSession = Depends(get_db)):
    indicator = await crud_indicator.delete(db, indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return indicator


@router.post("/import")
async def import_indicators(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload CSV or Excel.")

    contents = await file.read()
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    # Validate columns
    required_columns = ["group", "name", "description"]
    # Aliases allows Chinese headers
    column_map = {
        "指标分组": "group",
        "指标名称": "name",
        "指标描述": "description",
        "指标别名": "alias",
        "Group": "group",
        "Name": "name",
        "Description": "description",
        "Alias": "alias",
        # Advanced options
        "相关术语": "related_terms",
        "技术特征": "technical_features",
        "计算公式": "formula",
        "典型格式": "typical_format",
        "常见位置": "common_location",
        "文档范围": "doc_scope",
        "默认值": "default_value",
        "取值范围": "value_range",
        "参考范围值": "reference_range",
        # English Advanced
        "Related Terms": "related_terms",
        "Technical Features": "technical_features",
        "Formula": "formula",
        "Typical Format": "typical_format",
        "Common Location": "common_location",
        "Doc Scope": "doc_scope",
        "Default Value": "default_value",
        "Value Range": "value_range",
        "Reference Range": "reference_range",
    }

    df.rename(columns=column_map, inplace=True)

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing)}")

    results = {"success": 0, "failed": 0, "errors": []}

    advanced_keys = [
        "related_terms",
        "technical_features",
        "formula",
        "typical_format",
        "common_location",
        "doc_scope",
        "default_value",
        "value_range",
        "reference_range",
    ]

    for index, row in df.iterrows():
        try:
            # Basic validation
            if pd.isna(row["group"]) or pd.isna(row["name"]):
                results["failed"] += 1
                results["errors"].append(f"Row {index + 1}: Missing group or name")
                continue

            group = str(row["group"]).strip()
            name = str(row["name"]).strip()
            desc = str(row["description"]) if not pd.isna(row["description"]) else None
            alias = str(row["alias"]) if "alias" in df.columns and not pd.isna(row["alias"]) else None

            # Collect advanced options
            advanced_options = {}
            for key in advanced_keys:
                if key in df.columns and not pd.isna(row[key]):
                    advanced_options[key] = str(row[key]).strip()

            # Check existence
            existing = await crud_indicator.get_by_group_and_name(db, group, name)
            if existing:
                results["failed"] += 1
                results["errors"].append(f"Row {index + 1}: Duplicate indicator '{name}' in group '{group}'")
                continue

            indicator_in = IndicatorCreate(
                group=group,
                name=name,
                description=desc,
                alias=alias,
                advanced_options=advanced_options if advanced_options else None,
            )
            await crud_indicator.create(db, indicator_in)
            results["success"] += 1

        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Row {index + 1}: {str(e)}")

    return results
