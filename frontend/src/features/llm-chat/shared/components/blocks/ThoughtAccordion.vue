<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import type { ThoughtBlock } from '@/features/llm-chat/shared/types';
import MarkdownRenderer from '@/features/llm-chat/shared/components/common/MarkdownRenderer.vue';

const props = defineProps<{
  block: ThoughtBlock;
}>();

const isExpanded = ref(props.block.state === 'expanded' || props.block.state === 'thinking');

// Auto-collapse logic: if it transitions from thinking to collapsed/expanded
watch(
  () => props.block.state,
  (newState, oldState) => {
    if (oldState === 'thinking' && newState === 'collapsed') {
      setTimeout(() => {
        isExpanded.value = false;
      }, 2000);
    } else if (newState === 'expanded') {
      isExpanded.value = true;
    } else if (newState === 'collapsed') {
      isExpanded.value = false;
    }
  }
);

const handleToggle = (e: Event) => {
  const details = e.target as HTMLDetailsElement;
  isExpanded.value = details.open;
};

const blockContent = computed(() => {
  let text = props.block.content || '';
  // Clean up potential <think> tags if they were included in the string
  text = text.replace(/^<think>\n?/, '').replace(/\n?<\/think>$/, '');
  return text.trim();
});
</script>

<template>
  <details 
    class="group mb-2" 
    :open="isExpanded"
    @toggle="handleToggle"
  >
    <summary class="list-none cursor-pointer flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors w-fit select-none">
      <div class="w-4 h-4 rounded-full border border-border flex items-center justify-center group-open:rotate-180 transition-transform">
        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="m6 9 6 6 6-6"/></svg>
      </div>
      <span class="text-[10px] font-bold uppercase tracking-widest">
        {{ block.state === 'thinking' ? 'Thinking...' : 'Thought' }}
      </span>
    </summary>
    <div class="mt-2 pl-4 ml-2 border-l-2 border-border/50 text-xs text-muted-foreground/80 italic whitespace-pre-wrap leading-relaxed">
      <MarkdownRenderer v-if="blockContent" :content="blockContent" prose-class="thought-prose" />
      <span v-else class="text-muted-foreground/50">无思考过程数据</span>
    </div>
  </details>
</template>

<style scoped>
summary::-webkit-details-marker {
  display: none;
}
:deep(.thought-prose) {
  color: inherit !important;
  font-size: inherit !important;
  font-style: inherit !important;
  line-height: inherit !important;
  max-width: none;
}
:deep(.thought-prose p) {
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}
:deep(.thought-prose p:first-child) {
  margin-top: 0;
}
:deep(.thought-prose p:last-child) {
  margin-bottom: 0;
}
:deep(.thought-prose pre) {
  font-style: normal;
  background-color: hsl(var(--muted));
  padding: 0.5rem;
  border-radius: 0.25rem;
  overflow-x: auto;
}
:deep(.thought-prose code) {
  font-family: monospace;
}
</style>
