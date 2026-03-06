import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from openai import APIStatusError, APITimeoutError, AsyncOpenAI, AuthenticationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.llm_model import LLMModel
from app.schemas.llm_model import LLMModelCreate, LLMModelResponse, LLMModelUpdate, LLMTestRequest, LLMTestResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Existing Endpoints (Keep them for now) ---


@router.post("/register")
async def register_llm_provider():
    return {"message": "LLM Provider registration endpoint"}


@router.post("/process")
async def process_recording_with_llm():
    return {"message": "Processing recording with LLM"}


# --- New Model Management Endpoints ---


@router.post("/models/test", response_model=LLMTestResponse)
async def test_llm_connection(request: LLMTestRequest):
    """
    Test the connection to the LLM provider.
    """
    api_key = request.api_key
    base_url = request.base_url

    # Set default base_url for known providers if not provided
    if not base_url:
        if request.provider == "aliyun":
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        elif request.provider == "deepseek":
            base_url = "https://api.deepseek.com"

    # For local providers, base_url is usually required, e.g., http://localhost:11434/v1

    if not api_key and request.provider not in ["local", "other"]:
        # Some local providers might not need a key, but public ones do.
        # We'll try anyway if it's local, but for others we might warn or just let it fail.
        pass

    try:
        client = AsyncOpenAI(api_key=api_key or "dummy", base_url=base_url)

        is_embedding = ("embedding" in (request.model_id or "").lower()) or (
            "open.bigmodel.cn" in (base_url or "").lower()
        )

        if is_embedding:
            emb = await client.embeddings.create(model=request.model_id, input="今天天气很好")
            vec = emb.data[0].embedding if emb and emb.data else []
            return LLMTestResponse(success=True, message=f"连接成功！向量维度：{len(vec)}")
        else:
            response = await client.chat.completions.create(
                model=request.model_id,
                messages=[{"role": "user", "content": "Hello, this is a connection test."}],
                max_tokens=10,
            )
            return LLMTestResponse(success=True, message=f"连接成功！响应：{response.choices[0].message.content}")

    except AuthenticationError:
        return LLMTestResponse(success=False, message="认证失败：无效的 API Key")
    except APITimeoutError:
        return LLMTestResponse(success=False, message="连接超时：请检查您的网络或 Base URL")
    except APIStatusError as e:
        error_msg = f"API 错误 ({e.status_code}): {e.message}"
        if e.status_code == 401:
            error_msg = "认证失败：无效的 API Key (401)"
        elif e.status_code == 402:
            error_msg = "余额不足：您的账户余额已耗尽 (402)"
        elif e.status_code == 400:
            # Handle common 400 errors like invalid model
            if "Model Not Exist" in str(e) or "model_not_found" in str(e):
                error_msg = "模型不存在：请检查模型ID是否正确 (400)"
            elif "1210" in str(e) or "参数有误" in str(e):
                error_msg = "请求无效：嵌入模型需要使用 Embeddings 接口，请确认 Base URL 与输入参数 (400)"
            else:
                error_msg = f"请求无效：{e.message} (400)"
        elif e.status_code == 404:
            error_msg = "未找到：无效的模型 ID 或 Base URL (404)"
        elif e.status_code == 429:
            error_msg = "请求受限：请求过于频繁 (429)"
        return LLMTestResponse(success=False, message=error_msg)
    except Exception as e:
        logger.error(f"LLM Connection Test Failed: {str(e)}")
        return LLMTestResponse(success=False, message=f"连接失败：{str(e)}")


@router.get("/models", response_model=List[LLMModelResponse])
async def list_llm_models(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """
    List all LLM models.
    """
    query = select(LLMModel).order_by(LLMModel.id.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    models = result.scalars().all()
    return models


@router.post("/models", response_model=LLMModelResponse)
async def create_llm_model(model_in: LLMModelCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new LLM model.
    """
    # Check if name already exists (optional, but good for UX)
    # query = select(LLMModel).filter(LLMModel.name == model_in.name)
    # result = await db.execute(query)
    # if result.scalars().first():
    #     raise HTTPException(status_code=400, detail="Model with this name already exists")

    new_model = LLMModel(
        name=model_in.name,
        provider=model_in.provider,
        model_id=model_in.model_id,
        model_type=model_in.model_type,
        api_key=model_in.api_key,
        base_url=model_in.base_url,
        is_active=model_in.is_active,
    )
    db.add(new_model)
    await db.commit()
    await db.refresh(new_model)
    return new_model


@router.put("/models/{model_id}", response_model=LLMModelResponse)
async def update_llm_model(model_id: int, model_in: LLMModelUpdate, db: AsyncSession = Depends(get_db)):
    """
    Update an existing LLM model.
    """
    result = await db.execute(select(LLMModel).filter(LLMModel.id == model_id))
    model = result.scalars().first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    update_data = model_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)

    await db.commit()
    await db.refresh(model)
    return model


@router.delete("/models/{model_id}")
async def delete_llm_model(model_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete an LLM model.
    """
    result = await db.execute(select(LLMModel).filter(LLMModel.id == model_id))
    model = result.scalars().first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    await db.delete(model)
    await db.commit()
    return {"status": "deleted", "id": model_id}
