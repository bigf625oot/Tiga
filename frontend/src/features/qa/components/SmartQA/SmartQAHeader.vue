<template>
  <div class="flex-none px-4 py-3 border-b bg-background/80 backdrop-blur-md z-30 flex justify-between items-center supports-[backdrop-filter]:bg-background/60">
    <div class="flex items-center gap-4 min-w-0" v-if="!isLeftCollapsed">
      <div class="relative w-9 h-9 flex items-center justify-center shrink-0">
        <div class="absolute inset-0 rounded-full border-2 border-muted"></div>
        <svg class="absolute inset-0 w-full h-full -rotate-90 transform" viewBox="0 0 36 36">
          <circle cx="18" cy="18" r="16" fill="none" class="stroke-primary transition-all duration-500 ease-in-out" stroke-width="2" stroke-dasharray="100" :stroke-dashoffset="100 - (progress || 0)" />
        </svg>
        <Avatar class="absolute inset-0 m-auto w-6 h-6 shadow-sm">
          <AvatarImage v-if="agentIcon" :src="agentIcon" class="object-cover bg-white" alt="Agent" />
          <AvatarFallback class="bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white">
            <BaseIcon icon="mdi:file-document-outline" :size="14" />
          </AvatarFallback>
        </Avatar>
      </div>

      <div class="min-w-0">
        <h2 class="font-semibold text-sm leading-tight truncate text-foreground">
          {{ currentSession?.title || '新任务' }}
        </h2>
        <div class="flex items-center gap-1 text-xs text-muted-foreground truncate" v-if="currentAgent">
          <span>{{ currentModeId === 'team' ? '当前团队:' : '当前智能体:' }}</span>
          <span class="font-medium text-primary truncate">{{ currentAgent.name }}</span>
        </div>
      </div>
    </div>

    <div class="flex items-center gap-1 shrink-0" v-if="showControls">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger as-child>
            <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground" @click="$emit('open-logs')">
              <BaseIcon icon="lucide:code" :size="16" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>查看系统日志</TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import BaseIcon from '@/shared/components/atoms/BaseIcon';
import type { Agent, Session, Team } from '../../types';

const props = defineProps<{
  isLeftCollapsed: boolean;
  isRightCollapsed: boolean;
  progress: number;
  currentSession: Session | null;
  currentAgent: Agent | Team | undefined;
  currentModeId: string | null;
  showControls?: boolean;
}>();

defineEmits(['toggle-left', 'toggle-right', 'open-logs']);

const agentIcon = computed(() => {
  if (!props.currentAgent) return undefined;
  // Check if it's an Agent (has icon property, though optional)
  // Since Team doesn't have icon property defined in interface, we can check for existence or just use type guard
  const agent = props.currentAgent as Agent;
  return agent.icon || agent.icon_url;
});
</script>
