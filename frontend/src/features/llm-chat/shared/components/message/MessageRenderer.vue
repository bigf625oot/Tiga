<script setup lang="ts">
import { computed, inject } from 'vue';
import type { ChatMessage } from '@/features/llm-chat/shared/types';
import { BlockRendererRegistry } from '../blocks/BlockRendererRegistry';
import { ChatContextKey } from '@/features/llm-chat/shared/context/ChatContext';
import DocumentCard from '@/features/llm-chat/shared/components/common/DocumentCard.vue';
import SourceCard from '@/features/llm-chat/shared/components/common/SourceCard.vue';

const props = defineProps<{
  message: ChatMessage;
}>();

const emit = defineEmits<{
  (e: 'apply-action', path: string): void;
  (e: 'discard-action', path: string): void;
  (e: 'locate-node', ref: any): void;
  (e: 'open-doc-space', id: string): void;
  (e: 'resend-message'): void;
}>();

const chatContext = inject(ChatContextKey);

// Filter out tool_result blocks from direct rendering, as they are rendered inside ToolStatusCard
const renderableBlocks = computed(() => {
  return props.message.blocks.filter(b => b.type !== 'tool_result');
});

// Generic event forwarder
const handleEvent = (eventName: string, payload?: any) => {
  if (eventName === 'apply-action' || eventName === 'discard-action' || eventName === 'locate-node' || eventName === 'open-doc-space') {
    emit(eventName as any, payload);
  } else if (eventName === 'resend-message') {
    emit(eventName as any);
  }
};

// 提取所有文本块中的 doc# 引用，用于在底部集中展示卡片
const extractedDocIds = computed(() => {
  const docs = new Map<string, { id: string; title: string }>();
  
  props.message.blocks.forEach(block => {
    if (block.type === 'text') {
      const text = ('content' in block ? block.content : '') as string;
      const docCardRegex = /(?:[•▪·\-\*]\s*)?\*?\*?doc#\s*(\d+)\*?\*?(?:[:：]\s*(?:《([^》\n]+)》|\*([^\*\n]+)\*|([^\n，。；！？\[\]]+)))?/gi;
      
      let match;
      while ((match = docCardRegex.exec(text)) !== null) {
        const docId = match[1];
        const title = (match[2] || match[3] || match[4] || '').trim();
        if (!docs.has(docId)) {
          docs.set(docId, { id: docId, title });
        }
      }
    }
  });
  
  return Array.from(docs.values());
});

// 提取所有文本块中的 Markdown 链接 [text](url) 用于在底部集中展示为参考网页卡片
const extractedLinks = computed(() => {
  const links = new Map<string, { url: string; title: string }>();
  
  props.message.blocks.forEach(block => {
    if (block.type === 'text') {
      const text = ('content' in block ? block.content : '') as string;
      // 匹配标准的 Markdown 链接，但排除可能产生冲突的图片 ![alt](url)
      const linkRegex = /(?<!\!)\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g;
      
      let match;
      while ((match = linkRegex.exec(text)) !== null) {
        const title = match[1].trim();
        const url = match[2].trim();
        if (!links.has(url)) {
          links.set(url, { url, title });
        }
      }
    }
  });
  
  return Array.from(links.values());
});
</script>

<template>
  <div class="flex flex-col space-y-3 w-full max-w-full overflow-hidden">
    <template v-if="renderableBlocks && renderableBlocks.length > 0">
      <div 
        v-for="(block, index) in renderableBlocks" 
        :key="index"
        class="w-full max-w-full overflow-hidden"
      >
        <component 
          v-if="BlockRendererRegistry[block.type]"
          :is="BlockRendererRegistry[block.type]" 
          :block="block"
          :message-blocks="props.message.blocks"
          :context="chatContext"
          @apply-action="(p: string) => handleEvent('apply-action', p)"
          @discard-action="(p: string) => handleEvent('discard-action', p)"
          @locate-node="(ref: any) => handleEvent('locate-node', ref)"
          @open-doc-space="(id: string) => handleEvent('open-doc-space', id)"
          @resend-message="handleEvent('resend-message')"
        />
        <!-- Fallback for unknown block types: Graceful Degradation -->
        <component 
          v-else-if="BlockRendererRegistry['text']"
          :is="BlockRendererRegistry['text']"
          :block="{ type: 'text', content: ('content' in block ? block.content : JSON.stringify(block)) }"
          :message-blocks="props.message.blocks"
          :context="chatContext"
        />
        <div v-else class="p-2 border border-yellow-500/30 bg-yellow-500/10 text-yellow-600 rounded text-xs">
          <!-- Fallback of last resort if text renderer is somehow missing -->
          [Unknown Block: {{ block.type }}]
        </div>
      </div>
    </template>

    <!-- Appended Document Cards extracted from text -->
    <div v-if="extractedDocIds.length > 0" class="mt-2 flex flex-col gap-2">
      <div class="text-[11px] text-muted-foreground/60 font-medium px-1 uppercase tracking-widest">相关文档</div>
      <div class="flex flex-wrap gap-2">
        <DocumentCard
          v-for="docInfo in extractedDocIds"
          :key="docInfo.id"
          :doc-id="docInfo.id"
          :title="docInfo.title"
          class="w-full max-w-[320px]"
          @click="handleEvent('open-doc-space', docInfo.id)"
        />
      </div>
    </div>

    <!-- Appended Web Source Cards extracted from text links -->
    <div v-if="extractedLinks.length > 0" class="mt-1 flex flex-col gap-2">
      <div class="text-[11px] text-muted-foreground/60 font-medium px-1 uppercase tracking-widest">参考网页</div>
      <div class="flex flex-wrap gap-2">
        <SourceCard
          v-for="(link, idx) in extractedLinks"
          :key="`link-${idx}`"
          :source="{ url: link.url, title: link.title }"
          type="web"
          size="sm"
          class="w-full max-w-[320px]"
        />
      </div>
    </div>
  </div>
</template>
