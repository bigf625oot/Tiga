<template>
  <div class="h-full flex flex-col p-4 bg-white rounded-lg shadow-sm border border-slate-200">
    <h3 class="text-sm font-bold text-slate-700 mb-4 flex items-center">
      <DashboardOutlined class="mr-2" /> 资源监控
    </h3>
    
    <div class="grid grid-cols-1 gap-4 flex-1">
      <!-- CPU Chart -->
      <div class="h-32">
        <v-chart class="chart" :option="cpuOption" autoresize />
      </div>
      
      <!-- Memory Chart -->
      <div class="h-32">
        <v-chart class="chart" :option="memOption" autoresize />
      </div>

      <!-- Process List -->
      <div class="flex-1 overflow-auto border-t border-slate-100 pt-2">
        <h4 class="text-xs font-semibold text-slate-500 mb-2">活跃进程</h4>
        <table class="w-full text-xs text-left">
            <thead class="text-slate-400 font-medium">
                <tr>
                    <th class="pb-1">PID</th>
                    <th class="pb-1">CMD</th>
                    <th class="pb-1 text-right">CPU%</th>
                </tr>
            </thead>
            <tbody class="text-slate-600">
                <tr v-for="proc in processes" :key="proc.pid" class="border-b border-slate-50 last:border-0">
                    <td class="py-1 font-mono">{{ proc.pid }}</td>
                    <td class="py-1 truncate max-w-[120px]" :title="proc.cmd">{{ proc.cmd }}</td>
                    <td class="py-1 text-right">{{ proc.cpu.toFixed(1) }}</td>
                </tr>
            </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, TitleComponent } from 'echarts/components';
import VChart, { THEME_KEY } from 'vue-echarts';
import { DashboardOutlined } from '@ant-design/icons-vue';

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, TitleComponent]);

const props = defineProps(['sandboxId']);

// Mock Data for now, real implementation would use SSE/WebSocket
const cpuData = ref<number[]>([]);
const memData = ref<number[]>([]);
const processes = ref([
    { pid: 1, cmd: 'python app.py', cpu: 12.5 },
    { pid: 45, cmd: 'node server.js', cpu: 5.2 },
    { pid: 102, cmd: 'bash', cpu: 0.1 }
]);

let timer;

const updateCharts = () => {
    // Simulate real-time data
    const now = new Date();
    const cpu = Math.random() * 20 + 10;
    const mem = Math.random() * 100 + 200; // MB

    if (cpuData.value.length > 20) cpuData.value.shift();
    if (memData.value.length > 20) memData.value.shift();

    cpuData.value.push(cpu);
    memData.value.push(mem);
};

onMounted(() => {
    timer = setInterval(updateCharts, 2000);
});

onBeforeUnmount(() => {
    clearInterval(timer);
});

const commonOption = {
    grid: { top: 30, right: 10, bottom: 20, left: 40 },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', show: false },
};

const cpuOption = computed(() => ({
    ...commonOption,
    title: { text: 'CPU Usage (%)', textStyle: { fontSize: 12 } },
    yAxis: { type: 'value', max: 100 },
    series: [{
        data: cpuData.value,
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.1 },
        itemStyle: { color: '#3b82f6' }
    }]
}));

const memOption = computed(() => ({
    ...commonOption,
    title: { text: 'Memory (MB)', textStyle: { fontSize: 12 } },
    yAxis: { type: 'value' },
    series: [{
        data: memData.value,
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.1 },
        itemStyle: { color: '#10b981' }
    }]
}));
</script>

<style scoped>
.chart {
    height: 100%;
    width: 100%;
}
</style>
