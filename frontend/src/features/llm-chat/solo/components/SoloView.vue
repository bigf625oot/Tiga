<template>
  <SmartQA :session-id="sessionId" :embedded="false" />
</template>

<script setup lang="ts">
import SmartQA from '@/features/llm-chat/shared/components/SmartQA.vue';
import { useSoloModeStore } from '@/features/llm-chat/solo/store';

const { sessionId } = useSoloModeStore();
</script>
