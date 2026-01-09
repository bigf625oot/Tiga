from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.metrics_tool.prompt_service import generate_prompt
from app.services.metrics_tool.extraction_service import run_extraction

router = APIRouter()

class ExtractionRequest(BaseModel):
    indicator_name: str
    definition: str
    text_content: str
    output_format: str = "JSON"
    language: str = "CN"
    model: str = "qwen-plus"
    lite_mode: bool = False
    aliases: str = ""
    extraction_mode: str = "Multi"

class ExtractionResponse(BaseModel):
    status: str
    content: str
    prompt_used: Optional[str] = None

@router.post("/extract", response_model=ExtractionResponse)
async def extract_metric(request: ExtractionRequest):
    # 1. Generate Prompt
    prompt = generate_prompt(
        name=request.indicator_name,
        definition=request.definition,
        output_format=request.output_format,
        language=request.language,
        lite_mode=request.lite_mode,
        aliases=request.aliases,
        extraction_mode=request.extraction_mode
    )
    
    # 2. Run LLM
    result = await run_extraction(
        prompt=prompt,
        text_content=request.text_content,
        model=request.model
    )
    
    return ExtractionResponse(
        status=result["status"],
        content=result["content"],
        prompt_used=prompt
    )
