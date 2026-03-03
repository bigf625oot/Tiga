import asyncio
import httpx
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("probe")

async def probe_server():
    base_url = "http://47.236.134.123:16547"
    token = "909c6806f2869d70dd67681e70b1aa68"
    
    endpoints = [
        "/",
        "/health",
        "/api/health",
        "/v1/health",
        "/info",
        "/api/info",
        "/v1/models" # OpenAI compatible
    ]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Probe/1.0"
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        print(f"Probing {base_url}...")
        
        for ep in endpoints:
            url = f"{base_url}{ep}"
            try:
                resp = await client.get(url, headers=headers)
                print(f"[{resp.status_code}] {ep}")
                if resp.status_code == 200:
                    print(f"   Response: {resp.text[:200]}")
            except Exception as e:
                print(f"[ERR] {ep}: {e}")

if __name__ == "__main__":
    asyncio.run(probe_server())
