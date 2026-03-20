<template>
  <div class="thinking-block w-full my-2">
    <Collapsible v-model:open="isOpen" class="border-l-2 border-primary/20 bg-muted/20 rounded-r-lg overflow-hidden transition-all duration-300">
      <!-- 头部开关 -->
      <CollapsibleTrigger as-child>
        <button class="w-full flex items-center justify-between px-4 py-2 hover:bg-muted/40 transition-colors group outline-none">
          <div class="flex items-center gap-2">
            <!-- 思考状态图标 -->
            <div class="relative w-4 h-4 flex items-center justify-center">
              <Brain v-if="!isThinking" class="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary transition-colors" />
              <Loader2 v-else class="w-3.5 h-3.5 text-primary animate-spin" />
            </div>
            
            <span class="text-xs font-medium" :class="isThinking ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'">
              {{ isThinking ? '正在思考...' : `思考过程 (${timeSpent || '已完成'})` }}
            </span>
          </div>
          
          <ChevronDown 
            class="w-4 h-4 text-muted-foreground/50 transition-transform duration-200"
            :class="isOpen ? 'rotate-180' : ''"
          />
        </button>
      </CollapsibleTrigger>
      
      <!-- 内容区域 -->
      <CollapsibleContent class="px-4 pb-3 pt-1 text-sm text-muted-foreground font-mono leading-relaxed overflow-x-auto whitespace-pre-wrap">
        {{ content }}
        <span v-if="isThinking" class="inline-block w-1.5 h-3.5 ml-1 bg-primary align-middle animate-pulse"></span>
      </CollapsibleContent>
    </Collapsible>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { Brain, ChevronDown, Loader2 } from 'lucide-vue-next';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible';

const props = defineProps<{
  content: string;
  isThinking?: boolean;
  timeSpent?: string;
}>();

// 默认在思考中展开，思考结束后根据用户偏好决定（这里默认收起）
const isOpen = ref(true);

watch(() => props.isThinking, (newVal, oldVal) => {
  if (oldVal && !newVal) {
    // 当思考结束时，自动收起以节省空间（遵循尼尔森极简设计原则）
    setTimeout(() => {
      isOpen.value = false;
    }, 1500);
  }
});
</script>

<style scoped>
.thinking-block {
  /* 增加柔和的阴影和过渡 */
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
</style>