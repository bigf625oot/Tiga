<script setup lang="ts">
import ChartFrame from '../../../analytics/components/ChartFrame.vue';
import type { VisualizationBlock } from '../../types';

defineProps<{
  block: VisualizationBlock;
}>();

const parseChartOption = (data: string) => {
    try {
        return JSON.parse(data);
    } catch (e) {
        return null;
    }
};
</script>

<template>
  <div v-if="block.vis_type === 'echarts'" class="w-full bg-card rounded-lg border border-border shadow-sm overflow-hidden hover:shadow-md transition-shadow">
      <div class="p-4 py-2 border-b border-border bg-muted/50 flex items-center justify-between">
          <span class="text-xs font-semibold text-foreground flex items-center gap-2">
              <svg class="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
              数据可视化
          </span>
      </div>
      <div class="h-64 w-full relative bg-card">
          <ChartFrame :option="parseChartOption(block.data)" />
      </div>
  </div>
</template>