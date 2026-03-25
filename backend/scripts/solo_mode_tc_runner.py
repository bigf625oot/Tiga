import json
import os
import time
import uuid
import urllib.request
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
    with urllib.request.urlopen(req, timeout=timeout_s) as r:
        return json.loads(r.read().decode("utf-8"))


def _run_sse(url: str, payload: Dict[str, Any], timeout_s: int = 300) -> List[SseEvent]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=timeout_s)
    events: List[SseEvent] = []
    cur_event: Optional[str] = None
    cur_data: Optional[str] = None
    t0 = time.monotonic()

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

    return events


def _last_plan_steps(events: List[SseEvent]) -> Optional[List[Dict[str, Any]]]:
    for e in reversed(events):
        if e.event == "plan_step" and isinstance(e.data, list):
            if all(isinstance(x, dict) for x in e.data):
                return e.data  # type: ignore[return-value]
            return None
    return None


def _concat_think(events: List[SseEvent]) -> str:
    parts: List[str] = []
    for e in events:
        if e.event == "think":
            parts.append(str(e.data))
    return "".join(parts)


def _first_errors(events: List[SseEvent], n: int = 3) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for e in events:
        if e.event == "error":
            out.append({"t_ms": e.t_ms, "data": e.data})
            if len(out) >= n:
                break
    return out


def _status_tool_mentions(events: List[SseEvent]) -> List[Tuple[int, str]]:
    hits: List[Tuple[int, str]] = []
    for e in events:
        if e.event == "status" and isinstance(e.data, str) and "正在使用工具" in e.data:
            hits.append((e.t_ms, e.data))
    return hits


def analyze_tc_pl_01(events: List[SseEvent]) -> Dict[str, Any]:
    steps = _last_plan_steps(events) or []
    think = _concat_think(events)

    step_granularity_ok = len(steps) >= 3
    matrix_ref_ok = False
    if len(steps) >= 2:
        d = (steps[1].get("description") or "") if isinstance(steps[1], dict) else ""
        t = (steps[1].get("title") or "") if isinstance(steps[1], dict) else ""
        matrix_ref_ok = ("matrix.json" in d) or ("matrix.json" in t)

    reasoning_path_ok = ("先" in think and ("因为" in think or "依赖" in think)) or ("需要先" in think)

    return {
        "step_granularity": {"ok": step_granularity_ok, "steps_len": len(steps)},
        "matrix_ref_in_step2": {"ok": matrix_ref_ok},
        "reasoning_path_correctness": {"ok": reasoning_path_ok, "think_snippet": think[:300]},
        "plan_steps": steps[:10],
        "tool_mentions": _status_tool_mentions(events),
        "errors": _first_errors(events),
    }


def analyze_tc_pl_02(events: List[SseEvent]) -> Dict[str, Any]:
    steps = _last_plan_steps(events) or []
    think = _concat_think(events)
    tools = _status_tool_mentions(events)

    plan_has_weather = any(
        ("天气" in (s.get("title") or "") or "天气" in (s.get("description") or "")) for s in steps if isinstance(s, dict)
    )
    plan_has_shanghai = any(
        ("上海" in (s.get("title") or "") or "上海" in (s.get("description") or "")) for s in steps if isinstance(s, dict)
    )
    plan_has_modeling = any(
        ("综合" in (s.get("title") or "") or "建模" in (s.get("title") or "") or "综合" in (s.get("description") or "") or "建模" in (s.get("description") or ""))
        for s in steps
        if isinstance(s, dict)
    )

    return {
        "tool_selection": {"ok": len(tools) > 0, "tool_mentions": tools[:5]},
        "dynamic_expansion": {
            "ok": (len(steps) >= 3) and plan_has_weather and plan_has_shanghai,
            "steps_len": len(steps),
            "has_weather": plan_has_weather,
            "has_shanghai": plan_has_shanghai,
            "has_modeling_hint": plan_has_modeling,
        },
        "think_snippet": think[:300],
        "plan_steps": steps[:10],
        "errors": _first_errors(events),
    }


def run_case(base: str, message: str, enable_search: bool) -> Dict[str, Any]:
    session = _post_json(
        base + "/chat/sessions",
        {"title": "solo-tc-" + uuid.uuid4().hex[:8], "mode": "solo"},
        timeout_s=30,
    )
    sid = session["id"]
    events = _run_sse(
        base + f"/chat/sessions/{sid}/chat",
        {"message": message, "stream": True, "mode": "solo", "enable_reasoning": True, "enable_search": enable_search},
        timeout_s=300,
    )
    return {
        "session_id": sid,
        "event_counts": {
            "total": len(events),
            "plan_step": sum(1 for e in events if e.event == "plan_step"),
            "think": sum(1 for e in events if e.event == "think"),
            "status": sum(1 for e in events if e.event == "status"),
            "error": sum(1 for e in events if e.event == "error"),
        },
        "events": [{"t_ms": e.t_ms, "event": e.event, "data": e.data} for e in events],
    }


def main() -> None:
    base = "http://127.0.0.1:8000/api/v1"
    report: Dict[str, Any] = {"base": base, "cases": {}}

    tc_pl_01_msg = "先帮我生成一个 5x5 的随机整数矩阵并存入 matrix.json，然后读取该文件计算每一行的平均值，最后将平均值存为 Result.txt。"
    case1 = run_case(base, tc_pl_01_msg, enable_search=False)
    events1 = [SseEvent(**e) for e in case1["events"]]
    report["cases"]["TC-PL-01"] = {
        "run": {k: v for k, v in case1.items() if k != "events"},
        "analysis": analyze_tc_pl_01(events1),
    }

    tc_pl_02_msg = "分析一下最近三天的天气对上海旅游的影响。"
    case2 = run_case(base, tc_pl_02_msg, enable_search=True)
    events2 = [SseEvent(**e) for e in case2["events"]]
    report["cases"]["TC-PL-02"] = {
        "run": {k: v for k, v in case2.items() if k != "events"},
        "analysis": analyze_tc_pl_02(events2),
    }

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "solo_mode_tc_report.json")
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)
    
    print(f"\n[Done] Test run finished. Report saved to {out_path}")


if __name__ == "__main__":
    main()
