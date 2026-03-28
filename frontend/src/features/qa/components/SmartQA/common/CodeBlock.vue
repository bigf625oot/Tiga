<template>
  <div class="code-block-wrapper relative group my-4 rounded-lg overflow-hidden border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-[#0d1117]">
    <div class="code-block-header flex items-center justify-between px-4 py-1.5 bg-zinc-100 dark:bg-[#161b22] border-b border-zinc-200 dark:border-zinc-800">
      <span class="text-xs font-mono text-zinc-500 dark:text-zinc-400">{{ language }}</span>
      <button 
        class="copy-btn opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-zinc-200 dark:hover:bg-zinc-800 rounded text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200" 
        @click="copyToClipboard"
        title="Copy code"
      >
        <Check v-if="copied" class="text-emerald-500 w-3.5 h-3.5" />
        <Copy v-else class="w-3.5 h-3.5" />
      </button>
    </div>
    <div class="p-4 m-0 overflow-x-auto text-sm leading-relaxed custom-scrollbar text-zinc-800 dark:text-gray-100">
      <component :is="renderCodeNodes()" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, h } from 'vue';
import { Check, Copy } from 'lucide-vue-next';
import { useToast } from '@/components/ui/toast/use-toast';

const props = defineProps<{
  language?: string;
  rawCode: string;
  codeAstNodes?: any[]; // The Hast nodes or pre-rendered VNodes for the <code> tag
}>();

const copied = ref(false);
const { toast } = useToast();

const renderCodeNodes = () => {
  return h('pre', { class: 'm-0 p-0 bg-transparent' }, 
    props.codeAstNodes ? props.codeAstNodes : [h('code', props.rawCode)]
  );
};

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
</script>