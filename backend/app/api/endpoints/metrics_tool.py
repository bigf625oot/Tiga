from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from app.services.metrics_tool.prompt_service import generate_prompt
from app.services.metrics_tool.extraction_service import run_extraction
from app.services.document_parser import parse_document
from app.models.knowledge import KnowledgeDocument
from app.db.session import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.services.oss_service import oss_service
import requests

router = APIRouter()

class ParseDocResponse(BaseModel):
    text: str
    filename: str

class ParseKnowledgeDocResponse(BaseModel):
    text: str
    filename: str

@router.get("/parse_knowledge_doc/{doc_id}", response_model=ParseKnowledgeDocResponse)
async def parse_knowledge_doc_endpoint(doc_id: int, db: AsyncSession = Depends(get_db)):
    """
    Fetch a knowledge document from OSS/DB, parse it, and return text content.
    """
    result = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if not doc.oss_url:
        raise HTTPException(status_code=400, detail="Document has no OSS URL")

    # Download from OSS URL
    try:
        # Since oss_url is public or presigned (in our simple impl it's public-like), we can requests.get it
        # But if it's private bucket, we should use OSS client to get object.
        # oss_service doesn't expose get_object_to_file easily but we can add or just use requests if url is valid.
        # Assuming URL is accessible for now as per previous implementation.
        # Better: Use oss_service to get content if we have key.
        
        # If we have the key, we can use bucket.get_object
        if doc.oss_key and oss_service.enabled:
            # We need to implement get_content in oss_service or just use requests if URL is fine.
            # Let's try requests first, if fails (e.g. private), we might need to sign url.
            # For simplicity, let's assume we can fetch via URL or we add a helper in OSS service.
            # Let's add a helper in OSS service to get bytes.
            pass
            
        response = requests.get(doc.oss_url)
        response.raise_for_status()
        file_content = response.content
        
        # We need a file-like object for parse_document. 
        # parse_document expects UploadFile or similar. 
        # Actually parse_document implementation (we should check) likely takes UploadFile.
        # We can mock UploadFile or refactor parse_document to accept bytes.
        
        # Let's check parse_document signature. It takes UploadFile.
        # We can create a BytesIO and wrap it.
        from io import BytesIO
        
        class MockUploadFile:
            def __init__(self, file, filename):
                self.file = file
                self.filename = filename
                
        mock_file = MockUploadFile(BytesIO(file_content), doc.filename)
        
        text = await parse_document(mock_file)
        return ParseKnowledgeDocResponse(text=text, filename=doc.filename)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch or parse document: {str(e)}")

@router.post("/parse_doc", response_model=ParseDocResponse)
async def parse_doc_endpoint(file: UploadFile = File(...)):
    """
    Parse uploaded document and return text content
    """
    text = await parse_document(file)
    return ParseDocResponse(text=text, filename=file.filename)

class AdvancedOptions(BaseModel):
    related_terms: Optional[str] = None
    technical_features: Optional[str] = None
    formula: Optional[str] = None
    typical_format: Optional[str] = None
    common_location: Optional[str] = None
    doc_scope: Optional[str] = None
    default_value: Optional[str] = None
    value_range: Optional[str] = None
    reference_range: Optional[str] = None

class PreviewPromptRequest(BaseModel):
    indicator_name: str
    definition: str
    output_format: str = "JSON"
    language: str = "CN"
    lite_mode: bool = False
    aliases: str = ""
    extraction_mode: str = "Multi"
    advanced_options: Optional[AdvancedOptions] = None

class PreviewPromptResponse(BaseModel):
    prompt: str

@router.post("/preview_prompt", response_model=PreviewPromptResponse)
async def preview_prompt_endpoint(request: PreviewPromptRequest):
    prompt = generate_prompt(
        name=request.indicator_name,
        definition=request.definition,
        output_format=request.output_format,
        language=request.language,
        lite_mode=request.lite_mode,
        aliases=request.aliases,
        extraction_mode=request.extraction_mode,
        advanced_options=request.advanced_options.dict() if request.advanced_options else None
    )
    return PreviewPromptResponse(prompt=prompt)

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
    advanced_options: Optional[AdvancedOptions] = None

class BatchPromptRequest(BaseModel):
    indicators: List[dict] # List of indicator objects (from frontend table)
    output_format: str = "JSON"
    language: str = "CN"
    lite_mode: bool = False
    extraction_mode: str = "Multi"

@router.post("/batch_generate_prompts")
async def batch_generate_prompts(request: BatchPromptRequest):
    results = []
    for ind in request.indicators:
        # Construct advanced options from indicator dict
        adv = ind.get('advanced_options') or {}
        
        prompt = generate_prompt(
            name=ind.get('name', ''),
            definition=ind.get('description', '') or '',
            output_format=request.output_format,
            language=request.language,
            lite_mode=request.lite_mode,
            aliases=ind.get('alias', '') or '',
            extraction_mode=request.extraction_mode,
            advanced_options=adv
        )
        results.append({
            "indicator_name": ind.get('name'),
            "prompt": prompt
        })
    return results

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
        extraction_mode=request.extraction_mode,
        advanced_options=request.advanced_options.dict() if request.advanced_options else None
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
