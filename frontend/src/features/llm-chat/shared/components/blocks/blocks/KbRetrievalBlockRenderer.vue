<script setup lang="ts">
import { ref } from 'vue';
import { Database, ChevronDown, ChevronRight, Loader2 } from 'lucide-vue-next';
import type { KbRetrievalBlock } from '@/features/llm-chat/shared/types';
import SourceCard from '@/features/llm-chat/shared/components/common/SourceCard.vue';

const props = defineProps<{
  block: KbRetrievalBlock;
}>();

const isExpanded = ref(true);
</script>

<template>
  <div class="inline-flex flex-col transition-all duration-300 w-full my-1">
    <button
      type="button"
      class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-card/50 hover:bg-muted/50 cursor-pointer transition-colors shadow-sm w-fit"
      :aria-expanded="isExpanded"
      :aria-controls="`kb-results-${block.query}`"
      @click="isExpanded = !isExpanded"
    >
      <Loader2 v-if="block.status === 'searching'" class="w-3.5 h-3.5 text-primary animate-spin" />
      <Database v-else class="w-3.5 h-3.5 text-muted-foreground" />

      <span class="text-xs font-medium text-foreground/80">
        分析了 {{ block.results?.length || 0 }} 个知识片段
      </span>

      <ChevronDown v-if="isExpanded" class="w-3.5 h-3.5 text-muted-foreground ml-1" />
      <ChevronRight v-else class="w-3.5 h-3.5 text-muted-foreground ml-1" />
    </button>

    <div
      v-show="isExpanded && block.results?.length > 0"
      :id="`kb-results-${block.query}`"
      role="list"
      class="mt-3 flex flex-col gap-2"
    >
      <SourceCard
        v-for="(result, idx) in block.results"
        :key="idx"
        :source="{
          title: result.title || `Document ${idx + 1}`,
        }"
        type="doc"
        show-meta
        role="listitem"
      >
        <template #action>
          <span class="text-[10px] text-muted-foreground truncate max-w-[150px]">{{ result.source || '知识库' }}</span>
        </template>
      </SourceCard>
    </div>
  </div>
</template>
