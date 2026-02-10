import asyncio
import httpx
import uuid

BASE_URL = "http://localhost:8000/api/v1"

async def test_delete():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Create a session
        print("Creating session...")
        res = await client.post(f"{BASE_URL}/chat/sessions", json={"title": "Test Delete"})
        if res.status_code != 200:
            print(f"Failed to create session: {res.status_code} {res.text}")
            return
        
        session = res.json()
        session_id = session["id"]
        print(f"Created session: {session_id}")
        
        # 2. Delete the session
        print(f"Deleting session {session_id}...")
        res = await client.delete(f"{BASE_URL}/chat/sessions/{session_id}")
        print(f"Delete Status: {res.status_code}")
        print(f"Delete Response: {res.text}")
        
        # 3. Verify it's gone
        res = await client.get(f"{BASE_URL}/chat/sessions/{session_id}")
        print(f"Get Status (should be 404): {res.status_code}")

if __name__ == "__main__":
    asyncio.run(test_delete())
