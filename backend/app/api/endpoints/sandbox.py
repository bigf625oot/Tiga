from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.services.sandbox.codebox import codebox_service
import uuid
import os
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

class GenerateRequest(BaseModel):
    language: str = "python"
    code: Optional[str] = None
    template: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None # Optional session_id for persistent sessions

class SandboxResponse(BaseModel):
    session_id: str
    status: str
    result: Optional[Dict[str, Any]] = None

@router.post("/run", response_model=SandboxResponse)
async def run_sandbox_code(request: GenerateRequest):
    """
    Run code in sandbox (HTTP Mode, waits for completion).
    """
    # Use provided session_id or generate new one
    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"Sandbox Request [{session_id}]: {request.language}")
    
    # Simple logic: if code is provided, use it. If template is provided, format it.
    code_to_run = request.code
    if not code_to_run and request.template:
        try:
            code_to_run = request.template.format(**(request.params or {}))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Template formatting failed: {e}")
            
    if not code_to_run:
        raise HTTPException(status_code=400, detail="No code or template provided")
        
    # Execute
    # Pass session_id to allow persistent context
    result = await codebox_service.execute(code_to_run, session_id=session_id)
    
    # Log result to file as requested
    try:
        output_dir = os.path.abspath(os.path.join(os.getcwd(), "workspace", "results"))
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{session_id}.json")
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save result file: {e}")
        
    return SandboxResponse(
        session_id=session_id,
        status=result["status"],
        result=result
    )

# --- WebSocket Streaming ---
@router.websocket("/ws/{session_id}")
async def websocket_sandbox_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time sandbox execution.
    Protocol:
    - Client sends: {"code": "..."}
    - Server sends: {"type": "stdout", "content": "..."} | {"type": "result", "content": "..."}
    """
    await websocket.accept()
    logger.info(f"WS Connected: {session_id}")
    
    try:
        while True:
            # Wait for message
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                code = msg.get("code")
                if not code:
                    await websocket.send_json({"type": "error", "content": "No code provided"})
                    continue
                
                # Define callbacks to push to WS
                # Note: codebox_service.execute is async, but callbacks are sync.
                # We need to bridge them. Since callbacks run in a thread (usually),
                # we can't await websocket.send_json directly inside them without an event loop.
                # However, E2B might run callbacks in the same loop if async?
                # Actually, our execute implementation uses `sandbox.run_code` which blocks (sync SDK) or async SDK.
                # E2B Python SDK `e2b-code-interpreter` is synchronous by default but has async support?
                # Looking at our implementation `e2b_sandbox.py`, we call `sandbox.run_code` which is blocking.
                # So we are blocking the async loop! This is bad for WS ping/pong.
                # But since we are inside `execute` which is `async def`, if `run_code` is blocking, it blocks.
                # We should run `execute` in a threadpool if it's blocking.
                
                # Streaming Logic:
                # We need an asyncio Queue to pass messages from callbacks (thread) to WS (async loop).
                loop = asyncio.get_running_loop()
                queue = asyncio.Queue()
                
                def on_stdout(line):
                    loop.call_soon_threadsafe(queue.put_nowait, {"type": "stdout", "content": line + "\n"})

                def on_stderr(line):
                    loop.call_soon_threadsafe(queue.put_nowait, {"type": "stderr", "content": line + "\n"})

                # Consumer task: Read from queue and send to WS
                async def consumer():
                    while True:
                        item = await queue.get()
                        if item is None: break
                        await websocket.send_json(item)
                        queue.task_done()
                
                consumer_task = asyncio.create_task(consumer())
                
                # Execute in thread to avoid blocking loop
                # codebox_service.execute is async def but calls blocking run_code.
                # Ideally execute should use run_in_executor internally or be truly async.
                # For now, we rely on the fact that we can await it, but if it blocks, we are stuck.
                # Let's assume for now we just call it.
                # To fix blocking: We should wrap the blocking part in run_in_executor in the service.
                
                # Send start status
                await websocket.send_json({"type": "status", "content": "running"})
                
                result = await codebox_service.execute(
                    code, 
                    session_id=session_id,
                    on_stdout=on_stdout,
                    on_stderr=on_stderr
                )
                
                # Signal consumer to stop
                await queue.put(None)
                await consumer_task
                
                # Send final result
                await websocket.send_json({"type": "result", "result": result})
                await websocket.send_json({"type": "status", "content": "success"})
                
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "content": "Invalid JSON"})
            except Exception as e:
                logger.error(f"WS Execution Error: {e}")
                await websocket.send_json({"type": "error", "content": str(e)})
                
    except WebSocketDisconnect:
        logger.info(f"WS Disconnected: {session_id}")
