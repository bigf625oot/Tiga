<template>
  <div class="mermaid-container my-4 p-4 bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800 flex justify-center overflow-x-auto">
    <div ref="mermaidRef" class="mermaid"></div>
    <div v-if="error" class="text-red-500 text-sm p-2 bg-red-50 dark:bg-red-950/30 rounded w-full text-left font-mono whitespace-pre-wrap">
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import mermaid from 'mermaid';

const props = defineProps<{
  code: string;
}>();

const mermaidRef = ref<HTMLElement | null>(null);
const error = ref<string | null>(null);

let seq = 0;

const renderDiagram = async () => {
  if (!mermaidRef.value || !props.code) return;
  
  try {
    error.value = null;
    mermaidRef.value.innerHTML = ''; // clear previous
    const id = `mermaid-${Date.now()}-${++seq}`;
    const { svg } = await mermaid.render(id, props.code.trim());
    mermaidRef.value.innerHTML = svg;
  } catch (err: any) {
    console.error('Mermaid rendering failed:', err);
    error.value = err.message || 'Failed to render Mermaid diagram';
  }
};

onMounted(() => {
  mermaid.initialize({ startOnLoad: false, theme: document.documentElement.classList.contains('dark') ? 'dark' : 'default' });
  renderDiagram();
});

watch(() => props.code, renderDiagram);
</script>

<style scoped>
.mermaid-container :deep(svg) {
  max-width: 100%;
  height: auto;
}
</style>