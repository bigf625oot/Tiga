<template>
  <SmartQA :session-id="sessionId" :embedded="false" />
</template>

<script setup lang="ts">
import SmartQA from '@/features/llm-chat/shared/components/SmartQA.vue';
import { useChatModeStore } from '@/features/llm-chat/shared/composables/useChatModeStore';
import type { LlmChatMode } from '@/features/llm-chat/store/llmChatSlice';

const props = defineProps<{
  mode: LlmChatMode;
}>();

const { sessionId } = useChatModeStore(props.mode);
</script>
