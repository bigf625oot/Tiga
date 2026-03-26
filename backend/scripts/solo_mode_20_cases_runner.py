import json
import os
import time
import uuid
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class SseEvent:
    t_ms: int
    event: str
    data: Any

def _post_json(url: str, payload: Dict[str, Any], timeout_s: int = 30) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} {e.reason}")
        print(e.read().decode("utf-8"))
        raise

def _run_sse(url: str, payload: Dict[str, Any], timeout_s: int = 300) -> List[SseEvent]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST",
    )
    events: List[SseEvent] = []
    t0 = time.monotonic()
    
    try:
        resp = urllib.request.urlopen(req, timeout=timeout_s)
        cur_event: Optional[str] = None
        cur_data: Optional[str] = None

        for raw in resp:
            line = raw.decode("utf-8", errors="replace").rstrip("\n")
            if line.startswith("event: "):
                cur_event = line[len("event: ") :].strip()
            elif line.startswith("data: "):
                cur_data = line[len("data: ") :]
            elif line.strip() == "" and cur_event is not None:
                try:
                    data = json.loads(cur_data or "null")
                except Exception:
                    data = cur_data
                t_ms = int((time.monotonic() - t0) * 1000)
                events.append(SseEvent(t_ms=t_ms, event=cur_event, data=data))
                if cur_event == "done":
                    break
                cur_event = None
                cur_data = None
    except urllib.error.HTTPError as e:
        events.append(SseEvent(t_ms=int((time.monotonic() - t0) * 1000), event="http_error", data=str(e.code)))
    except Exception as e:
        events.append(SseEvent(t_ms=int((time.monotonic() - t0) * 1000), event="system_error", data=str(e)))

    return events

def _concat_text(events: List[SseEvent]) -> str:
    parts: List[str] = []
    for e in events:
        if e.event == "text":
            parts.append(str(e.data))
    return "".join(parts)

def run_case(base: str, sid: str, message: str, enable_search: bool = False) -> Dict[str, Any]:
    payload = {"message": message, "stream": True, "mode": "solo", "enable_reasoning": True, "enable_search": enable_search}
    events = _run_sse(
        base + f"/chat/sessions/{sid}/chat",
        payload,
        timeout_s=300,
    )
    
    error_msgs = [e.data for e in events if e.event == "error"]
    
    return {
        "message": message,
        "event_counts": {
            "total": len(events),
            "text": sum(1 for e in events if e.event == "text"),
            "think": sum(1 for e in events if e.event == "think"),
            "error": sum(1 for e in events if e.event == "error"),
            "http_error": sum(1 for e in events if e.event == "http_error")
        },
        "response_text": _concat_text(events),
        "duration_ms": events[-1].t_ms if events else 0,
        "error_msgs": error_msgs
    }

def main() -> None:
    base = "http://127.0.0.1:8000/api/v1"
    report: Dict[str, Any] = {"base": base, "cases": {}}

    print("Creating session for Context memory tests...")
    session = _post_json(base + "/chat/sessions", {"title": "solo-20-cases-" + uuid.uuid4().hex[:8], "mode": "solo"})
    sid = session["id"]

    test_cases = [
        # 1-4: Functionality
        {"id": "TC01", "desc": "基础问答", "msg": "你好，请回复'你好'"},
        {"id": "TC02", "desc": "数学计算", "msg": "15乘以15等于几？直接输出数字。"},
        {"id": "TC03", "desc": "逻辑推理", "msg": "树上有10只鸟，开枪打死1只，还剩几只？"},
        {"id": "TC04", "desc": "JSON格式", "msg": "请输出一个包含name和age的JSON对象，不要有额外内容"},
        
        # 5-6: Performance
        {"id": "TC05", "desc": "极短响应", "msg": "说1"},
        {"id": "TC06", "desc": "Token流速", "msg": "请输出1到50的数字，用逗号分隔"},
        
        # 7-10: Context Memory (Using same sid)
        {"id": "TC07", "desc": "设置上下文", "msg": "我的名字叫Alice"},
        {"id": "TC08", "desc": "回忆上下文", "msg": "我叫什么名字？"},
        {"id": "TC09", "desc": "追加上下文", "msg": "我今年30岁，是一名工程师"},
        {"id": "TC10", "desc": "综合上下文", "msg": "基于刚才的信息，写一段简短的自我介绍"},
        
        # 11-12: Window & Instructions
        {"id": "TC11", "desc": "中等文本理解", "msg": "总结以下文字的核心：苹果是一种水果，含有丰富的维生素C，颜色有红色、绿色和黄色。"},
        {"id": "TC12", "desc": "严格指令遵循", "msg": "不要回答任何多余的内容，只回复'Yes'"},
        
        # 13-15: Long Text Generation
        {"id": "TC13", "desc": "故事生成", "msg": "写一个约100字的微小说"},
        {"id": "TC14", "desc": "Markdown格式", "msg": "生成一个包含一级标题、无序列表和加粗的Markdown文档"},
        {"id": "TC15", "desc": "表格生成", "msg": "生成一个包含3行2列的Markdown表格，展示水果名称和颜色"},
        
        # 16-18: Code Generation
        {"id": "TC16", "desc": "Python代码", "msg": "写一个Python的HelloWorld程序"},
        {"id": "TC17", "desc": "Vue组件", "msg": "写一个Vue3的简单计数器组件，使用script setup"},
        {"id": "TC18", "desc": "SQL查询", "msg": "写一个SQL语句，查询users表中age大于18的记录"},
        
        # 19: Tools (if search is supported)
        {"id": "TC19", "desc": "工具调用", "msg": "查询一下今天北京的天气", "enable_search": True},
        
        # 20: Edge Cases
        {"id": "TC20", "desc": "特殊字符/空信息", "msg": "   \n\n\n   "},
    ]

    for i, tc in enumerate(test_cases):
        print(f"[{i+1}/20] Running {tc['id']} - {tc['desc']} ...")
        # create new session for non-context tests to avoid interference if needed
        # but the prompt says "上下文记忆", so it's good to keep them in the same session or create a new one.
        # Let's use the same session for 7-10, and maybe new ones for others, or just use one session for all to test context limits.
        # Let's just use the same session.
        
        enable_search = tc.get("enable_search", False)
        result = run_case(base, sid, tc["msg"], enable_search=enable_search)
        
        report["cases"][tc["id"]] = {
            "desc": tc["desc"],
            "run": result
        }
        
        print(f"  -> Done in {result['duration_ms']}ms. Text length: {len(result['response_text'])}")
        if result['event_counts']['error'] > 0 or result['event_counts']['http_error'] > 0:
            print(f"  -> Has Error! {result['event_counts']}")
            print(f"  -> Error Msgs: {result['error_msgs']}")
            
        time.sleep(2) # Prevent sqlite lock

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "solo_mode_20_cases_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)
    
    print(f"\n[Done] Test run finished. Report saved to {out_path}")

if __name__ == "__main__":
    main()
