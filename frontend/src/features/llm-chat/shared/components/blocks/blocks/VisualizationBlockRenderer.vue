<script setup lang="ts">
import { defineAsyncComponent } from 'vue';
import ChartFrame from '@/features/analytics/components/ChartFrame.vue';
import type { VisualizationBlock } from '@/features/llm-chat/shared/types';

const MermaidRenderer = defineAsyncComponent(
    () => import('@/features/llm-chat/shared/components/common/MermaidRenderer.vue')
);
const MarkmapRenderer = defineAsyncComponent(
    () => import('@/features/llm-chat/shared/components/common/MarkmapRenderer.vue')
);
const AntVChartRenderer = defineAsyncComponent(
    () => import('@/features/llm-chat/shared/components/blocks/blocks/AntVChartRenderer.vue')
);
const D3ChartRenderer = defineAsyncComponent(
    () => import('@/features/llm-chat/shared/components/blocks/blocks/D3ChartRenderer.vue')
);

defineProps<{
  block: VisualizationBlock;
}>();

const parseChartOption = (data: any) => {
    if (typeof data === 'object' && data !== null) return data;
    try {
        return JSON.parse(data);
    } catch (e) {
        return null;
    }
};
</script>

<template>
  <div v-if="block.vis_type === 'echarts' || block.vis_type === 'dynamic_chart'" class="w-full bg-card rounded-lg border border-border shadow-sm overflow-hidden hover:shadow-md transition-shadow">
      <div class="p-4 py-2 border-b border-border bg-muted/50 flex items-center justify-between">
          <span class="text-xs font-semibold text-foreground flex items-center gap-2">
              <svg class="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
              {{ block.vis_type === 'dynamic_chart' ? '动态数据可视化' : '数据可视化' }}
          </span>
      </div>
      <div class="h-64 w-full relative bg-card">
          <ChartFrame :option="parseChartOption(block.data)" />
      </div>
  </div>

  <AntVChartRenderer v-else-if="block.vis_type === 'antv'" :config="parseChartOption(block.data)" />
  
  <D3ChartRenderer v-else-if="block.vis_type === 'd3'" :config="parseChartOption(block.data)" />

  <MermaidRenderer v-else-if="block.vis_type === 'mermaid'" :code="block.data" />
  <MarkmapRenderer v-else-if="block.vis_type === 'markmap'" :content="block.data" />
</template>
