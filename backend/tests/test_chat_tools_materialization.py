import json
import uuid

def materialize_tools(cp_stream_events):
    materialized_tools = []
    if cp_stream_events:
        for ev in cp_stream_events:
            event_type = ev.get("event")
            content = ev.get("content")
            if event_type in ("tool_call", "call", "tool_start"):
                info = content
                if isinstance(info, str):
                    try:
                        info = json.loads(info)
                    except Exception:
                        info = {"tool": info}
                elif not isinstance(info, dict):
                    info = {"tool": str(info)}
                
                tool_id = info.get("tool_call_id") or info.get("id") or str(uuid.uuid4())
                tool_name = info.get("tool") or info.get("name") or "unknown_tool"
                args = info.get("args") or info.get("arguments") or {}
                materialized_tools.append({
                    "id": tool_id,
                    "name": tool_name,
                    "args": args,
                    "status": "running"
                })
            elif event_type in ("tool_output", "result", "tool_end", "tool_error"):
                info = content
                if isinstance(info, str):
                    try:
                        info = json.loads(info)
                    except Exception:
                        info = {"tool": "unknown_tool", "output": info}
                elif not isinstance(info, dict):
                    info = {"tool": "unknown_tool", "output": str(info)}
                
                tool_name = info.get("tool") or info.get("name")
                is_error = info.get("is_error", False)
                result_data = info.get("result") or info.get("output")
                if not isinstance(result_data, str):
                    result_data = json.dumps(result_data, ensure_ascii=False)
                
                for t in reversed(materialized_tools):
                    if t["name"] == tool_name and t["status"] == "running":
                        t["status"] = "error" if is_error else "success"
                        t["result"] = result_data
                        break
    return materialized_tools

def test_materialize_tools():
    events = [
        {"event": "tool_start", "content": '{"name": "search", "arguments": {"query": "test"}}'},
        {"event": "tool_output", "content": '{"name": "search", "output": "found 1 result"}'},
        {"event": "call", "content": {"tool": "write_file", "args": {"path": "test.txt"}}},
        {"event": "tool_error", "content": {"tool": "write_file", "is_error": True, "output": "Permission denied"}}
    ]
    
    tools = materialize_tools(events)
    assert len(tools) == 2
    
    assert tools[0]["name"] == "search"
    assert tools[0]["args"] == {"query": "test"}
    assert tools[0]["status"] == "success"
    assert tools[0]["result"] == "found 1 result"
    
    assert tools[1]["name"] == "write_file"
    assert tools[1]["args"] == {"path": "test.txt"}
    assert tools[1]["status"] == "error"
    assert tools[1]["result"] == "Permission denied"
    print("All tests passed!")

if __name__ == "__main__":
    test_materialize_tools()