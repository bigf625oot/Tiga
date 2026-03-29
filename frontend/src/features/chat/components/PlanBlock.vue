<script setup lang="ts">
import { computed } from 'vue';
import { CheckCircle2, XCircle } from 'lucide-vue-next';
import type { PlanBlock } from '../types';

const props = defineProps<{
  block: PlanBlock;
}>();

const isRunning = computed(() => props.block.steps.some(s => s.status === 'running'));
const hasError = computed(() => props.block.steps.some((s: any) => s.status === 'error'));
const completedStepCount = computed(() => props.block.steps.filter(s => s.status === 'completed' || (s as any).status === 'done').length);

const statusLabel = computed(() => {
  if (isRunning.value) return '执行中';
  if (hasError.value) return '部分失败';
  if (completedStepCount.value === 0 && props.block.steps.length > 0) return '待执行';
  if (completedStepCount.value < props.block.steps.length) return '执行中';
  return '已完成';
});

const statusPillClass = computed(() => {
  if (isRunning.value) return 'text-primary border-primary/30 bg-primary/8';
  if (hasError.value) return 'text-destructive border-destructive/30 bg-destructive/8';
  if (completedStepCount.value === 0 && props.block.steps.length > 0) return 'text-muted-foreground border-border/50 bg-muted/20';
  if (completedStepCount.value < props.block.steps.length) return 'text-primary border-primary/30 bg-primary/8';
  return 'text-emerald-600 dark:text-emerald-400 border-emerald-500/30 bg-emerald-500/8';
});

const stepProgress = computed(() => {
  const total = props.block.steps.length;
  if (total === 0) return 0;
  return Math.round((completedStepCount.value / total) * 100);
});
</script>

<template>
  <div class="w-full flex flex-col gap-2 min-w-0 my-1">
    <!-- ── Task status header ────────────── -->
    <div class="flex items-center gap-2.5 px-3 py-1.5  mb-1 w-max min-w-[200px] shadow-sm">
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
      <span v-if="block.steps.length > 0" class="text-[12px] text-muted-foreground/60 font-medium">
        {{ completedStepCount }}/{{ block.steps.length }} 步骤
      </span>

      <!-- Progress bar -->
      <div v-if="block.steps.length > 1" class="flex-1 h-1 rounded-full bg-muted overflow-hidden max-w-[100px] ml-auto">
        <div
          class="h-full rounded-full transition-[width] duration-500"
          :class="hasError ? 'bg-destructive/60' : 'bg-primary'"
          :style="{ width: stepProgress + '%' }"
        />
      </div>
    </div>

    <!-- ── Execution step timeline ─────────────── -->
    <div v-if="block.steps.length > 0" class="steps-timeline relative flex flex-col mt-0.5 min-w-0 pl-1.5">
      <div v-for="(step, idx) in block.steps" :key="step.id" class="step-row relative flex gap-2.5 min-w-0">

        <!-- Vertical connector -->
        <div
          v-if="idx < block.steps.length - 1"
          class="absolute left-[7.5px] top-[22px] bottom-[-2px] w-px z-0"
          :class="(step as any).status === 'error' ? 'bg-destructive/25' : 'bg-border/50'"
        ></div>

        <!-- Status indicator -->
        <div class="flex-shrink-0 w-[16px] h-[16px] flex items-center justify-center mt-0.5 z-10 bg-background rounded-full">
          <template v-if="step.status === 'running'">
            <span class="w-[14px] h-[14px] rounded-full border-2 border-primary border-t-transparent animate-spin inline-block"></span>
          </template>
          <CheckCircle2 v-else-if="step.status === 'completed' || (step as any).status === 'done'" class="w-[14px] h-[14px] text-emerald-500" />
          <XCircle v-else-if="(step as any).status === 'error'" class="w-[14px] h-[14px] text-destructive" />
          <div v-else class="w-[12px] h-[12px] rounded-full border-2 border-border bg-background"></div>
        </div>

        <!-- Step body -->
        <div class="flex-1 min-w-0 pb-2">
          <div class="flex items-start gap-2 min-w-0">
            <div class="text-[13px] leading-snug flex-1 break-words"
                 :class="{
                   'text-foreground font-medium': step.status === 'running',
                   'text-muted-foreground': step.status === 'completed' || (step as any).status === 'done',
                   'text-destructive': (step as any).status === 'error',
                   'text-muted-foreground/60': step.status === 'pending',
                 }"
                 :title="step.text">
              {{ step.text }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.solo-task-card {
  font-size: 13px;
}
</style>
