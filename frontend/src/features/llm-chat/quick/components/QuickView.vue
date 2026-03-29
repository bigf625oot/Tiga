<template>
  <SmartQA :session-id="sessionId" :embedded="false" />
</template>

<script setup lang="ts">
import SmartQA from '@/features/llm-chat/shared/components/SmartQA.vue';
import { useQuickModeStore } from '@/features/llm-chat/quick/store';

const { sessionId } = useQuickModeStore();
</script>
