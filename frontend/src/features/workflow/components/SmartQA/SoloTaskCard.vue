<template>
  <div class="solo-task-card w-full flex flex-col gap-2.5 min-w-0">

    <!-- ── 1. Task status header (PRD §3.1 Task Header) ────────────── -->
    <div class="flex items-center gap-2.5">
      <!-- Status pill -->
      <div class="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold border"
           :class="statusPillClass">
        <span v-if="isRunning" class="relative flex h-1.5 w-1.5">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 bg-current"></span>
          <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-current"></span>
        </span>
        <CheckCircle2 v-else-if="!hasError" class="w-3 h-3" />
        <XCircle v-else class="w-3 h-3" />
        <span>{{ statusLabel }}</span>
      </div>

      <!-- Step count -->
      <span v-if="execSteps.length > 0" class="text-[11px] text-muted-foreground/40">
        {{ completedStepCount }}/{{ execSteps.length }} 步骤
      </span>

      <!-- Progress bar (只在有步骤时显示) -->
      <div v-if="execSteps.length > 1" class="flex-1 h-1 rounded-full bg-muted/50 overflow-hidden max-w-[80px]">
        <div
          class="h-full rounded-full transition-[width] duration-500"
          :class="hasError ? 'bg-destructive/60' : 'bg-primary'"
          :style="{ width: stepProgress + '%' }"
        />
      </div>

      <!-- Duration -->
      <span v-if="message.meta_data?.duration && !isRunning" class="text-[11px] text-muted-foreground/40 ml-auto">
        {{ formatDuration(message.meta_data.duration) }}
      </span>
    </div>

    <!-- ── 2. Thinking (PRD §2.1 Thought Chain) ─────────────────────── -->
    <ThoughtAccordion
      v-if="thinkingContent"
      :block="{ type: 'thought', content: thinkingContent.raw, state: thinkingContent.isPartial ? 'thinking' : 'collapsed' }"
    />

    <!-- ── 3. Mini Execution Logs (PRD §2.2) ────────────────────────── -->
    <!-- status 事件推送的阶段说明，单行紧凑摘要，可点击定位到右侧 -->
    <div v-if="miniLogs.length > 0"
         class="flex flex-col gap-1 pl-0.5 min-w-0">
      <div
        v-for="log in miniLogs"
        :key="log.id"
        class="flex items-center gap-1.5 text-[11px] text-muted-foreground/60 cursor-default group min-w-0"
      >
        <span class="w-1 h-1 rounded-full bg-muted-foreground/30 flex-shrink-0 group-last:bg-primary/50 group-last:animate-pulse"></span>
        <span class="truncate leading-relaxed font-mono min-w-0 flex-1">{{ typeof log.text === 'string' ? log.text : JSON.stringify(log.text) }}</span>
      </div>
    </div>

    <!-- ── 4. Execution step timeline (PRD §2.2 + §3.2) ─────────────── -->
    <div v-if="execSteps.length > 0" class="steps-timeline relative flex flex-col mt-0.5 min-w-0">
      <div v-for="(step, idx) in execSteps" :key="step.id" class="step-row relative flex gap-3 min-w-0">

        <!-- Vertical connector -->
        <div
          v-if="idx < execSteps.length - 1"
          class="absolute left-[8px] top-[22px] bottom-0 w-px z-0"
          :class="step.status === 'error' ? 'bg-destructive/25' : 'bg-border/40'"
        ></div>

        <!-- Status indicator -->
        <div class="flex-shrink-0 w-[18px] h-[18px] mt-1 z-10 flex items-center justify-center">
          <template v-if="step.status === 'running'">
            <span class="w-[16px] h-[16px] rounded-full border-2 border-primary border-t-transparent animate-spin inline-block"></span>
          </template>
          <CheckCircle2 v-else-if="step.status === 'done'" class="w-[16px] h-[16px] text-emerald-500" />
          <XCircle v-else-if="step.status === 'error'" class="w-[16px] h-[16px] text-destructive" />
          <div v-else class="w-[14px] h-[14px] rounded-full border-2 border-border/50 bg-background"></div>
        </div>

        <!-- Step body -->
        <div class="flex-1 min-w-0 pb-3.5">
          <!-- Step title + elapsed -->
          <div class="flex items-baseline justify-between gap-2 mb-1.5 min-w-0">
            <div class="text-[13px] font-medium leading-snug truncate flex-1"
                 :class="{
                   'text-foreground/90': step.status === 'running',
                   'text-muted-foreground/55': step.status === 'done',
                   'text-destructive/80': step.status === 'error',
                   'text-muted-foreground/35': step.status === 'pending',
                 }"
                 :title="typeof step.title === 'string' ? step.title : JSON.stringify(step.title)">
              {{ typeof step.title === 'string' ? step.title : JSON.stringify(step.title) }}
            </div>
            <span v-if="step.elapsed" class="text-[10px] text-muted-foreground/35 font-mono flex-shrink-0">
              {{ step.elapsed }}
            </span>
          </div>

          <!-- Tool calls (PRD §2.3 Tool Invocation) -->
          <div v-if="step.toolCalls.length > 0" class="flex flex-col gap-1.5">
            <ToolStatusCard
              v-for="tc in step.toolCalls"
              :key="tc.id"
              :tool-call="{ type: 'tool_call', call_id: tc.id, tool_name: tc.name, arguments: tc.args || {}, state: tc.status === 'error' ? 'error' : (tc.status === 'running' ? 'running' : 'success') }"
              :tool-result="tc.result ? { type: 'tool_result', call_id: tc.id, content: typeof tc.result === 'string' ? tc.result : JSON.stringify(tc.result), is_error: tc.status === 'error' } : undefined"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- ── 5. Orphan tool calls (no plan steps) ──────────────────────── -->
    <div v-if="orphanToolCalls.length > 0" class="flex flex-col gap-1.5 pl-[26px] min-w-0">
      <ToolStatusCard
        v-for="tc in orphanToolCalls"
        :key="tc.id"
        :tool-call="{ type: 'tool_call', call_id: tc.id, tool_name: tc.name, arguments: tc.args || {}, state: tc.status === 'error' ? 'error' : (tc.status === 'running' ? 'running' : 'success') }"
        :tool-result="tc.result ? { type: 'tool_result', call_id: tc.id, content: typeof tc.result === 'string' ? tc.result : JSON.stringify(tc.result), is_error: tc.status === 'error' } : undefined"
      />
    </div>

    <!-- ── 6. Global waiting placeholder ─────────────────────────────── -->
    <div v-if="isRunning && execSteps.length === 0 && orphanToolCalls.length === 0 && miniLogs.length === 0 && artifactLinks.length === 0"
         class="flex items-center gap-2 pl-0.5 py-1">
      <span class="relative flex h-2 w-2">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary/60 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-primary/80"></span>
      </span>
      <span class="text-xs text-muted-foreground/50 animate-pulse">正在规划任务...</span>
    </div>

    <!-- ── 7. Deliverables / Artifacts (PRD §2.4) ─────────────────────── -->
    <!-- 不直接渲染最终生成内容，仅展示沙箱产出文件或其他交付物的链接卡片 -->
    <template v-if="artifactLinks.length > 0 || inlineCodeBlocks.length > 0 || isRunning">

      <!-- Divider (only when execution context exists above) -->
      <div v-if="execSteps.length > 0 || orphanToolCalls.length > 0"
           class="flex items-center gap-2 mb-3">
        <div class="flex-1 h-px bg-border/30"></div>
        <span class="text-[10px] text-muted-foreground/35 font-semibold uppercase tracking-widest">交付物</span>
        <div class="flex-1 h-px bg-border/30"></div>
      </div>

      <!-- Artifact link cards -->
      <div v-if="artifactLinks.length > 0 || inlineCodeBlocks.length > 0" class="flex flex-col gap-2 min-w-0">
        <a
          v-for="(art, i) in artifactLinks"
          :key="'art-'+i"
          :href="art.url"
          target="_blank"
          rel="noopener noreferrer"
          class="flex items-center gap-3 px-3 py-2.5 bg-muted/20 border border-border/40 rounded-lg hover:bg-muted/40 hover:border-border/70 transition-all group/artifact no-underline min-w-0"
        >
          <!-- File-type icon badge -->
          <div class="flex-shrink-0 w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center">
            <FileText class="w-4 h-4 text-primary/70" />
          </div>

          <!-- Name + meta -->
          <div class="flex-1 min-w-0">
            <p class="text-[13px] font-medium text-foreground/80 truncate group-hover/artifact:text-foreground transition-colors">
              {{ art.name }}
            </p>
            <p class="text-[11px] text-muted-foreground/50 mt-0.5 font-mono">
              {{ art.type }}{{ art.size ? ` · ${formatFileSize(art.size)}` : '' }}
            </p>
          </div>

          <!-- Open-in-new icon -->
          <ExternalLink class="w-3.5 h-3.5 text-muted-foreground/30 group-hover/artifact:text-primary/60 flex-shrink-0 transition-colors" />
        </a>

        <!-- Inline Code Blocks as Artifacts -->
        <div
          v-for="(code, i) in inlineCodeBlocks"
          :key="'code-'+i"
          @click="openCodeArtifact(code)"
          class="flex items-center gap-3 px-3 py-2.5 bg-muted/20 border border-border/40 rounded-lg hover:bg-muted/40 hover:border-border/70 transition-all group/artifact cursor-pointer min-w-0"
        >
          <div class="flex-shrink-0 w-8 h-8 rounded-md bg-indigo-500/10 flex items-center justify-center">
            <Code2 class="w-4 h-4 text-indigo-500/70" />
          </div>

          <div class="flex-1 min-w-0">
            <p class="text-[13px] font-medium text-foreground/80 truncate group-hover/artifact:text-foreground transition-colors">
              {{ code.language.toUpperCase() }} 代码块片段
            </p>
            <p class="text-[11px] text-muted-foreground/50 mt-0.5 font-mono">
              {{ code.lines }} 行代码 · 点击预览
            </p>
          </div>

          <Maximize2 class="w-3.5 h-3.5 text-muted-foreground/30 group-hover/artifact:text-indigo-500/60 flex-shrink-0 transition-colors" />
        </div>
      </div>

      <!-- Streaming placeholder (no artifacts produced yet) -->
      <div v-else-if="isRunning" class="flex items-center gap-2 pl-0.5 py-1">
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary/60 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-primary/80"></span>
        </span>
        <span class="text-xs text-muted-foreground/50 animate-pulse">正在生成交付物...</span>
      </div>

    </template>

    <!-- ── 8. Chart ────────────────────────────────────────────────── -->
    <div v-if="chartOption"
         class="w-full bg-card rounded-lg border border-border shadow-sm overflow-hidden hover:shadow-md transition-shadow mt-1">
      <div class="h-64 w-full relative bg-card">
        <ChartFrame :option="chartOption" />
      </div>
    </div>

    <!-- ── 9. Knowledge references ────────────────────────────────── -->
    <div v-if="message.sources && message.sources.length > 0" class="mt-1 pt-2 border-t border-border/20">
      <div class="flex items-center gap-1.5 mb-2">
        <Link2 class="w-3 h-3 text-muted-foreground/40" />
        <span class="text-[10px] text-muted-foreground/50 font-semibold uppercase tracking-widest">信息来源</span>
      </div>
      <div class="flex flex-wrap gap-1.5">
        <div
          v-for="(ref, idx) in message.sources"
          :key="idx"
          class="flex items-center gap-1 px-2 py-0.5 bg-muted/20 border border-border/30 rounded text-[11px] text-muted-foreground/70 cursor-pointer hover:bg-muted/50 hover:text-foreground transition-all max-w-[200px] truncate"
          :title="ref.title"
          @click="$emit('locate-node', ref)"
        >
          <span class="font-mono text-muted-foreground/40 text-[10px]">{{ idx + 1 }}</span>
          <span class="truncate">{{ ref.title }}</span>
        </div>
      </div>
    </div>

    <!-- ── 10. Error callout ──────────────────────────────────────── -->
    <ErrorCallout
      v-if="message.error"
      :message="message.error"
      :can-retry="true"
      @retry="$emit('resend-message', message)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { CheckCircle2, XCircle, Link2, FileText, ExternalLink, Code2, Maximize2 } from 'lucide-vue-next';
import type { Message, StreamEventItem } from '../../../qa/types';
import ThoughtAccordion from '../../../chat/components/ThoughtAccordion.vue';
import ToolStatusCard from '../../../chat/components/ToolStatusCard.vue';
import PlanBlock from '../../../chat/components/PlanBlock.vue';
import ErrorCallout from '../../../qa/components/SmartQA/common/ErrorCallout.vue';
import ChartFrame from '../../../analytics/components/ChartFrame.vue';
import { useChartOptions } from '../../../qa/composables/useChart';
import { formatDuration, formatFileSize } from '../../../qa/utils/dateUtils';
import { useArtifact } from '../../../chat/context/ArtifactContext';

// ── Props & emits ───────────────────────────────────────────────────
const props = defineProps<{
  message: Message;
  isLast: boolean;
  isStreaming: boolean;
}>();

const emit = defineEmits(['locate-node', 'resend-message']);

const { processOption } = useChartOptions();
const artifactContext = useArtifact();

// ── Code block parser ────────────────────────────────────────────────
// Extract code blocks from markdown message content to show as artifacts
const inlineCodeBlocks = computed(() => {
  if (!props.message.content) return [];
  const content = props.message.content;
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  const blocks: { language: string; content: string; lines: number }[] = [];
  
  let match;
  while ((match = codeBlockRegex.exec(content)) !== null) {
    const lang = match[1] || 'text';
    const code = match[2].trim();
    // Only capture blocks that are long enough to warrant an artifact view
    const lines = code.split('\n').length;
    if (lines >= 5 && ['vue', 'html', 'javascript', 'typescript', 'python', 'json', 'sql'].includes(lang.toLowerCase())) {
      blocks.push({
        language: lang,
        content: code,
        lines
      });
    }
  }
  return blocks;
});

const openCodeArtifact = (code: { language: string; content: string }) => {
  artifactContext.openArtifact({
    type: code.language as any,
    content: code.content,
    language: code.language,
    title: `生成代码 (${code.language})`
  });
};

// ── Derived flags ───────────────────────────────────────────────────
const isRunning = computed(() => props.isStreaming && props.isLast);

// ── Chart ────────────────────────────────────────────────────────────
const chartOption = computed(() => processOption(props.message.chart_config));

// ── Artifact deliverables ────────────────────────────────────────────
// 优先级: message.artifacts (store 写入) > stream_events[event==='artifact']
// AgentArtifactCard: { file_name, file_size, url, type }
interface ArtifactLink { name: string; url: string; type: string; size?: number; }

const artifactLinks = computed<ArtifactLink[]>(() => {
  const result: ArtifactLink[] = [];

  // 1. Direct field written by chat store / workflow store onto the message
  if (props.message.artifacts && Array.isArray(props.message.artifacts)) {
    for (const a of props.message.artifacts as any[]) {
      if (a?.url) {
        result.push({
          name: a.file_name || a.name || '交付文件',
          url: a.url,
          type: a.type || 'file',
          size: a.file_size ?? a.size,
        });
      }
    }
  }

  // 2. Parsed from SSE stream_events — artifact events carry JSON payload in content
  const events = props.message.stream_events ?? [];
  for (const ev of events) {
    if (ev.event === 'artifact') {
      try {
        // content may arrive as a JSON string or already an object (via ev.raw)
        const card: any = ev.raw ?? (typeof ev.content === 'string' ? JSON.parse(ev.content) : ev.content);
        if (card?.url) {
          result.push({
            name: card.file_name || card.name || '交付文件',
            url: card.url,
            type: card.type || 'file',
            size: card.file_size ?? card.size,
          });
        }
      } catch {
        // Malformed event — skip silently
      }
    }
  }

  return result;
});

// ── Thinking content ─────────────────────────────────────────────────
const thinkingContent = computed(() => {
  if (props.message.reasoning) {
    return { raw: props.message.reasoning, isPartial: isRunning.value };
  }
  if (props.message.meta_data?.reasoning) {
    return { raw: props.message.meta_data.reasoning, isPartial: false };
  }
  return null;
});

// ── Mini Execution Logs (PRD §2.2) ───────────────────────────────────
// stream_events 中 type==='status' 的条目转为简洁的单行摘要
const miniLogs = computed(() => {
  const events = props.message.stream_events ?? [];
  const result: { id: string; text: string }[] = [];
  for (const ev of events) {
    if (ev.event === 'status' && ev.content) {
      const text = typeof ev.content === 'string' ? ev.content : JSON.stringify(ev.content);
      result.push({ id: ev.id, text });
    }
  }
  // 运行中只显示最新 3 条，避免挤占空间；结束后全量展示
  return isRunning.value ? result.slice(-3) : result;
});

// ── Tool call types ──────────────────────────────────────────────────
interface ResolvedToolCall {
  id: string;
  name: string;
  args?: Record<string, any>;
  result?: string;
  status: 'running' | 'success' | 'error';
}

interface ExecStep {
  id: string;
  title: string;
  status: 'pending' | 'running' | 'done' | 'error';
  toolCalls: ResolvedToolCall[];
  elapsed?: string; // 步骤耗时
}

// ── Core execution state ─────────────────────────────────────────────
const { execSteps, orphanToolCalls } = computeExecution();

function computeExecution() {
  const execSteps = computed<ExecStep[]>(() => {
    const steps = props.message.steps ?? [];
    const rawTools = props.message.tools ?? [];

    if (steps.length === 0) return [];

    const tools: ResolvedToolCall[] = buildResolvedTools(rawTools);

    return steps.map((s: any, idx: number) => {
      const chunkSize = Math.ceil(tools.length / steps.length) || 1;
      const stepTools = tools.filter((_: any, ti: number) =>
        ti >= idx * chunkSize && ti < (idx + 1) * chunkSize,
      );

      const hasRunningTool = stepTools.some(t => t.status === 'running');
      const hasErrorTool = stepTools.some(t => t.status === 'error');
      const isLastStep = idx === steps.length - 1;

      let status: ExecStep['status'] = 'done';
      if (hasErrorTool) status = 'error';
      else if (hasRunningTool || (isRunning.value && isLastStep && stepTools.length === 0)) status = 'running';
      else if (!isRunning.value || !isLastStep) status = 'done';

      let title = s.content || s.description || s.title || `步骤 ${idx + 1}`;
      if (typeof title !== 'string') {
          title = JSON.stringify(title);
      }

      return {
        id: String(s.step ?? s.id ?? idx),
        title,
        status,
        toolCalls: stepTools,
        elapsed: undefined, // 后端未下发耗时时留空
      };
    });
  });

  const orphanToolCalls = computed<ResolvedToolCall[]>(() => {
    const steps = props.message.steps ?? [];
    const rawTools = props.message.tools ?? [];
    if (steps.length > 0) return [];
    return buildResolvedTools(rawTools);
  });

  return { execSteps, orphanToolCalls };
}

function buildResolvedTools(rawTools: any[]): ResolvedToolCall[] {
  if (!rawTools || rawTools.length === 0) return [];
  return rawTools.map((t: any, idx: number) => ({
    id: t.id || String(idx),
    name: t.name || '未知工具',
    args: t.args ?? t.arguments,
    result: t.result,
    status: t.status || 'running',
  }));
}

// ── Progress stats ───────────────────────────────────────────────────
const completedStepCount = computed(() =>
  execSteps.value.filter(s => s.status === 'done').length
);

const stepProgress = computed(() => {
  const total = execSteps.value.length;
  if (total === 0) return 0;
  return Math.round((completedStepCount.value / total) * 100);
});

// ── Error detection ──────────────────────────────────────────────────
const hasError = computed(() =>
  execSteps.value.some(s => s.status === 'error') ||
  orphanToolCalls.value.some(t => t.status === 'error') ||
  !!props.message.error
);

// ── Status pill ──────────────────────────────────────────────────────
const statusLabel = computed(() => {
  if (isRunning.value) return '执行中';
  if (hasError.value) return '部分失败';
  return '已完成';
});

const statusPillClass = computed(() => {
  if (isRunning.value) return 'text-primary border-primary/30 bg-primary/8';
  if (hasError.value) return 'text-destructive border-destructive/30 bg-destructive/8';
  return 'text-emerald-600 dark:text-emerald-400 border-emerald-500/30 bg-emerald-500/8';
});

</script>

<style scoped>
.solo-task-card {
  font-size: 13px;
}

:deep(.custom-scrollbar)::-webkit-scrollbar {
  height: 4px;
  width: 4px;
}
:deep(.custom-scrollbar)::-webkit-scrollbar-track {
  background: transparent;
}
:deep(.custom-scrollbar)::-webkit-scrollbar-thumb {
  background: hsl(var(--border));
  border-radius: 2px;
}
</style>
