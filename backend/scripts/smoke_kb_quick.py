import json
import socket
import sys
import urllib.request


def _json_request(url: str, payload: dict, timeout: int = 30):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _sse_head(url: str, payload: dict, max_lines: int = 240, timeout: int = 60) -> str:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST",
    )
    out = []
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for _ in range(max_lines):
            b = r.readline()
            if not b:
                break
            s = b.decode("utf-8", "ignore")
            out.append(s)
            if s.startswith("event: done"):
                break
    return "".join(out)


def main():
    socket.setdefaulttimeout(60)
    base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173/api/v1"
    agent_id = sys.argv[2] if len(sys.argv) > 2 else "bb70bb02-ace0-49d8-b031-b72543164539"

    sess = _json_request(
        f"{base}/chat/sessions",
        {"title": "kbtest", "agent_id": agent_id, "mode": "quick"},
        timeout=30,
    )
    sid = sess.get("id")
    if not sid:
        raise RuntimeError(f"create session failed: {sess}")

    # Test payload with explicit agent_id (testing the new feature)
    payload = {
        "message": "知识库中有什么内容？请列出要点，并引用 doc id。",
        "stream": True,
        "mode": "quick",
        "intent": "chat",
        "enable_search": False,
        "enable_reasoning": False,
        "agent_id": agent_id,
        "attachments": [],
    }
    head = _sse_head(f"{base}/chat/sessions/{sid}/chat", payload, max_lines=360, timeout=60)
    print(f"SESSION_ID={sid}")
    print("---SSE_HEAD---")
    print(head)


if __name__ == "__main__":
    main()

