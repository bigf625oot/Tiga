<script setup lang="ts">
import { computed } from 'vue';
import type { PlanBlock } from '@/features/llm-chat/shared/types';
import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-vue-next';

const props = defineProps<{
  block: PlanBlock;
}>();

const steps = computed(() => props.block.steps || []);

const totalSteps = computed(() => steps.value.length);
const completedSteps = computed(() => steps.value.filter(s => s.status === 'completed').length);
const failedSteps = computed(() => steps.value.filter(s => s.status === 'error').length);
const runningSteps = computed(() => steps.value.filter(s => s.status === 'running').length);

const isRunning = computed(() => runningSteps.value > 0);
const hasError = computed(() => failedSteps.value > 0);
const isCompleted = computed(() => totalSteps.value > 0 && completedSteps.value === totalSteps.value);

const statusPillClass = computed(() => {
  if (hasError.value) return 'border-destructive/30 text-destructive bg-destructive/5';
  if (isRunning.value) return 'border-primary/30 text-primary bg-primary/5';
  if (isCompleted.value) return 'border-emerald-500/30 text-emerald-600 bg-emerald-500/5';
  return 'border-muted-foreground/20 text-muted-foreground bg-muted/30';
});

const statusLabel = computed(() => {
  if (hasError.value) return '执行失败';
  if (isRunning.value) return '执行中';
  if (isCompleted.value) return '执行完成';
  return '等待中';
});

const stepProgress = computed(() => {
  if (totalSteps.value === 0) return 0;
  return Math.round((completedSteps.value / totalSteps.value) * 100);
});
</script>

<template>
  <div v-if="steps.length > 0" class="flex flex-col gap-2 my-2 w-full">
    <!-- Header with Badge and Progress -->
    <div class="flex items-center gap-2 mb-1">
      <div class="text-[11px] font-semibold text-muted-foreground uppercase tracking-widest flex items-center gap-1.5 shrink-0">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
        任务计划
      </div>

      <!-- Status pill -->
      <div class="flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-semibold border"
        :class="statusPillClass">
        <span v-if="isRunning" class="relative flex h-1.5 w-1.5">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 bg-current"></span>
          <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-current"></span>
        </span>
        <CheckCircle2 v-else-if="isCompleted" class="w-2.5 h-2.5" />
        <XCircle v-else-if="hasError" class="w-2.5 h-2.5" />
        <Circle v-else class="w-2.5 h-2.5" />
        <span>{{ statusLabel }}</span>
      </div>

      <!-- Progress bar -->
      <div class="flex items-center gap-1.5 flex-1 min-w-0 max-w-[120px] ml-1">
        <div class="flex-1 h-1 rounded-full bg-muted overflow-hidden">
          <div class="h-full rounded-full transition-[width] duration-500"
            :class="hasError ? 'bg-destructive/60' : 'bg-primary/80'" :style="{ width: stepProgress + '%' }" />
        </div>
        <span class="text-[10px] text-muted-foreground/60 font-mono shrink-0 tabular-nums">
          {{ completedSteps }}/{{ totalSteps }}
        </span>
      </div>
    </div>

    <!-- Steps Timeline -->
    <div class="relative pl-1.5 space-y-3 before:absolute before:inset-y-0 before:left-3.5 before:w-px before:bg-border/50">
      <div v-for="(step, index) in steps" :key="step.id || index" class="relative flex items-start gap-3">
        <div class="relative z-10 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-background mt-0.5">
          <CheckCircle2 v-if="step.status === 'completed'" class="h-4 w-4 text-emerald-500" />
          <Loader2 v-else-if="step.status === 'running'" class="h-4 w-4 text-primary animate-spin" />
          <XCircle v-else-if="step.status === 'error'" class="h-4 w-4 text-destructive" />
          <Circle v-else class="h-3.5 w-3.5 text-muted-foreground/40" />
        </div>
        <div class="flex flex-col pt-0.5 min-w-0">
          <span 
            class="text-[13px] leading-tight" 
            :class="{
              'text-foreground font-medium': step.status === 'running',
              'text-muted-foreground': step.status === 'completed',
              'text-destructive': step.status === 'error',
              'text-muted-foreground/60': step.status === 'pending'
            }"
          >
            {{ step.text }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
