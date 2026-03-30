<template>
  <DynamicGridBackground class="h-full overflow-hidden relative bg-background" background-color="transparent"
    :grid-size="30" :grid-color="isDark ? '#333' : '#e5e7eb'" :blob-count="3" :blob-colors="blobColors"
    :animation-speed="20" :show-grid="!useTaskUI">
    
    <component 
      :is="resolvedComponent" 
      :session-id="sessionId" 
      :embedded="embedded" 
      :initial-mode-id="currentModeId"
      @refresh-sessions="$emit('refresh-sessions')" 
      @update:sessionId="$emit('update:sessionId', $event)" 
    />

  </DynamicGridBackground>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useTheme } from '@/composables/useTheme';
import { chatService } from '@/features/llm-chat/services/chatService';
import DynamicGridBackground from '@/shared/components/molecules/DynamicGridBackground.vue';
import QuickQA from '@/features/llm-chat/quick/components/QuickQA.vue';
import WorkflowQA from '@/features/llm-chat/workflow/components/WorkflowQA.vue';
import { MODES } from '@/features/llm-chat/shared/constants';

// Fallbacks for now, point to WorkflowQA since they share TaskUI layout

const props = defineProps<{
  sessionId: string | null;
  embedded: boolean;
  initialMode?: string;
}>();

defineEmits(['refresh-sessions', 'update:sessionId']);

const { isLightMode } = useTheme();
const isDark = computed(() => !isLightMode.value);
const blobColors = computed(() => isDark.value
  ? ['rgba(99, 102, 241, 0.15)', 'rgba(59, 130, 246, 0.15)', 'rgba(168, 85, 247, 0.15)']
  : ['rgba(99, 102, 241, 0.12)', 'rgba(59, 130, 246, 0.12)', 'rgba(168, 85, 247, 0.12)']);

const currentMode = ref(props.initialMode || 'quick');
const useTaskUI = computed(() => currentMode.value !== 'quick');

const currentModeId = computed(() => {
    const config = MODES.find(m => m.value === currentMode.value);
    return config ? config.id : 'quick';
});

const resolvedComponent = computed(() => {
    switch (currentMode.value) {
        case 'workflow':
        case 'auto_task':
        case 'solo':
        case 'plan':
        case 'team':
            return WorkflowQA;
        default:
            return QuickQA;
    }
});

const loadMode = async (sid: string | null) => {
    if (!sid) {
        currentMode.value = props.initialMode || 'quick';
        return;
    }
    try {
        const session = await chatService.getSession(sid);
        if (session && session.mode) {
            currentMode.value = session.mode;
        } else {
            currentMode.value = props.initialMode || 'quick';
        }
    } catch (e) {
        currentMode.value = props.initialMode || 'quick';
    }
};

onMounted(() => {
    loadMode(props.sessionId);
});

watch(() => props.sessionId, (newId) => {
    loadMode(newId);
});
</script>
