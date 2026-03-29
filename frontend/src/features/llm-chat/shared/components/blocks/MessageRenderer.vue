<script setup lang="ts">
import { computed, inject } from 'vue';
import type { ChatMessage } from '@/features/llm-chat/shared/types';
import { BlockRendererRegistry } from './BlockRendererRegistry';
import { ChatContextKey } from '@/features/llm-chat/shared/context/ChatContext';

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
        <!-- Fallback for unknown block types -->
        <div v-else class="p-2 border border-red-500/30 bg-red-500/10 text-red-500 rounded text-xs">
          Unknown block type: {{ block.type }}
        </div>
      </div>
    </template>
  </div>
</template>
