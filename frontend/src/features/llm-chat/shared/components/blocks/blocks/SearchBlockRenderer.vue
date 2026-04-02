<script setup lang="ts">
import { ref } from 'vue';
import { Globe, ChevronDown, ChevronRight } from 'lucide-vue-next';
import type { SearchBlock } from '@/features/llm-chat/shared/types';
import SourceCard from '@/features/llm-chat/shared/components/common/SourceCard.vue';

const props = defineProps<{
  block: SearchBlock;
}>();

const isExpanded = ref(true);
</script>

<template>
  <div class="inline-flex flex-col transition-all duration-300 w-full my-1">
    <button
      type="button"
      class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-card/50 hover:bg-muted/50 cursor-pointer transition-colors shadow-sm w-fit"
      :aria-expanded="isExpanded"
      :aria-controls="`search-sources-${block.query}`"
      @click="isExpanded = !isExpanded"
    >
      <Globe class="w-3.5 h-3.5 text-muted-foreground" />
      <span class="text-xs font-medium text-foreground/80">
        搜索了 {{ block.sources?.length || 0 }} 个网页
      </span>
      <ChevronDown v-if="isExpanded" class="w-3.5 h-3.5 text-muted-foreground ml-1" />
      <ChevronRight v-else class="w-3.5 h-3.5 text-muted-foreground ml-1" />
    </button>

    <div
      v-show="isExpanded && block.sources?.length > 0"
      :id="`search-sources-${block.query}`"
      role="list"
      class="mt-3 flex flex-col gap-2"
    >
      <SourceCard
        v-for="(source, idx) in block.sources"
        :key="idx"
        :source="{
          url: source.url,
          title: source.title,
          favicon: source.favicon,
        }"
        type="web"
        show-meta
        show-external-icon
        role="listitem"
      />
    </div>
  </div>
</template>
