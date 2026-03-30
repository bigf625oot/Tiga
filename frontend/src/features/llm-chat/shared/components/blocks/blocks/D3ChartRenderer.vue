<template>
  <div class="w-full bg-card rounded-lg border border-border shadow-sm overflow-hidden hover:shadow-md transition-shadow d3-chart-container">
    <div class="p-4 py-2 border-b border-border bg-muted/50 flex items-center justify-between">
      <span class="text-xs font-semibold text-foreground flex items-center gap-2">
        <svg class="w-3.5 h-3.5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
        </svg>
        D3 可视化
      </span>
    </div>
    <div class="p-4 bg-card w-full flex justify-center overflow-x-auto">
        <div ref="chartContainer" class="w-full min-h-[250px] flex justify-center items-center relative"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';

const props = defineProps<{
  config: any; // We expect D3 to be driven either by raw data or by a specific function string. For safety, we expect the config to be data and we render a basic chart, or a standardized JSON representation.
}>();

const chartContainer = ref<HTMLElement | null>(null);

const renderChart = async () => {
  if (!chartContainer.value || !props.config) return;
  
  // Clear previous SVG
  chartContainer.value.innerHTML = '';
  
  try {
    // Dynamic import to reduce initial bundle size
    const d3 = await import('d3');
    
    // We assume config contains { type: 'bar' | 'line' | 'pie', data: [] } 
    // This is a minimal safe implementation. Executing raw D3 code strings from LLM is unsafe.
    const { type, data, options = {} } = props.config;
    
    if (!data || !Array.isArray(data)) {
        chartContainer.value.innerHTML = '<div class="text-sm text-muted-foreground">Invalid D3 data format</div>';
        return;
    }

    const width = options.width || chartContainer.value.clientWidth || 600;
    const height = options.height || 300;
    const margin = options.margin || { top: 20, right: 20, bottom: 30, left: 40 };

    const svg = d3.select(chartContainer.value)
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height])
      .attr("style", "max-width: 100%; height: auto;");

    if (type === 'bar') {
        const x = d3.scaleBand()
            .domain(data.map(d => d.name || d.x))
            .range([margin.left, width - margin.right])
            .padding(0.1);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.value || d.y) as number]).nice()
            .range([height - margin.bottom, margin.top]);

        svg.append("g")
            .attr("fill", "steelblue")
            .selectAll("rect")
            .data(data)
            .join("rect")
            .attr("x", d => x(d.name || d.x) as number)
            .attr("y", d => y(d.value || d.y))
            .attr("height", d => y(0) - y(d.value || d.y))
            .attr("width", x.bandwidth());

        svg.append("g")
            .attr("transform", `translate(0,${height - margin.bottom})`)
            .call(d3.axisBottom(x));

        svg.append("g")
            .attr("transform", `translate(${margin.left},0)`)
            .call(d3.axisLeft(y));
            
    } else if (type === 'line') {
        const x = d3.scalePoint()
            .domain(data.map(d => d.name || d.x))
            .range([margin.left, width - margin.right]);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.value || d.y) as number]).nice()
            .range([height - margin.bottom, margin.top]);

        const line = d3.line<any>()
            .x(d => x(d.name || d.x) as number)
            .y(d => y(d.value || d.y));

        svg.append("path")
            .datum(data)
            .attr("fill", "none")
            .attr("stroke", "steelblue")
            .attr("stroke-width", 1.5)
            .attr("d", line);

        svg.append("g")
            .attr("transform", `translate(0,${height - margin.bottom})`)
            .call(d3.axisBottom(x));

        svg.append("g")
            .attr("transform", `translate(${margin.left},0)`)
            .call(d3.axisLeft(y));
    } else {
        chartContainer.value.innerHTML = '<div class="text-sm text-muted-foreground">Unsupported D3 chart type. Only bar/line are supported via JSON.</div>';
    }
  } catch (error) {
    console.error('Failed to render D3 chart:', error);
    chartContainer.value.innerHTML = '<div class="text-sm text-destructive">Error rendering chart</div>';
  }
};

onMounted(() => {
  renderChart();
  
  // Basic resize observer
  const resizeObserver = new ResizeObserver(() => {
      renderChart();
  });
  if (chartContainer.value) {
      resizeObserver.observe(chartContainer.value);
  }
});

watch(() => props.config, () => {
  renderChart();
}, { deep: true });
</script>
