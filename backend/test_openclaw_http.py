import asyncio
import logging
import sys
import os

# Ensure backend directory is in python path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("openclaw.http").setLevel(logging.DEBUG)

from app.services.openclaw.clients.http.client import OpenClawHttpClient
from app.core.config import settings

async def test_openclaw_http():
    print(f"Testing connection to: {settings.OPENCLAW_BASE_URL}")
    print(f"Token present: {'Yes' if settings.OPENCLAW_GATEWAY_TOKEN or settings.OPENCLAW_TOKEN else 'No'}")
    
    client = OpenClawHttpClient(timeout=30.0)
    try:
        # 1. Test Health Check (Basic connectivity)
        print("\n--- Testing Health Check ---")
        health = await client.check_health()
        print(f"✅ Health Check Result: {health}")
        
        # 2. Test Tool Invocation (Auth check)
        # Using a simple tool like 'cron' list which should be safe
        print("\n--- Testing Tool Invocation (cron list) ---")
        result = await client.invoke("cron", {"action": "list"})
        print(f"✅ Tool Invocation Result: {result}")
        
    except Exception as e:
        print(f"\n❌ HTTP Connection Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(test_openclaw_http())
    except KeyboardInterrupt:
        pass
