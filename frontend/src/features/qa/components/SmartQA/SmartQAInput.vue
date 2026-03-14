<template>
  <div 
    class="w-full relative flex flex-col bg-background/80 backdrop-blur-xl rounded-2xl border border-[#d4d4d4] shadow-lg focus-within:ring-1 focus-within:ring-primary/20 focus-within:border-neutral-400 dark:border-border/60 dark:focus-within:border-border transition-all duration-300"
    :class="[
      isDragging ? 'border-neutral-400 ring-2 ring-primary/20 bg-muted/50' : ''
    ]"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="handleDrop"
  >
    <!-- Attachments Preview -->
    <div v-if="selectedAttachments.length > 0" class="flex flex-wrap gap-2 px-3 pt-3">
      <Badge 
        v-for="(att, idx) in selectedAttachments" 
        :key="idx" 
        variant="secondary" 
        class="flex items-center gap-1.5 px-2 py-1 bg-muted/50 border-border/50 group/att"
        :class="{'border-red-200 bg-red-50 text-red-600': att.status === 'error', 'border-green-200 bg-green-50 text-green-600': att.status === 'success'}"
      >
        <!-- Icon based on status -->
        <Loader2 v-if="att.status === 'uploading' || att.status === 'parsing'" class="w-3 h-3 animate-spin text-muted-foreground" />
        <FileX v-else-if="att.status === 'error'" class="w-3 h-3" />
        <FileCheck v-else-if="att.status === 'success'" class="w-3 h-3" />
        <Paperclip v-else class="w-3 h-3 text-muted-foreground" />
        
        <!-- Name & Progress -->
        <div class="flex flex-col min-w-0 max-w-[140px]">
            <span class="truncate text-xs">{{ att.name }}</span>
            <Progress 
                v-if="att.status === 'uploading' || att.status === 'parsing'" 
                :model-value="att.progress || 0" 
                class="h-0.5 w-full mt-0.5 bg-muted-foreground/20" 
            />
        </div>

        <!-- Success Hover Card -->
        <div v-if="att.status === 'success'" class="inline-flex">
            <HoverCard :open-delay="200">
                <HoverCardTrigger as-child>
                    <div class="w-4 h-4 flex items-center justify-center cursor-help ml-0.5 hover:bg-green-200/50 rounded-full transition-colors">
                        <Info class="w-3 h-3 opacity-50 hover:opacity-100" />
                    </div>
                </HoverCardTrigger>
                <HoverCardContent align="start" class="w-72 p-3 z-[50]">
                    <div class="space-y-1.5">
                        <h4 class="text-xs font-semibold flex items-center gap-1.5 text-foreground">
                            <FileCheck class="w-3.5 h-3.5 text-green-500" />
                            文档解析完成
                        </h4>
                        <p class="text-[10px] text-muted-foreground leading-relaxed line-clamp-4">
                            {{ att.summary || '暂无摘要信息。' }}
                        </p>
                        <div class="flex items-center gap-2 pt-1.5 mt-1 border-t border-border/50">
                            <Badge variant="secondary" class="text-[9px] h-4 px-1">页数: {{ att.pageCount || '-' }}</Badge>
                            <Badge variant="secondary" class="text-[9px] h-4 px-1">字数: {{ att.wordCount || '-' }}</Badge>
                        </div>
                    </div>
                </HoverCardContent>
            </HoverCard>
        </div>

        <!-- Error Tooltip -->
        <TooltipProvider v-if="att.status === 'error'">
            <Tooltip>
                <TooltipTrigger>
                    <div class="w-4 h-4 flex items-center justify-center cursor-help ml-0.5 hover:bg-red-200/50 rounded-full transition-colors">
                        <Info class="w-3 h-3 opacity-50 hover:opacity-100" />
                    </div>
                </TooltipTrigger>
                <TooltipContent>{{ att.errorMessage || '解析失败' }}</TooltipContent>
            </Tooltip>
        </TooltipProvider>
        
        <div class="w-px h-3 bg-border/50 mx-0.5"></div>
        <Trash2 class="w-3 h-3 cursor-pointer hover:text-destructive opacity-50 hover:opacity-100 transition-opacity" @click="$emit('remove-attachment', att)" />
      </Badge>
    </div>

    <!-- Quote Preview -->
    <div v-if="quotedMessage" class="px-3 pt-3 flex items-center">
        <div class="flex items-start gap-2 bg-muted/40 border border-l-4 border-l-primary/50 border-y-0 border-r-0 pl-3 pr-2 py-2 rounded-sm w-full relative">
            <div class="flex-1 min-w-0">
                <p class="text-xs text-muted-foreground truncate font-medium">引用消息</p>
                <p class="text-xs text-foreground/80 line-clamp-2 mt-0.5">{{ quotedMessage }}</p>
            </div>
            <button class="text-muted-foreground hover:text-foreground transition-colors p-1" @click="$emit('clear-quote')">
                <X class="w-3.5 h-3.5" />
            </button>
        </div>
    </div>

    <!-- Textarea -->
    <textarea
      ref="textareaRef"
      v-model="inputValue"
      @keydown.enter="handleEnter"
      @paste="handlePaste"
      @keydown.esc="handleEsc"
      @focus="isFocused = true"
      @blur="isFocused = false"
      rows="1"
      :placeholder="currentPlaceholder"
      :class="[
        'w-full p-4 resize-none outline-none text-sm bg-transparent max-h-[60vh] overflow-y-auto custom-scrollbar placeholder:text-muted-foreground/70 transition-all',
        large ? 'min-h-[128px]' : 'min-h-[56px]'
      ]"
      :disabled="isLoading"
      @input="adjustHeight"
    ></textarea>

    <!-- Bottom Toolbar -->
    <div class="flex items-end justify-between gap-3 px-3 pb-3 pt-2">
      <div class="flex items-center gap-1.5 min-w-0">
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

        <template v-if="(!currentModeId || currentModeId === 'quick' || currentModeId === 'solo') && !embedded">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger as-child>
                <button
                  type="button"
                  class="inline-flex items-center gap-2 h-8 px-2 sm:px-3 rounded-full border transition-colors"
                  :class="isNetworkSearchEnabled ? 'border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100' : 'border-border/60 bg-muted/30 text-muted-foreground hover:bg-muted/40'"
                  @click="toggleNetworkSearch"
                >
                  <Globe class="w-4 h-4" />
                  <span class="hidden sm:inline text-xs font-medium">联网</span>
                  <span class="relative flex h-2 w-2 ml-0.5">
                    <span v-if="isNetworkSearchEnabled" class="absolute inline-flex h-full w-full rounded-full bg-blue-500 opacity-60 animate-ping"></span>
                    <span class="relative inline-flex h-2 w-2 rounded-full" :class="isNetworkSearchEnabled ? 'bg-blue-600' : 'bg-muted-foreground/40'"></span>
                  </span>
                </button>
              </TooltipTrigger>
              <TooltipContent>{{ isNetworkSearchEnabled ? '已开启联网搜索' : '开启联网搜索' }}</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </template>

        <div
          v-if="!currentModeId || currentModeId === 'quick'"
          class="inline-flex items-center gap-1.5 h-8 px-2 sm:px-3 rounded-full border text-xs font-medium select-none transition-colors"
          :class="(isLoading || isTaskRunning) ? 'border-blue-200 bg-blue-50 text-blue-700 shadow-[0_0_0_1px_rgba(59,130,246,0.12)] dark:border-blue-900/60 dark:bg-blue-950/30 dark:text-blue-200' : 'border-border/60 bg-muted/30 text-foreground/80'"
        >
          <Avatar class="w-4 h-4">
            <AvatarImage v-if="agentIcon" :src="agentIcon" class="object-cover bg-white" />
            <AvatarFallback class="bg-gradient-to-br from-blue-500/10 to-indigo-500/10 flex items-center justify-center">
              <Zap class="w-3 h-3 text-blue-600" />
            </AvatarFallback>
          </Avatar>
          <span class="hidden sm:inline">快问快答</span>
          <span v-if="isLoading || isTaskRunning" class="ml-0.5 inline-flex items-center gap-1.5">
            <Loader2 class="w-3.5 h-3.5 animate-spin text-blue-600 dark:text-blue-300" />
            <span class="relative flex h-2 w-2">
              <span class="absolute inline-flex h-full w-full rounded-full bg-blue-500 opacity-50 animate-ping"></span>
              <span class="relative inline-flex h-2 w-2 rounded-full bg-blue-600"></span>
            </span>
          </span>
        </div>
        <div v-else class="flex items-center gap-2 h-8 px-2 rounded-lg border border-border/50 bg-background/40 hover:bg-muted/40 transition-colors min-w-0">
          <Avatar class="w-5 h-5">
            <AvatarImage v-if="agentIcon" :src="agentIcon" class="object-cover bg-white" />
            <AvatarFallback class="bg-gradient-to-br from-blue-500/10 to-indigo-500/10 flex items-center justify-center">
              <Zap class="w-3.5 h-3.5 text-blue-500" />
            </AvatarFallback>
          </Avatar>
          <Select
            :model-value="selectedAgentId" 
            @update:model-value="$emit('update:selectedAgentId', $event)"
          >
            <SelectTrigger class="w-auto h-6 !border-0 !bg-transparent !p-0 text-xs focus:ring-0 shadow-none gap-1">
              <span class="truncate max-w-[160px]">
                {{ currentAgent?.name || (currentModeId === 'team' ? '选择团队' : '选择智能体') }}
              </span>
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

        <div class="hidden sm:flex items-center gap-2 text-[10px] text-muted-foreground ml-1 select-none">
          <span class="flex items-center gap-1">
            <kbd class="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
              Enter
            </kbd>
            <span>发送</span>
          </span>
          <span class="flex items-center gap-1">
            <kbd class="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
              Shift + Enter
            </kbd>
            <span>换行</span>
          </span>
        </div>
      </div>

      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger as-child>
            <div class="inline-block cursor-pointer">
              <Button 
                @click="handleSend" 
                size="icon" 
                variant="default"
                class="h-9 w-9 rounded-full shadow-sm transition-all active:scale-95 relative overflow-hidden"
                :class="(inputValue.trim() || isTaskRunning) ? 'bg-neutral-900 text-white hover:bg-neutral-800' : 'bg-neutral-200 text-neutral-500 hover:bg-neutral-200'" 
                :disabled="(!inputValue.trim() && !isTaskRunning) || isStopping"
              >
                <span v-if="isRippleActive" class="absolute inset-0 rounded-full bg-white/30 animate-ripple pointer-events-none"></span>
                <Loader2 v-if="isStopping" class="w-4 h-4 animate-spin relative z-10" />
                <Square v-else-if="isTaskRunning" class="w-3 h-3 fill-current relative z-10" />
                <ArrowUp v-else class="w-4 h-4 relative z-10" />
              </Button>
            </div>
          </TooltipTrigger>
          <TooltipContent side="top" align="end" :side-offset="10">
            <div class="flex flex-col gap-1 text-xs text-muted-foreground">
              <div class="flex items-center justify-between gap-4">
                <span>发送</span>
                <span class="font-mono bg-muted px-1 rounded text-[10px]">Enter</span>
              </div>
              <div class="flex items-center justify-between gap-4">
                <span>换行</span>
                <span class="font-mono bg-muted px-1 rounded text-[10px]">Shift + Enter</span>
              </div>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/components/ui/select';
import { Paperclip, Trash2, Globe, Zap, Loader2, Square, ArrowUp, FileCheck, FileX, Info, X } from 'lucide-vue-next';
import { useToast } from '@/components/ui/toast/use-toast';
import { Progress } from '@/components/ui/progress';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from '@/components/ui/hover-card';
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
  quotedMessage?: string | null;
}>();

const emit = defineEmits([
  'update:modelValue',
  'update:selectedAgentId',
  'update:isNetworkSearchEnabled',
  'send',
  'stop',
  'open-attachment',
  'remove-attachment',
  'add-attachment',
  'clear-quote'
]);

const { toast } = useToast();
const isDragging = ref(false);
const isFocused = ref(false);

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
  const minHeight = props.large ? 128 : 56;
  el.style.height = Math.max(el.scrollHeight, minHeight) + 'px';
};

watch(() => props.modelValue, () => {
  nextTick(() => adjustHeight());
});

const handleEnter = (e: KeyboardEvent) => {
  if (e.isComposing) return;
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
};

const handleEsc = (e: KeyboardEvent) => {
  if (props.isTaskRunning) {
    e.preventDefault();
    emit('stop');
  }
};

const handleDrop = (e: DragEvent) => {
  isDragging.value = false;
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    emit('add-attachment', Array.from(files));
    toast({
      title: "已添加附件",
      description: `成功添加 ${files.length} 个文件`,
    });
  }
};

const handlePaste = (e: ClipboardEvent) => {
  // 1. Files
  if (e.clipboardData?.files && e.clipboardData.files.length > 0) {
    e.preventDefault();
    emit('add-attachment', Array.from(e.clipboardData.files));
    toast({
      title: "已添加附件",
      description: `成功添加 ${e.clipboardData.files.length} 个文件`,
    });
    return;
  }

  // 2. Long text
  const text = e.clipboardData?.getData('text');
  if (text && text.length > 300) {
    e.preventDefault();
    const blob = new Blob([text], { type: 'text/plain' });
    const file = new File([blob], `paste-${Date.now()}.txt`, { type: 'text/plain' });
    emit('add-attachment', [file]);
    toast({
      title: "文本过长",
      description: "已自动转换为TXT附件",
    });
  }
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
  nextTick(() => adjustHeight());
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
