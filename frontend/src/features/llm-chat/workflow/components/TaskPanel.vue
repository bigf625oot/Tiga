<template>
  <div class="h-full flex flex-col bg-background relative font-sans">

    <!-- ══════════════════════════════════════════
         Header ①: DAG 概览 — 受 showEmbeddedHeader 控制
         仅在 DAG 视图（未选中任务）时显示
         ══════════════════════════════════════════ -->
    <div v-if="showEmbeddedHeader && !selectedTask && (store.isRunning || store.tasks.length > 0)"
         class="flex-none border-b border-border bg-background/95 backdrop-blur-sm">
      <div class="px-3 pt-2 space-y-2 pb-2">
        <!-- 标题 + 状态 badge — gap-3(12px) ← spacing.scale -->
        <div class="flex items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-foreground truncate flex-1 leading-tight">
            {{ goalTitle || (store.isRunning ? '任务执行中...' : '等待任务分配') }}
          </h3>
          <span v-if="store.isRunning"
            class="shrink-0 inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full
                   bg-primary/10 text-primary border border-primary/20 font-medium animate-pulse">
            <span class="w-1.5 h-1.5 rounded-full bg-primary inline-block"></span>Running
          </span>
          <span v-else-if="store.tasks.length > 0 && store.tasks.every(t => t.status === 'completed')"
            class="shrink-0 inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full
                   bg-green-500/10 text-green-600 border border-green-500/20 font-medium">
            <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
            </svg>Success
          </span>
          <span v-else-if="store.tasks.some(t => t.status === 'failed')"
            class="shrink-0 inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full
                   bg-red-500/10 text-red-600 border border-red-500/20 font-medium">
            <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>Failed
          </span>
          <span v-else
            class="shrink-0 text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground
                   border border-border font-medium">Idle</span>
        </div>
        <!-- 进度条 — h-1.5 gap-2(8px) ← spacing.scale -->
        <div v-if="store.tasks.length > 0" class="flex items-center gap-2">
          <div class="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
            <div class="h-full rounded-full transition-[width] duration-700 ease-out"
                 :class="store.progress === 100 ? 'bg-green-500' : 'bg-primary'"
                 :style="{ width: store.progress + '%' }" />
          </div>
          <span class="text-xs font-mono font-semibold text-primary min-w-[2.5rem] text-right tabular-nums">
            {{ store.completedTasks }}/{{ store.totalTasks }}
          </span>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════
         Header ②: 详情导航栏 — 不受 showEmbeddedHeader 控制
         只要进入详情视图就始终渲染，确保 ← 返回按钮可见
         ══════════════════════════════════════════ -->
    <div v-if="selectedTask"
         class="flex-none border-b border-border bg-background/95 backdrop-blur-sm">
      <!-- px-3(12px) py-2(8px) gap-2(8px) ← spacing.scale -->
      <div class="px-3 py-2 flex items-center gap-2">
        <!-- 返回按钮 — w-7 h-7(28px) rounded-md ← spacing + borderRadius.md -->
        <button
          @click="goBack"
          class="flex-none w-7 h-7 rounded-md flex items-center justify-center
                 text-muted-foreground hover:text-foreground hover:bg-muted
                 transition-colors"
          title="返回 DAG 视图"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
        </button>

        <!-- 任务信息 -->
        <div class="flex-1 min-w-0">
          <!-- text-sm(14px) font-semibold(600) ← typography tokens -->
          <h3 class="text-sm font-semibold text-foreground truncate leading-tight">
            {{ selectedTask.name }}
          </h3>
          <!-- text-xs(12px) text-muted-foreground ← typography + color tokens -->
          <p v-if="selectedTask.startTime" class="text-xs text-muted-foreground mt-0.5 tabular-nums">
            {{ formatTime(selectedTask.startTime) }}
            <template v-if="selectedTask.endTime">
              · 耗时 {{ formatElapsed(selectedTask.startTime, selectedTask.endTime) }}
            </template>
            <template v-else-if="selectedTask.status === 'running'">
              · 执行中 {{ formatElapsed(selectedTask.startTime, null) }}
            </template>
          </p>
        </div>

        <!-- 任务状态 badge -->
        <span class="shrink-0 inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium"
              :class="taskBadgeClass(selectedTask.status)">
          <component :is="taskBadgeIcon(selectedTask.status)"
                     :class="['text-[10px]']"
                     :spin="selectedTask.status === 'running'" />
          {{ taskBadgeLabel(selectedTask.status) }}
        </span>
      </div>
    </div>

    <!-- ════════════════════════════════════════════
         Main Content — 两种视图互斥切换
         ════════════════════════════════════════════ -->
    <div class="flex-1 overflow-hidden flex flex-col min-h-0">

      <!-- 空状态 -->
      <div v-if="!store.isRunning && store.tasks.length === 0"
           class="flex-1 flex flex-col items-center justify-center bg-muted/5 text-muted-foreground gap-4">
        <div class="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-muted/40 to-muted/10
                    flex items-center justify-center border border-border/50
                    shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]">
          <Network class="w-8 h-8 text-muted-foreground/40 drop-shadow-sm stroke-[1.5]" />
          <div class="absolute -top-1 -right-1 w-3 h-3 bg-primary/20 rounded-full blur-[2px]"></div>
          <div class="absolute -bottom-2 -left-2 w-4 h-4 bg-muted-foreground/10 rounded-full blur-[3px]"></div>
        </div>
        <div class="text-center">
          <!-- text-sm(14px) font-medium(500) / text-xs(12px) ← typography tokens -->
          <p class="text-sm font-medium text-foreground mb-1">等待任务分配</p>
          <p class="text-xs text-muted-foreground max-w-[200px] leading-relaxed">
            系统正在分析您的需求，即将在此生成工作流图谱并开始执行任务。
          </p>
        </div>
      </div>

      <template v-else>
        <!-- ① DAG 视图: 任务未选中时全屏显示 -->
        <div v-if="!selectedTask" class="flex-1 min-h-0 overflow-hidden bg-muted/5">
          <TaskGraph />
        </div>

        <!-- ② 详情视图: 点击节点后进入 -->
        <div v-else class="flex-1 overflow-y-auto custom-scrollbar">
          <!-- p-4(16px) space-y-4(16px) ← spacing.scale -->
          <div class="p-4 space-y-4">

            <!-- 任务描述 (若有) -->
            <p v-if="selectedTask.description"
               class="text-sm text-muted-foreground leading-relaxed">
              {{ selectedTask.description }}
            </p>

            <!-- ─── 任务输出 ─── -->
            <!-- 有 output 时渲染 markdown；无 output 有 logs 时显示日志 -->
            <section v-if="selectedTask.output">
              <!-- section label: text-xs(12px) font-medium(500) — 无 uppercase/tracking，CJK 适配 -->
              <h4 class="text-xs font-medium text-muted-foreground mb-2 flex items-center justify-between leading-tight">
                <div class="flex items-center gap-1.5">
                  <svg class="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                  </svg>
                  任务输出
                </div>
                <button 
                  v-if="hasCodeArtifact(selectedTask.output)"
                  @click="openTaskArtifact(selectedTask.output)"
                  class="flex items-center gap-1 text-[10px] text-primary hover:text-primary/80 transition-colors px-1.5 py-0.5 rounded bg-primary/10"
                >
                  <Code2 class="w-3 h-3" />
                  预览代码产物
                </button>
              </h4>
              <!-- rounded-lg bg-muted/30 border p-4(16px) ← radius + color + spacing tokens -->
              <div ref="outputRef"
                   class="rounded-lg bg-muted/30 border border-border/50 p-4 task-output-prose"
                   v-html="renderMarkdown(selectedTask.output)">
              </div>
              <!-- running 时显示流式光标 -->
              <span v-if="selectedTask.status === 'running'"
                    class="inline-block w-1.5 h-3.5 bg-primary/60 animate-pulse ml-0.5 mt-1 align-text-bottom rounded-sm">
              </span>
            </section>

            <!-- 日志 (无 output 时的降级展示) -->
            <section v-else-if="parsedLogs.length > 0">
              <h4 class="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1.5 leading-tight">
                <svg class="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M4 6h16M4 10h16M4 14h16M4 18h16"/>
                </svg>
                执行日志
              </h4>
              <!-- rounded-md bg-muted/20 border p-3(12px) ← radius + color + spacing tokens -->
            <div class="rounded-md bg-muted/20 border border-solid  border-border/50 p-3 max-h-[60vh] overflow-y-auto custom-scrollbar">
                <div class="text-xs font-mono text-muted-foreground leading-relaxed whitespace-pre-wrap break-words">
                  <template v-for="log in parsedLogs" :key="log.id">
                    <span :class="{
                       'text-red-500': log.type === 'error',
                       'text-green-600 dark:text-green-500': log.type === 'success',
                       'text-yellow-600 dark:text-yellow-400': log.type === 'warning',
                     }">{{ log.text }}</span>
                  </template>
                </div>
              </div>
            </section>

            <!-- 暂无内容 (running 时) -->
            <div v-else-if="selectedTask.status === 'running'"
                 class="flex items-center gap-2 text-xs text-muted-foreground py-2">
              <span class="relative flex h-2 w-2">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span class="relative inline-flex h-2 w-2 rounded-full bg-primary"></span>
              </span>
              <span>任务执行中，正在等待输出...</span>
            </div>

            <!-- ─── 工具调用列表 ─── -->
            <section v-if="selectedTask.toolCalls?.length > 0">
              <!-- gap-2(8px) mb-2(8px) ← spacing.scale -->
              <h4 class="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1.5 leading-tight">
                <svg class="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
                工具调用
                <!-- count badge — text-xs font-medium ← typography tokens -->
                <span class="inline-flex items-center justify-center h-4 min-w-[16px] px-1
                             rounded-sm bg-muted text-muted-foreground text-xs font-medium tabular-nums">
                  {{ selectedTask.toolCalls.length }}
                </span>
              </h4>

              <!-- space-y-2(8px) ← spacing.scale -->
              <div class="space-y-2">
                <div v-for="(tool, idx) in selectedTask.toolCalls" :key="idx"
                     class="rounded-lg border border-border bg-background overflow-hidden">

                  <!-- 工具 Header: 名称 + 状态 -->
                  <!-- px-3(12px) py-2(8px) ← spacing.scale -->
                  <div class="flex items-center gap-2 px-3 py-2 bg-muted/20">
                    <component :is="toolStatusIcon(tool.status)"
                               :class="['text-sm shrink-0', toolStatusColor(tool.status)]"
                               :spin="tool.status === 'running'" />
                    <!-- text-sm(14px) font-mono font-medium(500) ← typography tokens -->
                    <span class="text-sm font-mono font-medium text-foreground flex-1 truncate">
                      {{ tool.tool_name }}
                    </span>
                    <!-- 状态 pill -->
                    <span class="shrink-0 text-xs px-1.5 py-0.5 rounded-sm font-medium"
                          :class="toolStatusPill(tool.status)">
                      {{ tool.status }}
                    </span>
                  </div>

                  <!-- 工具参数 -->
                  <div v-if="tool.tool_args && Object.keys(tool.tool_args).length > 0"
                       class="px-3 py-2 border-t border-border/50">
                    <!-- 搜索查询单独高亮 -->
                    <div v-if="getSearchQuery(tool)"
                         class="text-xs font-mono bg-muted/40 rounded-md px-2 py-1.5 text-foreground/80 truncate">
                      <span class="text-muted-foreground mr-1">›</span>{{ getSearchQuery(tool) }}
                    </div>
                    <!-- 其余参数 JSON 展示 -->
                    <pre v-else
                         class="text-xs font-mono text-muted-foreground bg-muted/30 rounded-md px-2 py-1.5 overflow-x-auto leading-relaxed whitespace-pre-wrap break-all">{{ formatArgs(tool.tool_args) }}</pre>
                  </div>

                  <!-- 工具结果 -->
                  <div v-if="tool.result" class="px-3 py-2 border-t border-border/50">
                    <!-- 搜索结果: 渲染为链接列表 -->
                    <template v-if="getSearchResults(tool).length > 0">
                      <p class="text-xs text-muted-foreground mb-1.5 flex items-center gap-1">
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
                        </svg>
                        {{ getSearchResults(tool).length }} 个来源
                      </p>
                      <div class="space-y-1">
                        <a v-for="(res, ri) in getSearchResults(tool)" :key="ri"
                           :href="res.url || res.link" target="_blank"
                           class="flex flex-col gap-0.5 px-2 py-1.5 rounded-md border border-transparent
                                  hover:border-border/60 hover:bg-muted/40 transition-colors no-underline">
                          <span class="text-xs font-medium text-primary truncate leading-tight">
                            {{ res.title || res.name || res.url || 'Untitled' }}
                          </span>
                          <span v-if="res.content || res.snippet"
                                class="text-xs text-muted-foreground line-clamp-1 leading-tight">
                            {{ res.content || res.snippet }}
                          </span>
                        </a>
                      </div>
                    </template>
                    <!-- 普通文本结果 -->
                    <p v-else
                       class="text-xs text-muted-foreground leading-relaxed line-clamp-4 font-mono break-all">
                      {{ tool.result }}
                    </p>
                  </div>

                </div>
              </div>
            </section>

          </div>
        </div>
      </template>
    </div>

    <!-- ════════════════════════════════════════════
         Control bar (running 时常驻底部)
         px-4(16px) py-2(8px) ← spacing.scale
         ════════════════════════════════════════════ -->
    <div v-if="store.isRunning"
         class="flex-none px-4 py-2 bg-muted/30 border-t border-border
                flex items-center justify-between">
      <div class="flex items-center gap-2 text-xs text-muted-foreground min-w-0">
        <span class="relative flex h-2 w-2 shrink-0">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
          <span class="relative inline-flex h-2 w-2 rounded-full bg-primary"></span>
        </span>
        <span class="font-mono truncate">{{ currentRunningTask?.name || '执行中...' }}</span>
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <button @click="openLogDrawer"
          class="flex items-center gap-1 px-2 py-1 rounded text-xs
                 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
          <FileTextOutlined :style="{ fontSize: '11px' }" />
          <span>日志</span>
        </button>
        <button @click="store.stopWorkflow"
          class="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium
                 text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors">
          <StopOutlined :style="{ fontSize: '11px' }" />
          <span>停止</span>
        </button>
      </div>
    </div>

    <!-- Log Drawer -->
    <LogDrawer :visible="isLogDrawerOpen" :logs="store.logs"
               @close="isLogDrawerOpen = false" @clear="store.clearLogs" />
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import { useWorkflowStore } from '@/features/llm-chat/store/workflow/workflow.store';
import LogDrawer from '@/features/llm-chat/workflow/components/drawer/LogDrawer.vue';
import TaskGraph from './graph/TaskGraph.vue';
import { Network, Code2 } from 'lucide-vue-next';
import {
  CheckCircleOutlined,
  SyncOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  StopOutlined,
  FileTextOutlined,
} from '@ant-design/icons-vue';
import { marked } from 'marked';
import mermaid from 'mermaid';
import { useArtifact } from '@/features/llm-chat/shared/context/ArtifactContext';

// ── Mermaid 初始化 (模块级，仅执行一次) ──
// theme: neutral 在亮/暗两种模式下均可接受；fontFamily:inherit 跟随系统字体
mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  fontFamily: 'inherit',
  fontSize: 13,
  securityLevel: 'loose',
  gantt: { barHeight: 20, barGap: 4, topPadding: 40, fontSize: 12 },
});

defineProps({
  embedded:           { type: Boolean, default: false },
  showEmbeddedHeader: { type: Boolean, default: true },
  sessionId:          { type: String,  default: '' },
  agentName:          { type: String,  default: '' },
  isWorkflowMode:     { type: Boolean, default: true },
  attachmentsCount:   { type: Number,  default: 0 }
});

const store = useWorkflowStore();
const isLogDrawerOpen = ref(false);
const artifactContext = useArtifact();

// ── Master → Detail 导航 ──
// selectedTask 为 null → DAG 视图；有值 → 详情视图
// 直接读 store.tasks 确保详情内容（output/toolCalls）实时响应 SSE 更新
const selectedTask = computed(() =>
  store.selectedTaskId
    ? (store.tasks.find(t => t.id === store.selectedTaskId) ?? null)
    : null
);

const goBack = () => {
  store.selectedTaskId = null;
};

// ── 日志解析 (计算属性，避免模板内每次渲染都执行正则) ──
const parsedLogs = computed(() => {
  if (!selectedTask.value?.logs) return [];
  return selectedTask.value.logs.map((line, index) => {
    let rawObj = line;
    let strLine = String(line);
    
    // 尝试解析可能的 JSON 字符串
    if (typeof line === 'string' && line.trim().startsWith('{')) {
      try {
        rawObj = JSON.parse(line);
        // 如果有 content 字段，提取出来作为日志文本
        if (rawObj && typeof rawObj === 'object' && 'content' in rawObj) {
          strLine = typeof rawObj.content === 'string' ? rawObj.content : JSON.stringify(rawObj.content);
        }
      } catch (e) {
        // ignore
      }
    } else if (typeof line === 'object' && line !== null && 'content' in line) {
      strLine = typeof line.content === 'string' ? line.content : JSON.stringify(line.content);
    }

    let type = 'default';
    if (/error|exception|traceback|failed/i.test(strLine)) type = 'error';
    else if (/success|done|completed|✓|✅/i.test(strLine)) type = 'success';
    else if (/warning|warn/i.test(strLine)) type = 'warning';
    
    return {
      id: index,
      text: typeof rawObj === 'object' && !('content' in rawObj) ? JSON.stringify(rawObj, null, 2) : strLine,
      type
    };
  });
});

// ── Mermaid 渲染 ──
// outputRef 指向 task-output-prose 容器；任务 completed 后扫描 .mermaid 节点并渲染
const outputRef = ref(null);
let _mermaidSeq = 0;

const renderMermaidDiagrams = async () => {
  await nextTick(); // 等 v-html 完成 DOM 写入
  const container = outputRef.value;
  if (!container) return;
  const nodes = Array.from(
    container.querySelectorAll('.mermaid:not([data-rendered])')
  );
  if (!nodes.length) return;
  for (const node of nodes) {
    try {
      const id = `mmd-${++_mermaidSeq}`;
      const { svg } = await mermaid.render(id, node.textContent.trim());
      node.innerHTML = svg;
    } catch (err) {
      // 图表语法有误时降级为错误提示，不崩溃组件
      node.innerHTML = `<pre class="mermaid-err">${err.message}</pre>`;
    }
    node.setAttribute('data-rendered', 'true');
  }
};

// 仅在任务完成（非流式进行中）时渲染，避免解析不完整的 mermaid 语法
watch(
  () => selectedTask.value?.status,
  (status) => { if (status === 'completed') renderMermaidDiagrams(); }
);
// 切换到已完成任务时立即触发
watch(
  selectedTask,
  (task) => { if (task?.status === 'completed') renderMermaidDiagrams(); },
  { immediate: true }
);

// ── Header 数据 ──
const goalTitle = computed(() => {
  const planLog = store.logs.find(l => l.step === 'plan' && l.message?.includes('规划'));
  if (planLog) return planLog.message.replace(/规划.*?：/, '').slice(0, 60);
  if (store.tasks.length > 0) return `执行计划：${store.tasks.length} 个步骤`;
  return '';
});

const currentRunningTask = computed(() => store.tasks.find(t => t.status === 'running'));

// ── 详情视图: 任务状态 badge helpers ──
const taskBadgeClass = (status) => {
  switch (status) {
    case 'completed': return 'bg-green-500/10 text-green-600 dark:text-green-500 border border-green-500/20';
    case 'running':   return 'bg-blue-500/10 text-blue-600 dark:text-blue-500 border border-blue-500/20';
    case 'failed':    return 'bg-red-500/10 text-red-600 dark:text-red-500 border border-red-500/20';
    default:          return 'bg-muted text-muted-foreground border border-border';
  }
};
const taskBadgeIcon = (status) => {
  switch (status) {
    case 'completed': return CheckCircleOutlined;
    case 'running':   return SyncOutlined;
    case 'failed':    return CloseCircleOutlined;
    default:          return ClockCircleOutlined;
  }
};
const taskBadgeLabel = (status) => {
  switch (status) {
    case 'completed': return '已完成';
    case 'running':   return '执行中';
    case 'failed':    return '失败';
    default:          return '等待中';
  }
};

// ── 工具调用状态 helpers ──
const toolStatusIcon = (status) => {
  switch (status) {
    case 'completed': return CheckCircleOutlined;
    case 'failed':    return CloseCircleOutlined;
    case 'running':   return SyncOutlined;
    default:          return ClockCircleOutlined;
  }
};
const toolStatusColor = (status) => {
  switch (status) {
    case 'completed': return 'text-green-500';
    case 'failed':    return 'text-red-500';
    case 'running':   return 'text-blue-500';
    default:          return 'text-muted-foreground';
  }
};
const toolStatusPill = (status) => {
  switch (status) {
    case 'completed': return 'bg-green-500/10 text-green-600 dark:text-green-500';
    case 'failed':    return 'bg-red-500/10 text-red-500';
    case 'running':   return 'bg-blue-500/10 text-blue-500';
    default:          return 'bg-muted text-muted-foreground';
  }
};

// ── 工具参数/结果解析 ──
const getSearchQuery = (tool) =>
  tool.tool_args?.query || tool.tool_args?.search || tool.tool_args?.q || null;

const getSearchResults = (tool) => {
  if (!tool.result) return [];
  try {
    const parsed = JSON.parse(tool.result);
    if (Array.isArray(parsed)) return parsed.slice(0, 5);
    if (Array.isArray(parsed.results)) return parsed.results.slice(0, 5);
    if (Array.isArray(parsed.items))   return parsed.items.slice(0, 5);
    return [];
  } catch { return []; }
};

const formatArgs = (args) => {
  try {
    return JSON.stringify(args, null, 2);
  } catch { return String(args); }
};

// ── 时间格式化 ──
const formatTime = (ts) => new Date(ts).toTimeString().slice(0, 8);

const formatElapsed = (startTime, endTime) => {
  const ms = ((endTime ?? Date.now()) - startTime);
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m${Math.floor((ms % 60000) / 1000)}s`;
};

// ── Markdown 渲染 ──
// 处理链路:
//   1. 预处理: LLM 常用 em-dash(—/–) 作为表格分隔行，marked 只识别 ASCII `-`，
//              逐行扫描纯分隔行并归一化，避免 table 被降级为 <p>
//   2. marked.parse(): gfm:true 默认，输出 HTML
//   3. 后处理①: <table> 包裹为 .md-table-wrap 实现横向滚动
//   4. 后处理②: mermaid/gantt/flowchart fenced code block → .mermaid div
//              (mermaid.render 在 watch 触发 DOM 更新后异步执行)
const MERMAID_LANGS = new Set([
  'mermaid','gantt','flowchart','sequencediagram','classdiagram',
  'statediagram','erdiagram','journey','pie','gitgraph',
  'mindmap','timeline','xychart-beta','block-beta',
]);

const renderMarkdown = (text) => {
  if (!text) return '';

  let processed = text.trim();

  // 去除 LLM 可能包裹在最外层的 ```markdown ... ``` (会导致全部内容变为代码块)
  const mdMatch = processed.match(/^```(?:markdown|md)\s*\n([\s\S]*?)\n```$/i);
  if (mdMatch) {
    processed = mdMatch[1];
  }

  // 处理 <think> 标签 (DeepSeek等模型)，前后补充空行确保 marked 能正确解析内部的 Markdown (如表格、标题)
  processed = processed
    .replace(/<think>/g, '<details class="think-block" open><summary>思考过程</summary>\n\n')
    .replace(/<\/think>/g, '\n\n</details>\n\n');

  // Step 1 — 表格分隔行 em-dash 归一化
  // 匹配仅由 | 空格 : - 及各类 Unicode 破折号构成的行（即分隔行）
  const normalized = processed.replace(/^[ \t]*\|?[ \t\-—–‐―‑:|]+\|[ \t\-—–‐―‑:|]*$/gm, (line) =>
    line.replace(/[—–‐―‑]/g, '-')
  );

  // Step 2 — marked 解析
  const html = marked.parse(normalized);

  // Step 3 & 4 — 后处理
  return html
    .replace(/<table([^>]*)>/g, '<div class="md-table-wrap"><table$1>')
    .replace(/<\/table>/g, '</table></div>')
    .replace(
      // 匹配 marked 输出的 fenced code block HTML
      /<pre><code class="language-([^"]+)">([\s\S]*?)<\/code><\/pre>/g,
      (_match, lang, encoded) => {
        if (!MERMAID_LANGS.has(lang.toLowerCase())) return _match;
        // marked 对 code 内容做了 HTML 实体编码，还原后传给 mermaid
        const code = encoded
          .replace(/&amp;/g, '&')
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&#39;/g, "'")
          .replace(/&#x27;/g, "'")
          .replace(/&quot;/g, '"');
          
        const lowerLang = lang.toLowerCase();
        let mermaidCode = code.trim();
        
        // 修复甘特图等语法错误：如果 LLM 没有输出图表类型声明，自动补充
        if (lowerLang !== 'mermaid' && !mermaidCode.toLowerCase().startsWith(lowerLang)) {
            mermaidCode = lowerLang + '\n' + mermaidCode;
        }

        return `<div class="mermaid-wrap"><div class="mermaid">${mermaidCode}</div></div>`;
      }
    );
};

// ── Code Artifact Support ──
const hasCodeArtifact = (text) => {
  if (!text) return false;
  // 检查是否包含支持的语言代码块且行数大于 5
  const match = text.match(/```(vue|html|javascript|typescript|python|json|sql)?\n([\s\S]*?)```/i);
  if (!match) return false;
  return match[2].trim().split('\n').length >= 5;
};

const openTaskArtifact = (text) => {
  if (!text) return;
  const match = text.match(/```(vue|html|javascript|typescript|python|json|sql)?\n([\s\S]*?)```/i);
  if (match) {
    const lang = (match[1] || 'text').toLowerCase();
    artifactContext.openArtifact({
      type: lang, 
      content: match[2].trim(),
      language: lang,
      title: `任务产物 (${lang})`
    });
  }
};

const openLogDrawer = () => { isLogDrawerOpen.value = true; };
defineExpose({ openLogDrawer });

onMounted(() => {});
onBeforeUnmount(() => {});
</script>

<style scoped>
/* 细滚动条 — 跟随主题色 */
.custom-scrollbar::-webkit-scrollbar       { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: hsl(var(--border)); border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }

/*
 * Markdown prose — @tailwindcss/typography 未安装，使用 :deep() 补齐排版。
 * v-html 注入的节点不携带 scoped data 属性，必须走 :deep() 才能命中。
 * font-size 统一 13px；spacing 对齐 design_tokens.json scale: 4/8/12/16px。
 */
.task-output-prose {
  font-family: inherit;
  font-size: 13px;
  line-height: 1.6;
  color: hsl(var(--foreground) / 0.9);
  word-break: break-word;
}
.task-output-prose :deep(.think-block) {
  margin-bottom: 12px;
  padding: 10px 14px;
  background: hsl(var(--muted) / 0.4);
  border-radius: calc(var(--radius) - 2px);
  border-left: 3px solid hsl(var(--muted-foreground) / 0.3);
}
.task-output-prose :deep(.think-block summary) {
  font-size: 12px;
  font-weight: 500;
  color: hsl(var(--muted-foreground));
  cursor: pointer;
  user-select: none;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.task-output-prose :deep(.think-block summary::before) {
  content: '💡';
  font-size: 14px;
}
.task-output-prose :deep(h1),
.task-output-prose :deep(h2),
.task-output-prose :deep(h3),
.task-output-prose :deep(h4),
.task-output-prose :deep(h5),
.task-output-prose :deep(h6) {
  font-weight: 600; line-height: 1.4;
  color: hsl(var(--foreground));
  margin-top: 12px; margin-bottom: 4px;
}
.task-output-prose :deep(h1) { font-size: 16px; }
.task-output-prose :deep(h2) { font-size: 14px; }
.task-output-prose :deep(h3) { font-size: 13px; font-weight: 500; }
.task-output-prose :deep(h4),
.task-output-prose :deep(h5),
.task-output-prose :deep(h6) { font-size: 12px; font-weight: 500; }
.task-output-prose :deep(:first-child) { margin-top: 0 !important; }
.task-output-prose :deep(:last-child)  { margin-bottom: 0 !important; }
.task-output-prose :deep(p)  { font-size: 13px; line-height: 1.6; margin-bottom: 8px; }
.task-output-prose :deep(ul),
.task-output-prose :deep(ol) { padding-left: 16px; margin-bottom: 8px; font-size: 13px; line-height: 1.6; }
.task-output-prose :deep(ul)     { list-style-type: disc; }
.task-output-prose :deep(ol)     { list-style-type: decimal; }
.task-output-prose :deep(li)     { margin-bottom: 2px; }
.task-output-prose :deep(li > p) { margin-bottom: 0; }
/* ── code / pre: ui-monospace = SF Mono(macOS) / Cascadia(Win11) / system mono ── */
.task-output-prose :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", "PingFang SC", "Microsoft YaHei", monospace;
  font-size: 12px; font-style: normal;
  background: hsl(var(--muted)); color: hsl(var(--foreground));
  padding: 1px 4px; border-radius: calc(var(--radius) - 4px);
}
.task-output-prose :deep(pre) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", "PingFang SC", "Microsoft YaHei", monospace;
  font-size: 12px; font-style: normal; line-height: 1.6;
  background: hsl(var(--muted)); color: hsl(var(--foreground));
  padding: 12px; border-radius: calc(var(--radius) - 2px);
  overflow-x: auto; margin-bottom: 8px;
  white-space: pre-wrap; word-break: break-all;
}
.task-output-prose :deep(pre code) { background: transparent; padding: 0; font-size: inherit; border-radius: 0; }
.task-output-prose :deep(blockquote) {
  border-left: 2px solid hsl(var(--border));
  padding-left: 12px; color: hsl(var(--muted-foreground));
  font-size: 13px; font-style: normal; margin-bottom: 8px;
}
.task-output-prose :deep(a) { color: hsl(var(--primary)); text-decoration: underline; text-underline-offset: 2px; }
.task-output-prose :deep(a:hover) { opacity: 0.8; }
.task-output-prose :deep(strong) { font-weight: 600; color: hsl(var(--foreground)); }
.task-output-prose :deep(em)     { font-style: italic; }
.task-output-prose :deep(hr)     { border: none; border-top: 1px solid hsl(var(--border)); margin: 12px 0; }

/* ── 表格: wrapper 实现横向滚动 + 圆角边框；thead 背景区分层次 ── */
.task-output-prose :deep(.md-table-wrap) {
  overflow-x: auto;
  border-radius: calc(var(--radius) - 2px);
  border: 1px solid hsl(var(--border));
  margin-bottom: 8px;
}
.task-output-prose :deep(.md-table-wrap:last-child) { margin-bottom: 0; }
.task-output-prose :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  /* 字体继承父容器系统字体，不单独声明 */
}
.task-output-prose :deep(thead) {
  background: hsl(var(--muted) / 0.7);
}
.task-output-prose :deep(th) {
  font-weight: 600;
  text-align: left;
  padding: 6px 12px;
  color: hsl(var(--muted-foreground));
  white-space: nowrap;
  border-bottom: 1px solid hsl(var(--border));
}
.task-output-prose :deep(tbody tr) {
  transition: background 0.1s ease;
}
.task-output-prose :deep(tbody tr:not(:last-child)) {
  border-bottom: 1px solid hsl(var(--border) / 0.4);
}
.task-output-prose :deep(tbody tr:hover) {
  background: hsl(var(--muted) / 0.4);
}
.task-output-prose :deep(td) {
  padding: 6px 12px;
  color: hsl(var(--foreground) / 0.9);
  vertical-align: top;
  line-height: 1.5;
}

/* ── Mermaid 图表容器 ── */
/* .mermaid-wrap 负责外层圆角 + 背景，让图表与 prose 文字风格保持一致 */
.task-output-prose :deep(.mermaid-wrap) {
  margin-bottom: 8px;
  border-radius: calc(var(--radius) - 2px);
  border: 1px solid hsl(var(--border));
  background: hsl(var(--card));
  padding: 12px;
  overflow-x: auto;
  text-align: center;
}
.task-output-prose :deep(.mermaid-wrap:last-child) { margin-bottom: 0; }
/* mermaid render() 输出的 SVG 默认宽度写死，限制最大宽度并居中 */
.task-output-prose :deep(.mermaid svg) {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 0 auto;
}
/* 解析失败时的降级错误提示 */
.task-output-prose :deep(.mermaid-err) {
  font-size: 12px;
  color: hsl(var(--destructive));
  background: hsl(var(--destructive) / 0.05);
  padding: 8px 12px;
  border-radius: calc(var(--radius) - 4px);
  white-space: pre-wrap;
  text-align: left;
}
</style>
