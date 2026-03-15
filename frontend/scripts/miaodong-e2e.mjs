import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function nowStamp() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    if (next && !next.startsWith("--")) {
      out[key] = next;
      i++;
      continue;
    }
    out[key] = true;
  }
  return out;
}

async function exists(p) {
  try {
    await readFile(p);
    return true;
  } catch {
    return false;
  }
}

function joinUrl(baseUrl, pathname) {
  const u = new URL(baseUrl);
  const p = pathname.startsWith("/") ? pathname : `/${pathname}`;
  u.pathname = p;
  return u.toString();
}

function normalizeNewlines(s) {
  return String(s || "").replace(/\r\n/g, "\n");
}

function countSentencesZh(s) {
  const t = normalizeNewlines(s).trim();
  if (!t) return 0;
  const parts = t.split(/[。！？!?]+/).map((x) => x.trim()).filter(Boolean);
  return parts.length;
}

function safeIncludes(s, sub) {
  return normalizeNewlines(s).toLowerCase().includes(String(sub).toLowerCase());
}

function pickLastAssistantText(transcript) {
  for (let i = transcript.length - 1; i >= 0; i--) {
    const t = transcript[i];
    if (t.role === "assistant" && t.type === "combined_text") return t.content || "";
  }
  return "";
}

function extractAllAssistantText(transcript) {
  const combined = transcript.filter((t) => t.role === "assistant" && t.type === "combined_text").map((t) => t.content || "");
  if (combined.length) return combined.join("\n\n");
  return transcript.filter((t) => t.role === "assistant" && t.type === "text").map((t) => t.content || "").join("");
}

function markdownEscapeInline(s) {
  return String(s || "").replace(/[\\`]/g, "\\$&");
}

function truncate(s, n = 1800) {
  const t = String(s || "");
  return t.length > n ? `${t.slice(0, n)}…` : t;
}

function oneLine(s) {
  return normalizeNewlines(s).replace(/\s+/g, " ").trim();
}

function genLongMeetingNotesZh() {
  const people = ["张三（项目经理）", "李四（研发负责人）", "王五（测试负责人）", "赵六（产品）", "钱七（运维）"];
  const bullets = [];
  bullets.push("会议纪要（杂乱版）：");
  bullets.push("1. 先聊了天气和周末安排，略。");
  bullets.push("2. 进度：核心接口联调比计划晚了 2 周，原因是需求变更+接口字段反复调整。");
  bullets.push("3. 张三说本周必须拉齐范围，不然下周 Demo 交付不了。");
  bullets.push("4. 李四承认排期评估偏乐观，研发资源被临时抽走去救火。");
  bullets.push("5. 王五反馈：测试环境不稳定，回归阻塞，缺少自动化用例；有 3 个阻断 bug 仍未修复。");
  bullets.push("6. 赵六提到：上周又加了 2 个关键需求（权限与导出），但没有同步到里程碑。");
  bullets.push("7. 钱七说：发布窗口有限，灰度方案没定，监控告警规则也没准备好。");
  bullets.push("8. 决策点：需要一个明确负责人来推进“范围冻结+里程碑+阻断清零”。");
  bullets.push("9. 风险：外部依赖接口 SLA 不稳定；本周还要做一次安全扫描。");
  bullets.push("10. 任务：李四承诺周三前完成接口字段冻结并出对齐文档；王五周四给回归清单；钱七周五出灰度与监控方案。");
  bullets.push("11. 争议：赵六认为导出必须进本期，否则客户验收不过；李四认为先保主链路。");
  bullets.push("12. 结论：先保主链路，导出做降级版本，权限按最小可用实现。");
  bullets.push("13. 会后：有人说“下次别临时改了”，但没落实机制。");
  bullets.push(`参会：${people.join("、")}。`);
  while (bullets.join("\n").length < 2100) {
    bullets.push(`补充碎片：有人提到“日志埋点不全”“看板没人维护”“接口文档落后于实现”，以及“周五请假导致沟通断层”。`);
  }
  return bullets.join("\n");
}

function genNoisyTextWithCoreRequirement() {
  const chunks = [];
  chunks.push("哎最近真的太热了，办公室空调还坏了，修了两次也不行。");
  chunks.push("昨天同事说要去吃火锅，我没去，我在加班。");
  chunks.push("对了我们产品要做一个功能：用户上传一个 CSV，然后系统自动识别字段、做校验、把数据入库，并生成一份导入报告（成功/失败条数、失败原因、可下载失败明细）。");
  chunks.push("老板还在群里发了个表情包，说要效率。");
  chunks.push("另外希望导入过程有进度条，超大文件要分片，后台异步处理，前端能看到任务状态。");
  chunks.push("我刚才说的这些可能有点乱，你就抓重点。");
  while (chunks.join("\n").length < 1800) {
    chunks.push("随口一提：最近天气、咖啡、周末、以及一些无关的吐槽。");
  }
  return chunks.join("\n");
}

function genTenRoundsTechDiscussion() {
  const msgs = [
    "我们聊点技术：解释一下什么是幂等？",
    "数据库索引怎么选？",
    "接口超时常见原因有哪些？",
    "什么是缓存穿透/击穿/雪崩？",
    "前端首屏慢怎么排查？",
    "日志怎么设计更好？",
    "如何做灰度发布？",
    "CI/CD 的关键步骤有哪些？",
    "如何设计一个简单的权限系统？",
    "如何在不加机器的情况下提升吞吐？"
  ];
  return msgs.map((m) => ({ message: m }));
}

function genFiveSmallRounds() {
  const msgs = [
    "我喜欢函数式风格。",
    "我们团队代码风格不统一。",
    "上线经常出问题。",
    "我不太想写测试。",
    "你觉得我该先改哪里？"
  ];
  return msgs.map((m) => ({ message: m }));
}

function resolveTemplateStep(step) {
  const k = step.template;
  if (k === "long_meeting_notes_zh") return [{ message: genLongMeetingNotesZh() }];
  if (k === "noisy_text_with_core_requirement") return [{ message: genNoisyTextWithCoreRequirement() }];
  if (k === "ten_rounds_tech_discussion") return genTenRoundsTechDiscussion();
  if (k === "five_small_rounds") return genFiveSmallRounds();
  throw new Error(`Unknown template: ${k}`);
}

async function readSuite(suitePath) {
  const raw = await readFile(suitePath, "utf8");
  const suite = JSON.parse(raw);
  if (!suite || !Array.isArray(suite.cases)) throw new Error("Invalid suite format");
  return suite;
}

async function httpJson(method, url, body, headers = {}) {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json", ...headers },
    body: body ? JSON.stringify(body) : undefined
  });
  const text = await res.text();
  let json = null;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    json = null;
  }
  return { ok: res.ok, status: res.status, headers: Object.fromEntries(res.headers.entries()), text, json };
}

async function preflight(baseUrl) {
  const url = joinUrl(baseUrl, "/api/v1/health/");
  const res = await fetch(url);
  if (!res.ok) {
    const t = await res.text().catch(() => "");
    throw new Error(`Health check failed: ${res.status} ${t}`);
  }
}

async function createSession(baseUrl, title) {
  const url = joinUrl(baseUrl, "/api/v1/chat/sessions");
  const r = await httpJson("POST", url, { title, mode: "chat" });
  if (!r.ok || !r.json?.id) throw new Error(`Create session failed: ${r.status} ${truncate(r.text, 300)}`);
  return r.json.id;
}

async function deleteSession(baseUrl, sessionId) {
  const url = joinUrl(baseUrl, `/api/v1/chat/sessions/${sessionId}`);
  await fetch(url, { method: "DELETE" }).catch(() => null);
}

async function sendChatAndCollect(baseUrl, sessionId, payload) {
  const url = joinUrl(baseUrl, `/api/v1/chat/sessions/${sessionId}/chat`);
  const startedAt = new Date().toISOString();
  const startMs = Date.now();
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
    body: JSON.stringify(payload)
  });
  const headers = Object.fromEntries(res.headers.entries());
  if (!res.ok || !res.body) {
    const t = await res.text().catch(() => "");
    return {
      ok: false,
      status: res.status,
      headers,
      meta: {
        url,
        request: payload,
        startedAt,
        durationMs: Date.now() - startMs,
        bytesRead: 0,
        eventCounts: {},
        endedBy: "http_error"
      },
      transcript: [{ role: "assistant", type: "error", content: t }]
    };
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buf = "";
  const transcript = [];
  let assistantText = "";
  let assistantThink = "";
  let bytesRead = 0;
  const eventCounts = {};
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    if (value) bytesRead += value.byteLength;
    buf += decoder.decode(value, { stream: true });
    while (true) {
      const idx = buf.indexOf("\n\n");
      if (idx === -1) break;
      const frame = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      const lines = frame.split("\n").map((l) => l.trimEnd());
      const evLine = lines.find((l) => l.startsWith("event:"));
      const dataLine = lines.find((l) => l.startsWith("data:"));
      const event = evLine ? evLine.slice("event:".length).trim() : "message";
      const dataRaw = dataLine ? dataLine.slice("data:".length).trim() : "";
      eventCounts[event] = (eventCounts[event] || 0) + 1;
      if (event === "done") {
        transcript.push({ role: "assistant", type: "done", content: dataRaw });
        return {
          ok: true,
          status: res.status,
          headers,
          meta: {
            url,
            request: payload,
            startedAt,
            durationMs: Date.now() - startMs,
            bytesRead,
            eventCounts,
            endedBy: "done_event"
          },
          transcript,
          assistantText,
          assistantThink
        };
      }
      if (event === "text" || event === "think" || event === "status" || event === "chart" || event === "error" || event === "file") {
        let parsed = null;
        if (dataRaw && dataRaw !== "[DONE]") {
          try {
            parsed = JSON.parse(dataRaw);
          } catch {
            parsed = dataRaw;
          }
        }
        transcript.push({ role: "assistant", type: event, content: parsed });
        if (event === "text") assistantText += typeof parsed === "string" ? parsed : JSON.stringify(parsed);
        if (event === "think") assistantThink += typeof parsed === "string" ? parsed : JSON.stringify(parsed);
      } else {
        transcript.push({ role: "assistant", type: event, content: dataRaw });
      }
    }
  }
  return {
    ok: true,
    status: res.status,
    headers,
    meta: {
      url,
      request: payload,
      startedAt,
      durationMs: Date.now() - startMs,
      bytesRead,
      eventCounts,
      endedBy: "stream_end"
    },
    transcript,
    assistantText,
    assistantThink
  };
}

function extractMetaHttp(transcript) {
  return transcript.filter((t) => t.role === "meta" && t.type === "http").map((t) => t.content).filter(Boolean);
}

function findSnippet(text, needle, radius = 40) {
  const t = normalizeNewlines(text);
  const n = String(needle);
  const i = t.indexOf(n);
  if (i === -1) return null;
  const s = Math.max(0, i - radius);
  const e = Math.min(t.length, i + n.length + radius);
  return t.slice(s, e);
}

function buildDiagnostics(caseDef, transcript, evaluation) {
  const finalText = evaluation.finalText || "";
  const steps = transcript.filter((t) => t.role === "user" && t.type === "text").map((t) => t.content || "");
  const http = extractMetaHttp(transcript);
  const failed = (evaluation.results || []).filter((r) => !r.pass).map((r) => r.id);
  const passed = (evaluation.results || []).filter((r) => r.pass).map((r) => r.id);

  const issues = failed.map((id) => {
    const issue = { checkId: id, evidence: null, hypothesis: null, nextProbe: null };
    if (id === "does_not_mention_cloudnative") {
      const snippet = findSnippet(finalText, "云原生", 60);
      issue.evidence = snippet ? `命中禁词上下文：${oneLine(snippet)}` : "未定位到禁词命中位置（可能在非最终段落或被分词影响）";
      issue.hypothesis = "模型未严格执行“强制过滤”约束，或在解释/举例时自动带入默认术语。";
      issue.nextProbe = "追加一轮：要求仅输出方案要点列表，并重复声明“不要出现‘云原生’字样（包括标题/小节/括号）”。";
    } else if (id === "flags_false_premise_or_asks_for_evidence") {
      issue.evidence = "输出未明确指出“此前并未提到上市/需要确认依据”，而是默认接受了上市前提并继续给方案。";
      issue.hypothesis = "模型将用户话术当成已知背景，缺少对对话记录的溯源校验。";
      issue.nextProbe = "在同一 session 先问无关问题，再触发该用例，观察是否会溯源‘你刚才并未提到’。";
    } else if (id === "single_sentence") {
      issue.evidence = `句子数估计：${countSentencesZh(finalText)}；存在换行：${/\n/.test(finalText) ? "是" : "否"}`;
      issue.hypothesis = "模型优先满足“详尽步骤”，忽略“一句话”硬约束。";
      issue.nextProbe = "把硬约束前置并加格式限制：要求输出不包含换行且不含分号列表，仅用逗号串联。";
    } else if (id === "asks_time_clarification") {
      issue.evidence = `问号数量：${(normalizeNewlines(finalText).match(/[？?]/g) || []).length}`;
      issue.hypothesis = "模型把‘下午’当成已足够具体的时间窗口，未触发澄清。";
      issue.nextProbe = "同用例增加上文：提到‘下午 2 点会议’，再问‘订下午闹钟’，观察是否会默认 2 点。";
    } else {
      issue.evidence = `未通过检查项：${id}`;
      issue.hypothesis = "输出特征与启发式判定不匹配，或模型未覆盖该能力点。";
      issue.nextProbe = "查看用例输出 JSON，确认失败是否来自启发式误判还是模型缺失。";
    }
    return issue;
  });

  const evidence = {
    stepsCount: steps.length,
    finalTextChars: String(finalText).length,
    httpCalls: http.map((h) => ({
      url: h.url,
      startedAt: h.startedAt,
      durationMs: h.durationMs,
      status: h.status,
      contentType: h.headers?.["content-type"] || h.headers?.["Content-Type"] || null,
      bytesRead: h.bytesRead,
      endedBy: h.endedBy,
      eventCounts: h.eventCounts || {}
    }))
  };

  const phase1 = {
    summary: "可复现输入与边界证据已采集（请求体/响应头/事件计数/最终输出）。",
    reproduction: steps.map((s, i) => ({ step: i + 1, message: truncate(s, 240) })),
    boundaries: evidence.httpCalls
  };

  const phase2 = {
    summary: "将失败定位到具体检查项，并保留通过项作为对照。",
    passedChecks: passed,
    failedChecks: failed
  };

  const phase3 = {
    summary: "针对每个失败检查项生成单一假设与下一步最小验证。",
    issues
  };

  const phase4 = {
    summary: "当前输出为诊断与证据链，不直接改模型；建议先用最小探针确认假设后再谈修复。",
    nextActions: issues.map((x) => ({ checkId: x.checkId, nextProbe: x.nextProbe }))
  };

  return { evidence, phases: { phase1, phase2, phase3, phase4 } };
}

function renderDiagnosticsMarkdown(diag) {
  const lines = [];
  lines.push("### 诊断（systematic-debugging）");
  lines.push("");
  lines.push("**Phase 1：Root Cause Investigation（证据采集）**");
  lines.push(`- 输入步数：${diag.evidence.stepsCount}；最终输出长度：${diag.evidence.finalTextChars} 字符`);
  if (diag.evidence.httpCalls.length) {
    const c = diag.evidence.httpCalls[diag.evidence.httpCalls.length - 1];
    lines.push(`- HTTP：${c.status || ""}；Content-Type：${c.contentType || ""}；耗时：${c.durationMs}ms；bytes：${c.bytesRead}`);
    lines.push(`- SSE 事件计数：${Object.entries(c.eventCounts || {}).map(([k, v]) => `${k}=${v}`).join("，")}`);
  }
  lines.push("");
  lines.push("**Phase 2：Pattern Analysis（对照与差异）**");
  lines.push(`- 通过：${(diag.phases.phase2.passedChecks || []).join("，") || "无"}`);
  lines.push(`- 失败：${(diag.phases.phase2.failedChecks || []).join("，") || "无"}`);
  lines.push("");
  lines.push("**Phase 3：Hypothesis and Testing（假设与最小探针）**");
  for (const it of diag.phases.phase3.issues || []) {
    lines.push(`- ${it.checkId}`);
    lines.push(`  - 证据：${truncate(oneLine(it.evidence || ""), 220)}`);
    lines.push(`  - 假设：${truncate(oneLine(it.hypothesis || ""), 220)}`);
    lines.push(`  - 下一步验证：${truncate(oneLine(it.nextProbe || ""), 240)}`);
  }
  lines.push("");
  lines.push("**Phase 4：Implementation（执行建议）**");
  lines.push("- 先用最小探针确认失败类型（模型能力缺失 vs 启发式误判 vs 环境/协议问题），再进入修复。");
  return lines.join("\n");
}

function buildChecks() {
  const tools = [
    "midjourney",
    "stable diffusion",
    "dall",
    "flux",
    "adobe firefly",
    "ideogram",
    "leonardo",
    "playground",
    "canva",
    "krea",
    "comfyui"
  ];
  const checks = {};

  checks.has_sections = ({ text }) => {
    const t = normalizeNewlines(text);
    const lines = t.split("\n");
    const headingCount =
      lines.filter((l) => /^\s*#{1,6}\s+\S+/.test(l)).length +
      lines.filter((l) => /^\s*([一二三四五六七八九十]+|[0-9]{1,2})[、.]\s*\S+/.test(l)).length;
    const keyHits = ["本周", "进展", "问题", "风险", "下周", "计划", "行动项", "总结"].filter((k) => t.includes(k)).length;
    return headingCount >= 2 || keyHits >= 3;
  };

  checks.has_action_items = ({ text }) => {
    const t = normalizeNewlines(text);
    const has = ["行动项", "下一步", "下周", "TODO", "待办"].some((k) => t.includes(k));
    const bullet = t.split("\n").filter((l) => /^\s*[-*]\s+\S+/.test(l)).length;
    return has && bullet >= 2;
  };

  checks.asks_for_missing_info_or_placeholders = ({ text }) => {
    const t = normalizeNewlines(text);
    const q = (t.match(/[？?]/g) || []).length;
    const placeholders =
      ["待定", "TBD", "占位", "待补", "如未提供", "请补充", "请填写"].some((k) => t.includes(k)) ||
      /\[(请补充|请填写)[^\]]*\]/.test(t) ||
      /【(请补充|请填写)[^】]*】/.test(t);
    return q >= 1 || placeholders;
  };

  checks.has_markdown_table = ({ text }) => {
    const t = normalizeNewlines(text);
    const lines = t.split("\n");
    const sep = lines.some((l) => /^\s*\|?(\s*[-:]{3,}\s*\|)+\s*[-:]{3,}\s*\|?\s*$/.test(l));
    const row = lines.filter((l) => l.includes("|")).length;
    return sep && row >= 4;
  };

  checks.mentions_multiple_named_items = ({ text }) => {
    const t = normalizeNewlines(text).toLowerCase();
    const hit = tools.filter((x) => t.includes(x)).length;
    return hit >= 3;
  };

  checks.has_meeting_essentials = ({ text }) => {
    const t = normalizeNewlines(text);
    const hits = [
      /时间|日期|周一/.test(t),
      /地点|会议室|线上|腾讯会议|Zoom|Teams|飞书/.test(t),
      /参会|参与人|与会|相关同学/.test(t),
      /议程|Agenda|讨论项/.test(t),
      /准备|会前|材料/.test(t)
    ].filter(Boolean).length;
    return hits >= 4;
  };

  checks.tone_not_too_formal = ({ text }) => {
    const t = normalizeNewlines(text);
    const tooFormal = ["兹定于", "敬请", "特此通知", "务请"].some((k) => t.includes(k));
    const friendly = ["大家", "小伙伴", "辛苦", "一起"].some((k) => t.includes(k));
    return !tooFormal && friendly;
  };

  checks.has_numbered_outline = ({ text }) => {
    const t = normalizeNewlines(text);
    const num = t.split("\n").filter((l) => /^\s*\d+[\.)、]\s*\S+/.test(l)).length;
    return num >= 5;
  };

  checks.has_execution_level_details = ({ text }) => {
    const t = normalizeNewlines(text);
    const k = ["里程碑", "负责人", "指标", "交付", "时间表", "落地", "行动"].filter((x) => t.includes(x)).length;
    return k >= 2;
  };

  checks.has_interview_structure = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["自我介绍", "追问", "案例", "要点"].filter((k) => t.includes(k)).length >= 3;
  };

  checks.has_specific_examples = ({ text }) => {
    const t = normalizeNewlines(text);
    const has = ["例如", "比如", "举例"].some((k) => t.includes(k));
    const bullet = t.split("\n").filter((l) => /^\s*[-*]\s+\S+/.test(l)).length;
    return has || bullet >= 4;
  };

  checks.has_architecture_choice = ({ text }) => {
    const t = normalizeNewlines(text).toLowerCase();
    const hits = ["react", "vue", "svelte", "next", "vite", "pinia", "redux", "zustand", "tauri", "electron"].filter((k) => t.includes(k)).length;
    return hits >= 2;
  };

  checks.has_directory_structure = ({ text }) => {
    const t = normalizeNewlines(text);
    return /src\/|src\\|\n\s*[-*]\s*src\b|├──|└──/.test(t);
  };

  checks.asks_clarifying_questions = ({ text }) => {
    const t = normalizeNewlines(text);
    const q = (t.match(/[？?]/g) || []).length;
    return q >= 2;
  };

  checks.gives_common_causes = ({ text }) => {
    const t = normalizeNewlines(text).toLowerCase();
    const hits = ["flex", "grid", "overflow", "width", "box-sizing", "media", "responsive", "viewport", "position"].filter((k) => t.includes(k)).length;
    return hits >= 2;
  };

  checks.returns_refactored_code = ({ text }) => {
    const t = normalizeNewlines(text);
    const hasFence = /```[\s\S]*```/.test(t);
    const hasFunc = /function\s+\w+\s*\(|const\s+\w+\s*=\s*\(/.test(t);
    return hasFence && hasFunc;
  };

  checks.explains_changes_concisely = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["改动", "优化点", "原因", "说明"].some((k) => t.includes(k));
  };

  checks.has_step_by_step = ({ text }) => {
    const t = normalizeNewlines(text);
    const steps = t.split("\n").filter((l) => /^\s*(\d+[\.)、]|[-*])\s+\S+/.test(l)).length;
    return steps >= 4;
  };

  checks.mentions_windows_considerations = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["Windows", "WSL", "CUDA", "驱动", "显卡"].some((k) => t.includes(k));
  };

  checks.contains_regex_like = ({ text }) => {
    const t = normalizeNewlines(text);
    return /(\^|\(\?=|\(\?!|\\d|\[A-Z\]|\[a-z\])/.test(t);
  };

  checks.mentions_rule_limitations = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["连续", "同一字符", "正则", "实现难点", "需要额外校验"].some((k) => t.includes(k));
  };

  checks.has_day_by_day_plan = ({ text }) => {
    const t = normalizeNewlines(text);
    const day = t.split("\n").filter((l) => /^\s*(Day\s*\d+|第\s*\d+\s*天|\d+\s*\/\s*\d+)/i.test(l)).length;
    return day >= 5;
  };

  checks.mentions_health_risk_warning = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["高反", "海拔", "缺氧", "就医"].some((k) => t.includes(k));
  };

  checks.has_ranked_options = ({ text }) => {
    const t = normalizeNewlines(text);
    const num = t.split("\n").filter((l) => /^\s*\d+[\.)、]\s+\S+/.test(l)).length;
    return num >= 4;
  };

  checks.mentions_compliance = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["合规", "版权", "授权", "robots", "条款", "违法", "风险"].some((k) => safeIncludes(t, k));
  };

  checks.has_executable_plan = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["上午", "中午", "晚上", "当天", "流程", "步骤"].filter((k) => t.includes(k)).length >= 3;
  };

  checks.has_multiple_variants = ({ text }) => {
    const t = normalizeNewlines(text);
    const hit = ["方案A", "方案B", "方案C"].filter((k) => t.includes(k)).length;
    return hit >= 2 || /三套|3\s*套|三个方案/.test(t);
  };

  checks.has_4week_plan = ({ text }) => {
    const t = normalizeNewlines(text);
    const hit = ["第1周", "第2周", "第3周", "第4周"].filter((k) => t.includes(k)).length;
    return hit >= 3;
  };

  checks.considers_knee_constraint = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["膝盖", "低冲击", "不跳", "替代动作"].some((k) => t.includes(k));
  };

  checks.mentions_seek_medical_help_threshold = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["就医", "急诊", "胸痛", "晕厥", "呼吸困难"].some((k) => t.includes(k));
  };

  checks.uses_plain_language = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["先", "再", "如果", "比如"].filter((k) => t.includes(k)).length >= 2;
  };

  checks.uses_analogy_and_caveats = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["类比", "比喻", "打个比方"].some((k) => t.includes(k)) && ["不是完全", "不等同", "只是帮助理解"].some((k) => t.includes(k));
  };

  checks.avoids_obvious_misconceptions = ({ text }) => {
    const t = normalizeNewlines(text);
    return !/超光速|瞬间传信息|直接通信/.test(t);
  };

  checks.is_interactive = ({ text }) => {
    const t = normalizeNewlines(text).trim();
    const lines = t.split("\n").filter(Boolean);
    const hasServer = /服务员|waiter/i.test(t);
    const endsQuestion = /[？?]$/.test(t);
    return hasServer && endsQuestion && lines.length <= 4;
  };

  checks.does_not_continue_without_user = ({ text }) => {
    const t = normalizeNewlines(text);
    const hasBoth = /顾客：|Customer:|你：/.test(t) && /服务员：|Waiter:/.test(t);
    return !hasBoth;
  };

  checks.outputs_polished_text = ({ text }) => {
    const t = normalizeNewlines(text);
    return /Dear|Hi|Hello/.test(t) && /Best regards|Sincerely|Thanks|Thank you/i.test(t);
  };

  checks.tone_professional = ({ text }) => {
    const t = normalizeNewlines(text);
    return /could you|would you|i would appreciate|at your earliest convenience/i.test(t.toLowerCase());
  };

  checks.is_three_sentences_or_less = ({ text }) => {
    return countSentencesZh(text) <= 3;
  };

  checks.mentions_accountability_and_next_steps = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["负责", "责任", "Owner", "下一步", "接下来"].some((k) => safeIncludes(t, k));
  };

  checks.extracts_core_requirements = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["CSV", "导入", "校验", "入库", "报告", "进度"].filter((k) => safeIncludes(t, k)).length >= 3;
  };

  checks.five_bullets_or_less = ({ text }) => {
    const t = normalizeNewlines(text);
    const bullets = t.split("\n").filter((l) => /^\s*([-*]|\d+[\.)、])\s+/.test(l)).length;
    return bullets <= 5 && bullets >= 1;
  };

  checks.acknowledges_updated_constraint = ({ text }) => safeIncludes(text, "50") || safeIncludes(text, "五十");

  checks.proposes_tradeoffs = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["砍", "保留", "必须", "可选", "降级"].filter((k) => t.includes(k)).length >= 2;
  };

  checks.outputs_markdown_mindmap = ({ text }) => {
    const t = normalizeNewlines(text);
    const indented = t.split("\n").filter((l) => /^\s{2,}[-*]\s+/.test(l)).length;
    const root = t.split("\n").filter((l) => /^\s*[-*]\s+/.test(l)).length;
    return root >= 3 && indented >= 2;
  };

  checks.covers_multiple_points = ({ text }) => {
    const t = normalizeNewlines(text);
    const keys = ["接口", "数据库", "缓存", "前端", "监控", "慢查询", "P95", "第三方"].filter((k) => t.includes(k)).length;
    return keys >= 3;
  };

  checks.is_single_paragraph = ({ text }) => {
    const t = normalizeNewlines(text).trim();
    return !/\n\s*\n/.test(t) && t.split("\n").filter(Boolean).length <= 6;
  };

  checks.is_deduplicated = ({ text }) => {
    const t = normalizeNewlines(text);
    return t.length <= 450 && ["进度", "需求", "风险", "负责人", "里程碑"].filter((k) => t.includes(k)).length >= 2;
  };

  checks.mentions_cat_name = ({ text }) => safeIncludes(text, "大黄") && safeIncludes(text, "猫");

  checks.gives_pet_health_advice = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["疫苗", "驱虫", "体检", "注意"].filter((k) => t.includes(k)).length >= 2;
  };

  checks.references_server_constraint = ({ text }) => safeIncludes(text, "3") || safeIncludes(text, "三台");

  checks.has_phased_plan = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["阶段", "短期", "中期", "长期"].filter((k) => t.includes(k)).length >= 2;
  };

  checks.explicitly_reverses_conclusion = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["反转", "相反", "改为", "之前", "现在"].filter((k) => t.includes(k)).length >= 2;
  };

  checks.explains_reversal = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["因为", "因此", "导致"].some((k) => t.includes(k));
  };

  checks.maintains_role_tone = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["毒舌", "直说", "糟糕", "烂", "别这样"].some((k) => t.includes(k));
  };

  checks.gives_code_review_points = ({ text }) => {
    const t = normalizeNewlines(text);
    const bullets = t.split("\n").filter((l) => /^\s*[-*]\s+\S+/.test(l)).length;
    const hits = ["边界", "测试", "命名", "类型", "可读性", "异常"].filter((k) => t.includes(k)).length;
    return bullets >= 2 || hits >= 3;
  };

  checks.explains_prior_recommendation = ({ text }) => {
    const t = normalizeNewlines(text);
    const has3 = /3\s*个|三个|三点|三方面/.test(t);
    const hits = ["功能", "性能", "运维", "生态", "特性"].filter((k) => t.includes(k)).length;
    return has3 && hits >= 2;
  };

  checks.mentions_when_memcached_fits = ({ text }) => safeIncludes(text, "memcached");

  checks.disambiguates_pronoun = ({ text }) => safeIncludes(text, "python") || safeIncludes(text, "java");

  checks.asks_user_goal_or_constraints = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["你更想", "你的目标", "你准备", "你要做什么"].some((k) => t.includes(k)) || (t.match(/[？?]/g) || []).length >= 1;
  };

  checks.asks_time_clarification = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["几点", "时间", "具体", "下午几点"].some((k) => t.includes(k)) && (t.match(/[？?]/g) || []).length >= 1;
  };

  checks.explains_metaphor = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["意思是", "比喻", "形容"].some((k) => t.includes(k));
  };

  checks.gives_actionable_advice = ({ text }) => {
    const t = normalizeNewlines(text);
    const bullets = t.split("\n").filter((l) => /^\s*[-*]\s+\S+/.test(l)).length;
    return bullets >= 3 || ["下一步", "建议", "行动"].filter((k) => t.includes(k)).length >= 2;
  };

  checks.does_not_mention_cloudnative = ({ text }) => !normalizeNewlines(text).includes("云原生");

  checks.provides_solution = ({ text }) => normalizeNewlines(text).trim().length >= 200;

  checks.switches_to_indexing_architecture = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["索引", "抓取", "去重", "更新", "robots"].filter((k) => safeIncludes(t, k)).length >= 2;
  };

  checks.mentions_time_pressure = ({ text }) => ["下周", "时间", "赶", "期限"].some((k) => normalizeNewlines(text).includes(k));

  checks.makes_choice = ({ text }) => /选\s*A|选\s*B|选择\s*A|选择\s*B|A\s*方案|B\s*方案/.test(normalizeNewlines(text));

  checks.single_sentence = ({ text }) => {
    const t = normalizeNewlines(text).trim();
    return countSentencesZh(t) <= 1 && t.split("\n").filter(Boolean).length <= 2;
  };

  checks.addresses_constraint_conflict = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["一句话", "详尽", "限制", "无法同时"].some((k) => t.includes(k));
  };

  checks.contains_code_and_comments = ({ text }) => {
    const t = normalizeNewlines(text);
    const hasPy = /```python[\s\S]*```/.test(t) || /def\s+f\s*\(/.test(t);
    const hasComment = /#\s*\S+/.test(t);
    return hasPy && hasComment;
  };

  checks.has_classical_chinese_flavor = ({ text }) => /子曰|夫|盖|是故|君子/.test(normalizeNewlines(text));

  checks.uses_prior_context = ({ text }) => ["首屏", "接口", "5 秒", "3 秒"].filter((k) => normalizeNewlines(text).includes(k)).length >= 1;

  checks.provides_optimization_plan = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["排查", "优先级", "方案", "步骤"].filter((k) => t.includes(k)).length >= 2;
  };

  checks.flags_false_premise_or_asks_for_evidence = ({ text }) => {
    const t = normalizeNewlines(text);
    return ["你刚才", "没有提到", "未提到", "我没看到", "请确认", "依据"].some((k) => t.includes(k));
  };

  return checks;
}

function evalCase(caseDef, transcript) {
  const checks = buildChecks();
  const allText = extractAllAssistantText(transcript);
  const finalText = pickLastAssistantText(transcript) || allText;
  const results = [];
  for (const c of caseDef.checks || []) {
    const fn = checks[c];
    if (!fn) {
      results.push({ id: c, pass: false, reason: "unknown_check" });
      continue;
    }
    let pass = false;
    try {
      pass = !!fn({ text: finalText, allText, transcript });
    } catch {
      pass = false;
    }
    results.push({ id: c, pass });
  }
  const passCount = results.filter((r) => r.pass).length;
  const score = results.length ? Math.round((passCount / results.length) * 100) : 0;
  return { pass: passCount === results.length, score, results, finalText };
}

function renderMarkdownReport(run) {
  const lines = [];
  lines.push(`# 秒懂-全链路语义理解测试报告`);
  lines.push("");
  lines.push(`- 运行时间：${run.startedAt}`);
  lines.push(`- Base URL：${run.baseUrl}`);
  lines.push(`- Suite：${markdownEscapeInline(run.suitePath)}`);
  lines.push(`- Session：${markdownEscapeInline(run.sessionId || "")}`);
  lines.push(`- 用例数：${run.cases.length}`);
  lines.push("");
  lines.push(`| 用例 | 分组 | 结果 | 得分 | 检查项 |`);
  lines.push(`|---|---|---:|---:|---|`);
  for (const c of run.cases) {
    const ok = c.evaluation.pass ? "PASS" : "FAIL";
    const checks = (c.evaluation.results || []).map((r) => `${r.pass ? "✅" : "❌"}${r.id}`).join(" ");
    lines.push(`| ${markdownEscapeInline(c.id)} | ${markdownEscapeInline(c.group)} | ${ok} | ${c.evaluation.score} | ${checks} |`);
  }
  lines.push("");
  for (const c of run.cases) {
    lines.push(`## ${c.group} / ${c.title} (${c.id})`);
    lines.push("");
    lines.push(`- 结果：${c.evaluation.pass ? "PASS" : "FAIL"}（${c.evaluation.score}）`);
    lines.push(`- 检查项：${(c.evaluation.results || []).map((r) => `${r.pass ? "通过" : "失败"}:${r.id}`).join("，")}`);
    lines.push("");
    lines.push(`### 最终输出（截断）`);
    lines.push("");
    lines.push("```text");
    lines.push(truncate(c.evaluation.finalText || "", 2600));
    lines.push("```");
    lines.push("");
    if (c.diagnostics) {
      lines.push(renderDiagnosticsMarkdown(c.diagnostics));
      lines.push("");
    }
  }
  return lines.join("\n");
}

async function main() {
  const args = parseArgs(process.argv);
  const baseUrl = args.baseUrl || "http://localhost:5173";
  const filter = args.filter ? String(args.filter) : null;
  const keepSessions = !!args.keepSessions;
  const providedSessionId = args.sessionId ? String(args.sessionId) : null;
  const outDir = args.outDir ? path.resolve(args.outDir) : path.resolve(process.cwd(), "docs/Agent/测试用例");
  const stamp = nowStamp();

  const defaultSuiteA = path.resolve(process.cwd(), "docs/Agent/测试用例/秒懂-全链路测试套件.json");
  const defaultSuiteB = path.resolve(__dirname, "../../docs/Agent/测试用例/秒懂-全链路测试套件.json");
  const suitePath = args.suite ? path.resolve(args.suite) : (await exists(defaultSuiteA) ? defaultSuiteA : defaultSuiteB);
  const suite = await readSuite(suitePath);

  const selected = (suite.cases || []).filter((c) => (filter ? new RegExp(filter).test(c.id) : true));
  if (!selected.length) throw new Error("No cases selected");

  await mkdir(outDir, { recursive: true });
  await preflight(baseUrl);
  const sessionId = providedSessionId || (await createSession(baseUrl, `秒懂E2E ${stamp}`));
  const defaults = suite.defaults || {};

  const run = {
    startedAt: new Date().toISOString(),
    baseUrl,
    suitePath,
    sessionId,
    cases: []
  };

  try {
    for (const c of selected) {
      const transcript = [];
      const expandedSteps = [];
      for (const s of c.steps || []) {
        if (s.template) expandedSteps.push(...resolveTemplateStep(s));
        else expandedSteps.push(s);
      }
      for (const s of expandedSteps) {
        const payload = {
          message: s.message,
          stream: true,
          mode: s.mode ?? null,
          intent: s.intent ?? null,
          strict_mode: s.strict_mode ?? defaults.strict_mode ?? false,
          threshold: s.threshold ?? defaults.threshold ?? 0.85,
          debug: s.debug ?? defaults.debug ?? false,
          attachments: s.attachments ?? [],
          enable_search: s.enable_search ?? defaults.enable_search ?? true
        };
        transcript.push({ role: "user", type: "text", content: s.message });
        const r = await sendChatAndCollect(baseUrl, sessionId, payload);
        transcript.push({
          role: "meta",
          type: "http",
          content: { ...(r.meta || {}), status: r.status, headers: r.headers }
        });
        transcript.push(...(r.transcript || []));
        transcript.push({ role: "assistant", type: "combined_text", content: r.assistantText || "" });
      }
      const evaluation = evalCase(c, transcript);
      const diagnostics = buildDiagnostics(c, transcript, evaluation);
      run.cases.push({
        id: c.id,
        group: c.group,
        title: c.title,
        evaluation,
        diagnostics,
        transcript
      });
      const perCaseRawPath = path.join(outDir, `秒懂-用例输出-${c.id}-${stamp}.json`);
      await writeFile(perCaseRawPath, JSON.stringify(run.cases[run.cases.length - 1], null, 2), "utf8");
    }
  } finally {
    if (!providedSessionId && !keepSessions) await deleteSession(baseUrl, sessionId);
  }

  const rawPath = path.join(outDir, `秒懂-全链路测试结果-${stamp}.json`);
  await writeFile(rawPath, JSON.stringify(run, null, 2), "utf8");

  const mdPath = path.join(outDir, `秒懂-全链路测试报告-${stamp}.md`);
  const md = renderMarkdownReport(run);
  await writeFile(mdPath, md, "utf8");

  process.stdout.write(`${mdPath}\n${rawPath}\n`);
}

main().catch((e) => {
  process.stderr.write(String(e?.stack || e) + "\n");
  process.exit(1);
});
