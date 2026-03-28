<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { Brain, ChevronDown, ChevronRight } from 'lucide-vue-next';
import type { ThoughtBlock } from '../types';

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

const toggle = () => {
  isExpanded.value = !isExpanded.value;
};
</script>

<template>
  <div class="rounded-xl border border-border bg-muted/30 overflow-hidden shadow-sm flex flex-col transition-all duration-300">
    <!-- Header -->
    <div 
      class="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-muted/50 transition-colors"
      @click="toggle"
    >
      <div class="w-0.5 h-4 bg-primary/50 rounded-full"></div>
      <Brain class="w-4 h-4 text-muted-foreground" />
      <span class="text-sm font-medium text-muted-foreground select-none flex-1">
        {{ block.state === 'thinking' ? 'Thinking...' : 'Thought process' }}
      </span>
      <ChevronDown v-if="isExpanded" class="w-4 h-4 text-muted-foreground" />
      <ChevronRight v-else class="w-4 h-4 text-muted-foreground" />
    </div>

    <!-- Content -->
    <div 
      v-show="isExpanded" 
      class="px-4 py-3 text-sm text-foreground/80 border-t border-border/50 bg-background/50 leading-relaxed whitespace-pre-wrap"
    >
      {{ block.content }}
    </div>
  </div>
</template>
