<template>
  <div class="thinking-block w-full my-1">
    <Collapsible v-model:open="isOpen" class="bg-transparent overflow-hidden transition-all duration-300">
      <!-- 头部开关 -->
      <CollapsibleTrigger as-child>
        <button class="w-full flex items-center justify-between px-2 py-1.5 hover:bg-muted/30 transition-colors group outline-none rounded">
          <div class="flex items-center gap-2">
            <!-- 思考状态图标 -->
            <div class="relative w-4 h-4 flex items-center justify-center">
              <Brain v-if="!isThinking" class="w-3.5 h-3.5 text-muted-foreground/60 group-hover:text-muted-foreground transition-colors" />
              <Loader2 v-else class="w-3.5 h-3.5 text-muted-foreground/80 animate-spin" />
            </div>

            <span class="text-[11px] font-medium tracking-tight" :class="isThinking ? 'text-muted-foreground/80' : 'text-muted-foreground/60 group-hover:text-muted-foreground'">
              {{ isThinking ? 'Thought Process' : `Thought Process (${timeSpent || 'Complete'})` }}
            </span>
          </div>

          <ChevronDown
            class="w-3.5 h-3.5 text-muted-foreground/40 transition-transform duration-200 group-hover:text-muted-foreground/60"
            :class="isOpen ? 'rotate-180' : ''"
          />
        </button>
      </CollapsibleTrigger>

      <!-- 内容区域 — 固定最大高度，启用滚动 -->
      <CollapsibleContent>
        <div
          ref="contentRef"
          class="px-3 pb-3 pt-1 text-[13px] text-muted-foreground/80 font-mono leading-relaxed overflow-x-auto overflow-y-auto whitespace-pre-wrap max-h-64 custom-scrollbar border-l-2 border-border/40 ml-2.5 pl-4"
        >{{ content }}<span v-if="isThinking" class="inline-block w-1.5 h-3.5 ml-1 bg-muted-foreground/50 align-middle animate-pulse"></span>
        </div>
      </CollapsibleContent>
    </Collapsible>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import { Brain, ChevronDown, Loader2 } from 'lucide-vue-next';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible';

const props = defineProps<{
  content: string;
  isThinking?: boolean;
  timeSpent?: string;
}>();

const isOpen = ref(true);
const contentRef = ref<HTMLElement | null>(null);

// Auto-scroll to bottom as new think tokens arrive
watch(() => props.content, () => {
  if (!props.isThinking) return;
  nextTick(() => {
    if (contentRef.value) {
      contentRef.value.scrollTop = contentRef.value.scrollHeight;
    }
  });
});

watch(() => props.isThinking, (newVal, oldVal) => {
  if (oldVal && !newVal) {
    // 当思考结束时，自动收起以节省空间
    setTimeout(() => {
      isOpen.value = false;
    }, 1500);
  }
});
</script>

<style scoped>
.thinking-block {
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
</style>