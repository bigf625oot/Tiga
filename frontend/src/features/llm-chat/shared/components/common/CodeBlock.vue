<script lang="ts">
import { ref, h, defineComponent, watch } from 'vue';
import { Check, Copy } from 'lucide-vue-next';
import { useToast } from '@/components/ui/toast/use-toast';
import { highlightCode, escapeHtml } from '@/features/llm-chat/shared/composables/useMarkdown';

export default defineComponent({
  name: 'CodeBlock',
  props: {
    language: String,
    rawCode: { type: String, required: true },
  },
  setup(props) {
    const copied = ref(false);
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

    // PrismJS 是同步的，直接计算高亮
    const highlightedHtml = () => highlightCode(props.rawCode, props.language || 'text');

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
        // Body: PrismJS 高亮后的 HTML 直接注入
        h('div', { class: 'p-4 m-0 overflow-x-auto text-sm leading-relaxed custom-scrollbar' }, [
          h('pre', { class: 'm-0 p-0 bg-transparent text-zinc-200 font-mono whitespace-pre' }, [
            h('code', {
              class: `language-${props.language || 'text'}`,
              innerHTML: highlightedHtml()
            })
          ])
        ])
      ]
    );
  }
});
</script>
