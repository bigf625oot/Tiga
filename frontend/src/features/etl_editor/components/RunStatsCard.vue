<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { HelpCircle } from 'lucide-vue-next';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

type Trend = 'up' | 'down';

type Metric = {
  label: string;
  value: string | number;
  unit?: string;
  trend?: Trend;
  description?: string;
};

const props = defineProps<{
  metrics: Metric[];
  lastRunAt?: string;
}>();

const now = ref(Date.now());
let timer: number | null = null;

const startTimer = () => {
  if (timer != null) return;
  timer = window.setInterval(() => {
    now.value = Date.now();
  }, 1000);
};

const stopTimer = () => {
  if (timer == null) return;
  window.clearInterval(timer);
  timer = null;
};

onMounted(() => {
  if (props.lastRunAt) startTimer();
});

onBeforeUnmount(() => {
  stopTimer();
});

watch(
  () => props.lastRunAt,
  (v) => {
    if (v) startTimer();
    else stopTimer();
  }
);

const durationText = computed(() => {
  if (!props.lastRunAt) return null;
  const start = Date.parse(props.lastRunAt);
  if (Number.isNaN(start)) return null;
  const ms = Math.max(0, now.value - start);
  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  const mmss = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  if (hours <= 0) return mmss;
  return `${String(hours).padStart(2, '0')}:${mmss}`;
});

const metricsToShow = computed<Metric[]>(() => {
  if (!durationText.value) return props.metrics;
  return [...props.metrics, { label: '运行时长', value: durationText.value }];
});
</script>

<template>
  <div class="bg-card/90 backdrop-blur border border-border rounded-lg shadow-lg px-3 py-2.5 transition-all duration-300">
    <div class="flex items-center gap-2 pb-2 border-b border-border/70">
      <div class="text-[11px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
        <span>运行统计</span>
        <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
      </div>
    </div>

    <div class="pt-2 flex flex-wrap items-center gap-x-4 gap-y-2">
      <div v-for="(metric, idx) in metricsToShow" :key="idx" class="flex flex-col min-w-[88px]">
        <div class="flex items-center gap-1.5 mb-0.5">
          <TooltipProvider v-if="metric.description">
            <Tooltip :delay-duration="300">
              <TooltipTrigger as-child>
                <div class="flex items-center gap-1 cursor-help group">
                  <span class="text-[10px] text-muted-foreground truncate font-medium group-hover:text-foreground transition-colors">
                    {{ metric.label }}
                  </span>
                  <HelpCircle class="w-3 h-3 text-muted-foreground/50 group-hover:text-primary transition-colors" />
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" align="start" class="bg-popover text-popover-foreground shadow-md border border-border">
                <p class="text-xs font-normal max-w-[220px]">{{ metric.description }}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <span v-else class="text-[10px] text-muted-foreground truncate font-medium">
            {{ metric.label }}
          </span>

          <div v-if="metric.trend" class="flex items-center">
            <svg
              v-if="metric.trend === 'up'"
              class="w-2.5 h-2.5 text-green-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            <svg
              v-else
              class="w-2.5 h-2.5 text-red-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
            </svg>
          </div>
        </div>

        <div class="flex items-baseline gap-1">
          <span class="text-[15px] font-bold font-mono tracking-tight text-foreground leading-none">
            {{ metric.value }}
          </span>
          <span v-if="metric.unit" class="text-[10px] text-muted-foreground/80 font-medium leading-none">
            {{ metric.unit }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
