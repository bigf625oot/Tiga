from fastapi import APIRouter

router = APIRouter()

@router.post("/register")
async def register_llm_provider():
    return {"message": "LLM Provider registration endpoint"}

@router.post("/process")
async def process_recording_with_llm():
    return {"message": "Processing recording with LLM"}
