<template>
  <div 
    class="markdown-body text-sm leading-normal" 
    v-html="renderedHtml"
    @click="handleContentClick"
  ></div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useMarkdown } from '../../composables/useMarkdown';
import { useToast } from '@/components/ui/toast/use-toast';

const props = defineProps<{
  content: string;
}>();

const { render, initHighlighter } = useMarkdown();
const { toast } = useToast();

// 在组件挂载时确保高亮器已加载，并触发重新渲染
onMounted(async () => {
    await initHighlighter();
});

// 使用 computed 缓存渲染结果（类似于 React 的 memo 效果，依赖项 `props.content` 变化时才重新计算）
const renderedHtml = computed(() => {
  return render(props.content || '');
});

// 事件委托：处理代码块的一键复制
const handleContentClick = async (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  const copyBtn = target.closest('.copy-btn');
  
  if (copyBtn) {
    const codeToCopy = copyBtn.getAttribute('data-code');
    if (codeToCopy) {
      try {
        // 解码 HTML 实体
        const txt = document.createElement('textarea');
        txt.innerHTML = codeToCopy;
        await navigator.clipboard.writeText(txt.value);
        
        // 视觉反馈
        const originalHtml = copyBtn.innerHTML;
        copyBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-emerald-500"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
        toast({
            title: "已复制到剪贴板",
            duration: 2000,
        });
        
        setTimeout(() => {
          copyBtn.innerHTML = originalHtml;
        }, 2000);
      } catch (err) {
        console.error('Failed to copy text: ', err);
      }
    }
  }
};
</script>

<style>
/* Markdown 基础样式调整，适配 shadcn/ui 的设计语言 */
.markdown-body {
  @apply text-foreground break-words;
}
.markdown-body p {
  @apply mb-2.5 last:mb-0;
}
.markdown-body a {
  @apply text-primary hover:underline underline-offset-4;
}
.markdown-body ul {
  @apply list-disc pl-5 mb-3 space-y-0.5;
}
.markdown-body ol {
  @apply list-decimal pl-5 mb-3 space-y-0.5;
}
.markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4 {
  @apply font-semibold tracking-tight text-foreground mt-4 mb-2;
}
.markdown-body h1 { @apply text-xl; }
.markdown-body h2 { @apply text-lg border-b border-border pb-1; }
.markdown-body h3 { @apply text-base; }
.markdown-body blockquote {
  @apply border-l-4 border-muted-foreground/30 pl-4 italic text-muted-foreground my-3;
}
/* 行内代码 */
.markdown-body code:not(.shiki) {
  @apply relative rounded bg-muted px-[0.3rem] py-[0.1rem] font-mono text-[13px] font-medium text-primary;
}
</style>