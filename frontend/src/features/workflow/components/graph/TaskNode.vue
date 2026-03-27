<template>
  <!--
    概览卡片：任务名称 + 状态 + 工具调用次数 + 输出字符数
    完整执行详情通过点击进入 TaskPanel 的 Detail 视图查看
    w-[260px] 固定宽度确保 DAG 布局一致性
  -->
  <div
    class="task-node group relative rounded-xl border bg-card shadow-sm w-[260px]
           cursor-pointer select-none
           transition-all duration-200 hover:shadow-md hover:-translate-y-px"
    :class="cardBorderClass"
  >
    <!-- running 状态顶部进度条 -->
    <div v-if="data.status === 'running'"
         class="absolute top-0 left-0 right-0 h-0.5 rounded-t-xl overflow-hidden bg-blue-500/10">
      <div class="h-full bg-blue-500 animate-pulse" style="width: 60%"></div>
    </div>

    <!-- VueFlow 连接锚点 — target(入) -->
    <Handle type="target" position="top"
            class="!w-2.5 !h-2.5 !border-2 !border-background !bg-muted-foreground/30
                   transition-colors group-hover:!bg-primary/50" />

    <!-- ── 卡片 Header: 状态图标 + 任务名 + 耗时 ── -->
    <!-- px-4(16px) pt-3(12px) pb-2(8px) gap-3(12px) ← spacing.scale -->
    <div class="px-4 pt-3 pb-2 flex items-start gap-3">
      <!-- 状态图标圆圈 — w-6 h-6(24px) rounded-full ← spacing + borderRadius tokens -->
      <div class="flex-none mt-0.5 w-6 h-6 rounded-full flex items-center justify-center"
           :class="iconBgClass">
        <component :is="statusIcon"
                   :class="['w-3 h-3 flex items-center', iconColorClass]"
                   :spin="data.status === 'running'" />
      </div>

      <!-- 任务名 + 状态文字 -->
      <div class="flex-1 min-w-0">
        <!-- text-sm(14px) font-semibold(600) leading-tight(1.4) ← typography tokens -->
        <p class="text-sm font-semibold text-foreground truncate leading-tight">
          {{ data.label }}
        </p>
        <!-- text-xs(12px) font-medium(500) ← typography tokens -->
        <p class="text-xs font-medium mt-0.5 leading-tight" :class="statusTextClass">
          {{ statusText }}
        </p>
      </div>

      <!-- 耗时角标 — text-xs(12px) ← typography.fontSizes.xs -->
      <span v-if="elapsedTime"
            class="flex-none text-xs font-mono text-muted-foreground/70 mt-0.5 tabular-nums">
        {{ elapsedTime }}
      </span>
    </div>

    <!-- 分隔线 — border-border/40 ← color token -->
    <div class="mx-4 h-px bg-border/40"></div>

    <!-- ── 指标行: 工具调用次数 + 输出字符数 ── -->
    <!-- px-4(16px) py-2(8px) gap-3(12px) ← spacing.scale -->
    <div class="px-4 py-2 flex items-center gap-3">
      <!-- 工具调用次数 — text-xs(12px) text-muted-foreground ← typography + color tokens -->
      <div class="flex items-center gap-1.5 text-xs text-muted-foreground">
        <ToolOutlined class="text-[11px]" />
        <span>{{ data.toolCalls?.length || 0 }} 次调用</span>
      </div>

      <!-- 输出字符数 -->
      <div class="flex items-center gap-1.5 text-xs text-muted-foreground">
        <FileTextOutlined class="text-[11px]" />
        <span>{{ outputSummary }}</span>
      </div>

      <!-- hover 时显示"查看详情"提示 -->
      <div class="ml-auto flex items-center gap-0.5 text-primary
                  opacity-0 group-hover:opacity-100 transition-opacity duration-150">
        <span class="text-xs font-medium">详情</span>
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/>
        </svg>
      </div>
    </div>

    <!-- VueFlow 连接锚点 — source(出) -->
    <Handle type="source" position="bottom"
            class="!w-2.5 !h-2.5 !border-2 !border-background !bg-muted-foreground/30
                   transition-colors group-hover:!bg-primary/50" />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Handle } from '@vue-flow/core';
import {
  CheckCircleOutlined,
  SyncOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  ToolOutlined,
  FileTextOutlined,
} from '@ant-design/icons-vue';

const props = defineProps(['data']);

// ── 状态样式映射 ──
const cardBorderClass = computed(() => {
  switch (props.data.status) {
    case 'completed': return 'border-green-500/40 ring-1 ring-green-500/10';
    case 'running':   return 'border-blue-500/50 ring-1 ring-blue-500/20';
    case 'failed':    return 'border-red-500/50 ring-1 ring-red-500/20';
    default:          return 'border-border/60 border-dashed';
  }
});

const iconBgClass = computed(() => {
  switch (props.data.status) {
    case 'completed': return 'bg-green-500/10';
    case 'running':   return 'bg-blue-500/10';
    case 'failed':    return 'bg-red-500/10';
    default:          return 'bg-muted';
  }
});

const iconColorClass = computed(() => {
  switch (props.data.status) {
    case 'completed': return 'text-green-500';
    case 'running':   return 'text-blue-500';
    case 'failed':    return 'text-red-500';
    default:          return 'text-muted-foreground';
  }
});

const statusTextClass = computed(() => {
  switch (props.data.status) {
    case 'completed': return 'text-green-600 dark:text-green-500';
    case 'running':   return 'text-blue-600 dark:text-blue-500';
    case 'failed':    return 'text-red-600 dark:text-red-500';
    default:          return 'text-muted-foreground';
  }
});

const statusText = computed(() => {
  switch (props.data.status) {
    case 'completed': return '已完成';
    case 'running':   return '执行中...';
    case 'failed':    return '执行失败';
    default:          return '等待中';
  }
});

const statusIcon = computed(() => {
  switch (props.data.status) {
    case 'completed': return CheckCircleOutlined;
    case 'running':   return SyncOutlined;
    case 'failed':    return CloseCircleOutlined;
    default:          return ClockCircleOutlined;
  }
});

// ── 耗时 ──
const elapsedTime = computed(() => {
  if (!props.data.startTime) return '';
  const ms = (props.data.endTime || Date.now()) - props.data.startTime;
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m${Math.floor((ms % 60000) / 1000)}s`;
});

// ── 输出摘要: 优先显示 output 字符数，降级到日志条数 ──
const outputSummary = computed(() => {
  const len = (props.data.output || '').length;
  if (len > 0) {
    if (len < 1000) return `${len} 字符`;
    return `${(len / 1000).toFixed(1)}K 字符`;
  }
  const logCount = props.data.logs?.length || 0;
  if (logCount > 0) return `${logCount} 条日志`;
  return '暂无输出';
});
</script>

<style scoped>
.task-node { transform: translateZ(0); }
</style>
