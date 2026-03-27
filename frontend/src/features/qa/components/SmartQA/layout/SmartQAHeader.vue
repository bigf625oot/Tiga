<template>
  <div class="flex-none px-4 py-3 border-b bg-background/80 backdrop-blur-md z-30 flex justify-between items-center supports-[backdrop-filter]:bg-background/60">
    <div class="flex items-center gap-4 min-w-0" v-if="!isLeftCollapsed">
      <div class="relative w-9 h-9 flex items-center justify-center shrink-0">
        <div class="absolute inset-0 rounded-full border-2 border-muted"></div>
        <svg class="absolute inset-0 w-full h-full -rotate-90 transform" viewBox="0 0 36 36">
          <circle cx="18" cy="18" r="16" fill="none" class="stroke-primary transition-all duration-500 ease-in-out" stroke-width="2" stroke-dasharray="100" :stroke-dashoffset="100 - (progress || 0)" />
        </svg>
        <Avatar class="absolute inset-0 m-auto w-full h-full rounded-full">
          <AvatarImage v-if="agentIcon" :src="agentIcon" class="object-cover bg-white" alt="Agent" />
          <AvatarFallback class="bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white">
            <BaseIcon icon="mdi:file-document-outline" :size="14" />
          </AvatarFallback>
        </Avatar>
      </div>

      <div class="min-w-0 flex items-center gap-3">
        <div v-if="!isEditing" class="flex items-center gap-2 group cursor-pointer" @click="startEditing">
          <h2 class="font-semibold text-sm leading-tight truncate text-foreground max-w-[200px]">
            {{ currentSession?.title || '新任务' }}
          </h2>
          <Edit2 class="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
        <div v-else class="flex items-center gap-1">
          <Input 
            ref="titleInputRef"
            v-model="editTitle" 
            class="h-7 w-[200px] text-sm px-2 py-1" 
            @keydown.enter="saveTitle"
            @keydown.esc="cancelEditing"
            @blur="saveTitle"
            autofocus
          />
        </div>

        <div class="h-4 w-px bg-border/60"></div>

        <div class="flex items-center gap-2 text-xs text-muted-foreground truncate">
          <span class="flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 rounded-full bg-primary/70"></span>
            {{ currentModeName }}
            <Badge
              v-if="currentModeBadge"
              variant="secondary"
              class="h-4 px-1.5 text-[9px] font-bold bg-blue-500/10 text-blue-600 border-blue-500/20 dark:bg-blue-500/10 dark:text-blue-300 dark:border-blue-500/30"
            >
              {{ currentModeBadge }}
            </Badge>
          </span>
          <span class="text-muted-foreground/30">|</span>
          <span>{{ sessionTime }}</span>
        </div>
      </div>
    </div>

    <div class="flex items-center gap-1 shrink-0" v-if="showControls">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger as-child>
            <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground hover:text-amber-500" @click="$emit('open-memo')">
              <Bookmark class="w-4 h-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>秒记列表</TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <TooltipProvider v-if="currentModeId && currentModeId !== 'quick'">
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
import { ref, computed, watch, nextTick } from 'vue';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';
import BaseIcon from '@/shared/components/atoms/BaseIcon';
import type { Agent, Session, Team } from '../../../types';
import dayjs from 'dayjs';
import { MODES } from '../../../constants';
import { Edit2, Check, X, Bookmark } from 'lucide-vue-next';

const props = defineProps<{
  isLeftCollapsed: boolean;
  isRightCollapsed: boolean;
  progress: number;
  currentSession: Session | null;
  currentAgent: Agent | Team | undefined;
  currentModeId: string | null;
  showControls?: boolean;
}>();

const emit = defineEmits(['toggle-left', 'toggle-right', 'open-logs', 'update-title', 'open-memo']);

const isEditing = ref(false);
const editTitle = ref('');
const titleInputRef = ref<HTMLInputElement | null>(null);

const startEditing = () => {
  if (!props.currentSession) return;
  editTitle.value = props.currentSession.title || '新任务';
  isEditing.value = true;
  nextTick(() => {
    titleInputRef.value?.focus();
  });
};

const cancelEditing = () => {
  isEditing.value = false;
};

const saveTitle = () => {
  const newTitle = editTitle.value.trim();
  if (newTitle && props.currentSession && newTitle !== props.currentSession.title) {
      emit('update-title', { id: props.currentSession.id, title: newTitle });
  }
  isEditing.value = false;
};

const agentIcon = computed(() => {
  if (!props.currentAgent) return undefined;
  // Check if it's an Agent (has icon property, though optional)
  // Since Team doesn't have icon property defined in interface, we can check for existence or just use type guard
  const agent = props.currentAgent as Agent;
  return agent.icon || agent.icon_url;
});

const currentMode = computed(() => {
  if (!props.currentModeId) return undefined;
  return MODES.find(m => m.id === props.currentModeId);
});

const currentModeName = computed(() => {
  if (!props.currentModeId) return '快问快答';
  return currentMode.value ? currentMode.value.name : '未知模式';
});

const currentModeBadge = computed(() => currentMode.value?.badge);

const sessionTime = computed(() => {
  if (!props.currentSession?.created_at) return dayjs().format('YYYY-MM-DD HH:mm');
  return dayjs(props.currentSession.created_at).format('YYYY-MM-DD HH:mm');
});
</script>
