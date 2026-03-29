<template>
  <SmartQA :session-id="sessionId" :embedded="false" />
</template>

<script setup lang="ts">
import SmartQA from '@/features/llm-chat/shared/components/SmartQA.vue';
import { useTeamModeStore } from '@/features/llm-chat/team/store';

const { sessionId } = useTeamModeStore();
</script>
