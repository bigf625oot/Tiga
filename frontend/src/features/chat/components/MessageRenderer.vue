<script setup lang="ts">
import { computed } from 'vue';
import type { ChatMessage, ToolResultBlock, ToolCallBlock } from '../types';
import ThoughtAccordion from './ThoughtAccordion.vue';
import ActionCard from './ActionCard.vue';
import ToolStatusCard from './ToolStatusCard.vue';
import TerminalBlock from './TerminalBlock.vue';
import PlanBlock from './PlanBlock.vue';
// Optional: import markdown renderer for TextBlock if available. For now, simple text.

const props = defineProps<{
  message: ChatMessage;
}>();

const emit = defineEmits<{
  (e: 'apply-action', path: string): void;
  (e: 'discard-action', path: string): void;
}>();

// Helper to find tool result for a tool call
const getToolResult = (callId: string): ToolResultBlock | undefined => {
  return props.message.blocks.find(
    (b) => b.type === 'tool_result' && b.call_id === callId
  ) as ToolResultBlock | undefined;
};

// Filter out tool_result blocks from direct rendering, as they are rendered inside ToolStatusCard
const renderableBlocks = computed(() => {
  return props.message.blocks.filter(b => b.type !== 'tool_result');
});
</script>

<template>
  <div class="flex flex-col space-y-3 max-w-3xl w-full mx-auto p-4">
    <!-- Message Avatar & Wrapper could go here, but focusing on Blocks -->
    <div 
      v-for="(block, index) in renderableBlocks" 
      :key="index"
      class="w-full"
    >
      <template v-if="block.type === 'thought'">
        <ThoughtAccordion :block="block" />
      </template>

      <template v-else-if="block.type === 'plan'">
        <PlanBlock :block="block" />
      </template>

      <template v-else-if="block.type === 'tool_call'">
        <ToolStatusCard 
          :tool-call="block as ToolCallBlock" 
          :tool-result="getToolResult((block as ToolCallBlock).call_id)" 
        />
      </template>

      <template v-else-if="block.type === 'action'">
        <ActionCard 
          :block="block" 
          @apply="path => emit('apply-action', path)"
          @discard="path => emit('discard-action', path)"
        />
      </template>

      <template v-else-if="block.type === 'terminal'">
        <TerminalBlock :block="block" />
      </template>

      <template v-else-if="block.type === 'text'">
        <!-- Simple text rendering, in real app use Markdown -->
        <div class="text-sm text-foreground leading-relaxed whitespace-pre-wrap px-2 py-1">
          {{ block.content }}
        </div>
      </template>
      
      <template v-else-if="block.type === 'search'">
        <div class="rounded-xl border border-border bg-card p-3 text-sm">
          <div class="font-medium mb-2">Searching: "{{ block.query }}"</div>
          <div class="flex flex-col gap-1">
            <a 
              v-for="(source, idx) in block.sources" 
              :key="idx" 
              :href="source.url" 
              target="_blank"
              class="text-blue-500 hover:underline flex items-center gap-2"
            >
              <img v-if="source.favicon" :src="source.favicon" class="w-3 h-3" />
              {{ source.title }}
            </a>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
