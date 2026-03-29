<script lang="ts">
import { ref, h, defineComponent, watch, onUnmounted } from 'vue';
import { Check, Copy } from 'lucide-vue-next';
import { useToast } from '@/components/ui/toast/use-toast';
import { getHighlighter } from '@/features/llm-chat/shared/composables/useMarkdown';

export default defineComponent({
  name: 'CodeBlock',
  props: {
    language: String,
    rawCode: { type: String, required: true },
  },
  setup(props) {
    const copied = ref(false);
    const highlightedCode = ref<string | null>(null);
    const { toast } = useToast();

    const copyToClipboard = async () => {
      try {
        await navigator.clipboard.writeText(props.rawCode);
        copied.value = true;
        toast({
          title: "已复制到剪贴板",
          duration: 2000,
        });
        setTimeout(() => {
          copied.value = false;
        }, 2000);
      } catch (err) {
        console.error('Failed to copy text: ', err);
      }
    };

    let timeoutId: number | null = null;

    const highlightCode = () => {
      const highlighter = getHighlighter();
      if (!highlighter || !props.language || props.language === 'text') {
        highlightedCode.value = null;
        return;
      }
      try {
        const html = highlighter.codeToHtml(props.rawCode, {
          lang: props.language,
          theme: 'github-dark' // 根据需要调整主题
        });
        // 剥离 shiki 外层，只保留内部代码
        const match = html.match(/<code[^>]*>([\s\S]*?)<\/code>/);
        if (match) {
          highlightedCode.value = match[1];
        } else {
          highlightedCode.value = html.replace(/^<pre[^>]*><code[^>]*>/, '').replace(/<\/code><\/pre>$/, '');
        }
      } catch (e) {
        console.warn(`Failed to highlight lang: ${props.language}`, e);
        highlightedCode.value = null;
      }
    };

    // 解决 Shiki CPU 抢占：流式阶段仅做纯文本追加，待停止变化后触发一次性高亮
    watch(() => props.rawCode, () => {
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
      
      // 动态防抖：如果 highlighter 已经就绪，缩短延迟到 100ms 以提升响应感
      const delay = getHighlighter() ? 100 : 500;
      
      timeoutId = window.setTimeout(() => {
        highlightCode();
      }, delay);
    }, { immediate: true });

    onUnmounted(() => {
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    });

    // 安全转义函数，避免 XSS
    const escapeHtml = (str: string) => {
      return str.replace(/[&<>"']/g, m => {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m] as string;
      });
    };

    // 回归第一性原理：最简单可靠的 pre > code 渲染
    return () => h(
      'div',
      { class: 'code-block-wrapper not-prose relative group my-4 rounded-lg overflow-hidden border border-zinc-200 dark:border-zinc-800 bg-[#0d1117]' },
      [
        // Header
        h('div', { class: 'code-block-header flex items-center justify-between px-4 py-1.5 bg-[#161b22] border-b border-zinc-200 dark:border-zinc-800' }, [
          h('span', { class: 'text-xs font-mono text-zinc-400' }, props.language || ''),
          h('button', {
            class: 'copy-btn opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-zinc-800 rounded text-zinc-400 hover:text-zinc-200',
            onClick: copyToClipboard,
            title: 'Copy code'
          }, [
            copied.value ? h(Check, { class: 'text-emerald-500 w-3.5 h-3.5' }) : h(Copy, { class: 'w-3.5 h-3.5' })
          ])
        ]),
        // Body: 采用单路渲染方案（统一走 innerHTML），彻底解决 VNode 与 innerHTML 冲突导致的白屏问题
        h('div', { class: 'p-4 m-0 overflow-x-auto text-sm leading-relaxed custom-scrollbar' }, [
          h('pre', { class: 'm-0 p-0 bg-transparent text-zinc-200 font-mono whitespace-pre' }, [
            h('code', { 
              class: highlightedCode.value ? `shiki language-${props.language}` : `language-${props.language}`,
              innerHTML: highlightedCode.value || escapeHtml(props.rawCode)
            })
          ])
        ])
      ]
    );
  }
});
</script>