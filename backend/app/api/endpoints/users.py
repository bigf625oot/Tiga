import os
import uuid
import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any

from app.services.storage.service import storage_service

router = APIRouter()

@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload user avatar
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Generate a unique file name
    ext = os.path.splitext(file.filename)[1]
    if not ext:
        ext = ".png"
    
    file_key = f"avatars/avatar_{uuid.uuid4().hex[:8]}_{int(time.time())}{ext}"
    
    try:
        # Read the file data
        data = await file.read()
        
        # Upload using storage service
        url = storage_service.upload_file_sync(file_key, data)
        
        # In a real scenario, we would save this URL to the database for the current user.
        # But since we just want to replace the frontend stub and there might not be user authentication setup,
        # returning the URL is enough for the frontend to display.
        
        return {
            "status": "success",
            "url": url,
            "message": "Avatar uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload avatar: {str(e)}")
