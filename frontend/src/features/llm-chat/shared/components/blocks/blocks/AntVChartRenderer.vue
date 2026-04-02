<template>
  <div class="w-full bg-card rounded-lg border border-border shadow-sm overflow-hidden hover:shadow-md transition-shadow antv-chart-container">
    <div class="p-4 py-2 border-b border-border bg-muted/50 flex items-center justify-between">
      <span class="text-xs font-semibold text-foreground flex items-center gap-2">
        <svg class="w-3.5 h-3.5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
        </svg>
        AntV 可视化
      </span>
    </div>
    <div class="p-4 bg-card w-full flex justify-center">
        <div ref="chartContainer" class="w-full h-64"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import { Chart } from '@antv/g2';

const props = defineProps<{
  config: any;
}>();

const chartContainer = ref<HTMLElement | null>(null);
let chartInstance: Chart | null = null;

const renderChart = () => {
  if (!chartContainer.value || !props.config) return;

  // Cleanup existing instance
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  try {
    chartInstance = new Chart({
      container: chartContainer.value,
      autoFit: true,
    });

    // Apply config to chart
    chartInstance.options(props.config);
    chartInstance.render();
  } catch (error) {
    console.error('Failed to render AntV chart:', error);
  }
};

onMounted(() => {
  renderChart();
});

watch(() => props.config, () => {
  renderChart();
}, { deep: true });

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
});
</script>
