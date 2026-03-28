import { ChatMessage } from '../types';

export const mockMessage: ChatMessage = {
  id: 'msg-001',
  role: 'assistant',
  status: 'completed',
  blocks: [
    {
      type: 'thought',
      content: 'I need to create a new component for the user. First, I will check the current directory, then create the file.',
      state: 'collapsed',
    },
    {
      type: 'tool_call',
      call_id: 'call-123',
      tool_name: 'fs_read_dir',
      arguments: { path: './src/components' },
      state: 'success',
    },
    {
      type: 'tool_result',
      call_id: 'call-123',
      content: '["Button.vue", "Input.vue"]',
      is_error: false,
    },
    {
      type: 'thought',
      content: 'The directory exists. Now I will write the new Card component.',
      state: 'collapsed',
    },
    {
      type: 'action',
      action_type: 'create_file',
      path: 'src/components/Card.vue',
      description: 'Create a new Card component',
      diff: '--- /dev/null\n+++ b/src/components/Card.vue\n@@ -0,0 +1,10 @@\n+<template>\n+  <div class="card">\n+    <slot></slot>\n+  </div>\n+</template>\n+\n+<style scoped>\n+.card { border: 1px solid #ccc; }\n+</style>',
      status: 'pending',
    },
    {
      type: 'terminal',
      command: 'npm run lint',
      output: 'Linter running...\nNo errors found.',
      status: 'success',
    },
    {
      type: 'text',
      content: 'I have created the `Card.vue` component and verified it with the linter. Would you like to apply the changes?',
    }
  ]
};
