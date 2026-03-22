<template>
  <div 
    class="markdown-body text-sm leading-normal" 
    v-html="renderedHtml"
    @click="handleContentClick"
  ></div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useMarkdown, isHighlighterReady } from '../../composables/useMarkdown';
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
  // 依赖 isHighlighterReady.value，当 shiki 加载完毕时会触发重新渲染
  // eslint-disable-next-line @typescript-eslint/no-unused-expressions
  isHighlighterReady.value;
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

<style scoped>
/* Markdown 基础样式调整，适配 shadcn/ui 的设计语言 */
.markdown-body {
  color: hsl(var(--foreground));
  word-break: break-word;
}
.markdown-body p {
  margin-bottom: 0.625rem;
}
.markdown-body p:last-child {
  margin-bottom: 0;
}
.markdown-body a {
  color: hsl(var(--primary));
  text-decoration: none;
}
.markdown-body a:hover {
  text-decoration: underline;
  text-underline-offset: 4px;
}
.markdown-body ul {
  list-style-type: disc;
  padding-left: 1.25rem;
  margin-bottom: 0.75rem;
}
.markdown-body ul li, .markdown-body ol li {
  margin-bottom: 0.125rem;
}
.markdown-body ol {
  list-style-type: decimal;
  padding-left: 1.25rem;
  margin-bottom: 0.75rem;
}
.markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4 {
  font-weight: 600;
  letter-spacing: -0.015em;
  color: hsl(var(--foreground));
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}
.markdown-body h1 { font-size: 1.25rem; line-height: 1.75rem; }
.markdown-body h2 { 
  font-size: 1.125rem; 
  line-height: 1.75rem;
  border-bottom: 1px solid hsl(var(--border));
  padding-bottom: 0.25rem;
}
.markdown-body h3 { font-size: 1rem; line-height: 1.5rem; }
.markdown-body blockquote {
  border-left: 4px solid hsl(var(--muted-foreground) / 0.3);
  padding-left: 1rem;
  font-style: italic;
  color: hsl(var(--muted-foreground));
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
}
/* 行内代码 */
.markdown-body code:not(.shiki) {
  position: relative;
  border-radius: 0.25rem;
  background-color: hsl(var(--muted));
  padding: 0.1rem 0.3rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 13px;
  font-weight: 500;
  color: hsl(var(--primary));
}

/* 修复 Shiki 内联代码块背景问题 */
.markdown-body pre code.shiki {
  background-color: transparent !important;
}
.markdown-body pre code.shiki .line {
  display: block;
  min-height: 1.5rem;
}
</style>