<template>
  <SmartQA :session-id="sessionId" :embedded="false" />
</template>

<script setup lang="ts">
import SmartQA from '@/features/llm-chat/shared/components/SmartQA.vue';
import { useWorkflowModeStore } from '@/features/llm-chat/workflow/store';

const { sessionId } = useWorkflowModeStore();
</script>
