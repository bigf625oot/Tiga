<script setup lang="ts">
import { ref } from 'vue';
import MessageRenderer from './MessageRenderer.vue';
import { mockMessage } from '../mock/chatMock';

const message = ref(mockMessage);

const handleApplyAction = (path: string) => {
  console.log(`Action applied for: ${path}`);
  // Find the action block and update its status
  const block = message.value.blocks.find(b => b.type === 'action' && b.path === path);
  if (block && block.type === 'action') {
    block.status = 'applied';
  }
};

const handleDiscardAction = (path: string) => {
  console.log(`Action discarded for: ${path}`);
  const block = message.value.blocks.find(b => b.type === 'action' && b.path === path);
  if (block && block.type === 'action') {
    block.status = 'rejected';
  }
};
</script>

<template>
  <div class="h-full w-full bg-background flex flex-col items-center py-8 overflow-y-auto">
    <div class="text-center mb-8">
      <h1 class="text-2xl font-bold tracking-tight mb-2">Agent Chat System</h1>
      <p class="text-sm text-muted-foreground">Block-based protocol rendering demo</p>
    </div>
    
    <MessageRenderer 
      :message="message" 
      @apply-action="handleApplyAction"
      @discard-action="handleDiscardAction"
    />
  </div>
</template>
