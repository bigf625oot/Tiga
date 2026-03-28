<script setup lang="ts">
import ToolStatusCard from '../ToolStatusCard.vue';
import type { ToolCallBlock, ToolResultBlock } from '../../types';

defineProps<{
  block: ToolCallBlock;
  messageBlocks: any[];
}>();

// Helper to find tool result for a tool call
const getToolResult = (callId: string, blocks: any[]): ToolResultBlock | undefined => {
  return blocks.find(
    (b) => b.type === 'tool_result' && b.call_id === callId
  ) as ToolResultBlock | undefined;
};
</script>

<template>
  <ToolStatusCard 
    :tool-call="block" 
    :tool-result="getToolResult(block.call_id, messageBlocks)" 
  />
</template>