<template>
  <div class="w-full relative flex flex-col bg-background/80 backdrop-blur-xl rounded-2xl border border-border/50 shadow-lg focus-within:ring-1 focus-within:ring-primary/20 focus-within:border-primary/50 transition-all duration-300">
    <!-- Attachments Preview -->
    <div v-if="selectedAttachments.length > 0" class="flex flex-wrap gap-2 px-3 pt-3">
      <Badge v-for="(att, idx) in selectedAttachments" :key="idx" variant="secondary" class="flex items-center gap-1 px-2 py-1 bg-muted/50 border-border/50">
        <Paperclip class="w-3 h-3" />
        <span class="max-w-[100px] truncate">{{ att.name }}</span>
        <Trash2 class="w-3 h-3 cursor-pointer hover:text-destructive ml-1" @click="$emit('remove-attachment', idx)" />
      </Badge>
    </div>

    <!-- Textarea -->
    <textarea
      ref="textareaRef"
      v-model="inputValue"
      @keydown.enter.prevent="handleEnter"
      rows="1"
      :placeholder="currentPlaceholder"
      :class="[
        'w-full p-4 resize-y outline-none text-sm bg-transparent max-h-[60vh] custom-scrollbar placeholder:text-muted-foreground/70 transition-all',
        large ? 'min-h-[128px]' : 'min-h-[56px]'
      ]"
      :disabled="isLoading"
      @input="adjustHeight"
    ></textarea>

    <!-- Bottom Toolbar -->
    <div class="flex justify-between items-center px-2 pb-2">
      <div class="flex items-center gap-1">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger as-child>
              <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground hover:bg-muted rounded-lg" @click="$emit('open-attachment')">
                <Paperclip class="w-4 h-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>添加附件</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <div class="flex items-center gap-2">
        <!-- Agent Selector -->
        <div class="flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer">
          <Avatar class="w-5 h-5">
            <AvatarImage v-if="agentIcon" :src="agentIcon" class="object-cover bg-white" />
            <AvatarFallback class="bg-gradient-to-br from-blue-500/10 to-indigo-500/10 flex items-center justify-center">
              <Zap class="w-3.5 h-3.5 text-blue-500" />
            </AvatarFallback>
          </Avatar>
          <Select 
            :model-value="selectedAgentId" 
            @update:model-value="$emit('update:selectedAgentId', $event)"
            :disabled="!currentModeId || currentModeId === 'quick'"
          >
            <SelectTrigger :class="`w-auto min-w-[60px] max-w-[120px] h-6 !border-0 !bg-transparent p-0 text-xs focus:ring-0 shadow-none gap-1 ${(!currentModeId || currentModeId === 'quick') ? '[&>svg]:hidden' : ''}`">
               <span class="truncate">{{ (!currentModeId || currentModeId === 'quick') ? '快问快答' : (currentAgent?.name || (currentModeId === 'team' ? '选择团队' : '选择智能体')) }}</span>
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="item in agentList" :key="item.id" :value="item.id">
                <div v-if="currentModeId === 'team'" class="flex flex-col items-start gap-1 py-1 w-[240px]">
                  <div class="font-medium">{{ item.name }}</div>
                  <div class="text-xs text-muted-foreground line-clamp-2 text-left whitespace-normal opacity-80">
                    {{ item.description || '暂无描述' }}
                  </div>
                </div>
                <span v-else>{{ item.name }}</span>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <template v-if="(!currentModeId || currentModeId === 'quick' || currentModeId === 'solo') && !embedded">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger as-child>
                <div 
                  class="flex items-center gap-1.5 px-3 py-1.5 h-8 rounded-full cursor-pointer transition-all duration-300 border select-none"
                  :class="isNetworkSearchEnabled 
                    ? 'bg-blue-50 text-blue-600 border-blue-100 shadow-sm' 
                    : 'bg-muted/30 text-muted-foreground border-transparent hover:bg-muted/50'"
                  @click="toggleNetworkSearch"
                >
                  <Globe class="w-3.5 h-3.5" :class="{'animate-pulse': isNetworkSearchEnabled}" />
                  <span class="text-xs font-medium">联网</span>
                  <div class="w-1.5 h-1.5 rounded-full transition-colors" 
                       :class="isNetworkSearchEnabled ? 'bg-blue-500' : 'bg-muted-foreground/30'"></div>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>{{ isNetworkSearchEnabled ? '已开启联网搜索' : '开启联网搜索' }}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </template>

        <Button 
          @click="handleSend" 
          size="icon" 
          class="h-8 w-8 rounded-full shadow-sm transition-all active:scale-95 relative overflow-hidden" 
          :variant="(inputValue.trim() || isTaskRunning) ? 'default' : 'secondary'" 
          :disabled="(!inputValue.trim() && !isTaskRunning) || isStopping"
        >
          <span v-if="isRippleActive" class="absolute inset-0 rounded-full bg-white/30 animate-ripple pointer-events-none"></span>
          <Loader2 v-if="isStopping" class="w-4 h-4 animate-spin relative z-10" />
          <Square v-else-if="isTaskRunning" class="w-3 h-3 fill-current relative z-10" />
          <ArrowUp v-else class="w-4 h-4 relative z-10" />
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Switch } from '@/components/ui/switch';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Paperclip, Trash2, Globe, Zap, Loader2, Square, ArrowUp } from 'lucide-vue-next';
import type { Agent, Attachment, Team } from '../../types';

const props = defineProps<{
  modelValue: string;
  isLoading: boolean;
  isTaskRunning: boolean;
  isStopping: boolean;
  selectedAttachments: Attachment[];
  currentAgent: Agent | Team | undefined;
  selectedAgentId: string;
  agentList: (Agent | Team)[]; // or Team[]
  currentModeId: string | null;
  embedded: boolean;
  isNetworkSearchEnabled: boolean;
  large?: boolean;
}>();

const emit = defineEmits([
  'update:modelValue',
  'update:selectedAgentId',
  'update:isNetworkSearchEnabled',
  'send',
  'stop',
  'open-attachment',
  'remove-attachment'
]);

const agentIcon = computed(() => {
  if (!props.currentAgent) return undefined;
  const agent = props.currentAgent as Agent;
  return agent.icon || agent.icon_url;
});

const inputValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

const textareaRef = ref<HTMLTextAreaElement | null>(null);

const adjustHeight = () => {
  const el = textareaRef.value;
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = Math.max(el.scrollHeight, 36) + 'px';
};

watch(() => props.modelValue, () => {
  nextTick(() => adjustHeight());
});

const handleEnter = (e: KeyboardEvent) => {
  if (e.shiftKey) return;
  handleSend();
};

const isRippleActive = ref(false);

const handleSend = () => {
  if (!props.isTaskRunning) {
    isRippleActive.value = true;
    setTimeout(() => {
      isRippleActive.value = false;
    }, 600);
  }

  if (props.isTaskRunning) {
    emit('stop');
  } else {
    emit('send');
  }
};

const toggleNetworkSearch = () => {
  emit('update:isNetworkSearchEnabled', !props.isNetworkSearchEnabled);
};

// Dynamic Placeholder Logic
const placeholders = [
  "描述您的需求...",
  "帮我写一段 Python 代码...",
  "分析这篇文档的关键点...",
  "解释一下量子纠缠...",
  "生成一份周报模板...",
  "如何优化 React 性能..."
];
const currentPlaceholder = ref(placeholders[0]);
let placeholderInterval: any;

onMounted(() => {
  let index = 0;
  placeholderInterval = setInterval(() => {
    index = (index + 1) % placeholders.length;
    currentPlaceholder.value = placeholders[index];
  }, 3000);
});

onUnmounted(() => {
  if (placeholderInterval) clearInterval(placeholderInterval);
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
    height: 6px;
    width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background: transparent;
    border-radius: 10px;
}
.custom-scrollbar:hover::-webkit-scrollbar-thumb {
    background: hsl(var(--muted));
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: hsl(var(--muted-foreground));
}

@keyframes ripple {
  0% {
    transform: scale(0);
    opacity: 0.5;
  }
  100% {
    transform: scale(2.5);
    opacity: 0;
  }
}

.animate-ripple {
  animation: ripple 0.6s linear;
}
</style>
