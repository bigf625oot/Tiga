<template>
  <div class="h-full flex-1 flex flex-col min-h-0 relative min-w-0">
    <!-- Empty State -->
    <div v-if="messages.length === 0" key="empty-state" class="flex-1 flex flex-col items-center justify-start pt-[15vh] px-4 overflow-y-auto relative custom-scrollbar">
      <div class="w-full max-w-2xl flex flex-col items-center gap-6">
        <div class="flex flex-col items-center gap-4 transition-all duration-500 ease-in-out" 
             :class="inputValue ? 'opacity-40 scale-90 translate-y-4' : 'opacity-100'">
          <TechAnimation :width="200" :height="200" class="mb-4" />
          <h1 v-if="!embedded" class="text-3xl font-bold tracking-tight text-foreground text-center">
            让我们创造点厉害的东西！
          </h1>
          <h1 v-else class="text-xl font-semibold text-foreground text-center">有什么可以帮您？</h1>
        </div>

        <!-- Mode Selection -->
        <div class="w-full px-1 transition-all duration-500 ease-in-out"
             :class="inputValue ? 'max-h-0 opacity-0 pb-0 -translate-y-4 scale-95 overflow-hidden' : 'max-h-[500px] opacity-100 pt-1 pb-6 overflow-visible'">
          <SmartQAIntroFlipCards :mode-entrance="modeEntrance" @select="handleSelectEntrance" />

          <div v-if="modeEntrance === 'manual'" class="grid w-full grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            <div v-for="m in modes" :key="m.id"
              class="relative flex flex-col items-start justify-between p-3 rounded-xl border transition-all duration-300 cursor-pointer group h-[90px] overflow-hidden"
              :class="[
                (currentModeId || 'quick') === m.id
                  ? `${getTheme(m.themeColor).activeBorder} ${getTheme(m.themeColor).activeBg} shadow-md ring-1 ${getTheme(m.themeColor).activeRing}`
                  : `border-transparent bg-white/60 dark:bg-card/40 backdrop-blur-md shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05)] hover:shadow-xl hover:-translate-y-1 ${getTheme(m.themeColor).hoverBorder} ${getTheme(m.themeColor).hoverShadow}`
              ]"
              @click="$emit('select-mode', m)"
            >
              <div class="absolute -right-8 -top-8 w-32 h-32 rounded-full blur-3xl opacity-20 pointer-events-none transition-colors duration-500"
                   :class="(currentModeId || 'quick') === m.id ? `bg-${m.themeColor || 'blue'}-500 dark:bg-${m.themeColor || 'blue'}-400` : 'bg-gray-300 dark:bg-gray-700'"></div>

              <div v-if="(currentModeId || 'quick') === m.id" 
                class="absolute top-3 right-3 rounded-full p-0.5 animate-in fade-in zoom-in duration-200"
                :class="getTheme(m.themeColor).checkBg">
                <Check class="w-3 h-3 text-white dark:text-slate-950" stroke-width="3" />
              </div>

              <Badge
                v-if="m.badge"
                variant="secondary"
                class="absolute top-3 left-3 h-5 px-2 text-[10px] font-bold bg-blue-500/10 text-blue-600 border-blue-500/20 dark:bg-blue-500/10 dark:text-blue-300 dark:border-blue-500/30"
              >
                {{ m.badge }}
              </Badge>

              <div class="flex flex-col w-full z-10 gap-1 mt-auto">
                <span class="text-sm font-bold tracking-wide transition-colors duration-300"
                  :class="(currentModeId || 'quick') === m.id ? getTheme(m.themeColor).titleText : 'text-gray-900 dark:text-gray-100'">
                  {{ m.name }}
                </span>
                <span class="text-xs text-muted-foreground leading-relaxed line-clamp-2 opacity-90">
                  {{ m.description }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Input Area (Centered) -->
        <SmartQAInput
          large
          v-bind="$props"
          v-model="inputValue"
          :quoted-message="quotedMessage"
          @update:is-network-search-enabled="$emit('update:isNetworkSearchEnabled', $event)"
          @update:selectedAgentId="$emit('update:selectedAgentId', $event)"
          @send="handleSend"
          @stop="$emit('stop')"
          @open-attachment="$emit('open-attachment')"
          @remove-attachment="$emit('remove-attachment', $event)"
          @add-attachment="$emit('add-attachment', $event)"
          @clear-quote="quotedMessage = null"
        />

        <!-- User Scripts -->
        <div v-if="userScripts.length > 0" class="flex flex-col gap-4 w-full animate-fade-in-up">
          <div class="flex items-center justify-between px-1">
            <span class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">快捷指令</span>
          </div>
          
          <!-- Recent Used / Horizontal Scroll -->
          <ScrollArea class="w-full whitespace-nowrap pb-2">
            <div class="flex w-max space-x-3 p-1">
              <div v-for="s in userScripts" :key="s.id"
                class="group relative flex items-center gap-3 p-3 pr-4 rounded-xl border border-border/40 bg-card/40 backdrop-blur-md hover:bg-accent/50 hover:shadow-md hover:border-primary/50 transition-all duration-300 cursor-pointer min-w-[180px] max-w-[240px]"
                @click="$emit('send-script', s.content)"
              >
                <!-- Icon Placeholder based on content type (mock logic) -->
                <div class="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/10 group-hover:scale-110 transition-transform duration-300">
                  <Zap class="w-4 h-4 text-primary/70 group-hover:text-primary" />
                </div>
                
                <div class="flex flex-col gap-0.5 overflow-hidden">
                  <span class="text-xs font-medium text-foreground truncate group-hover:text-primary transition-colors">{{ s.title }}</span>
                  <span class="text-[10px] text-muted-foreground truncate opacity-70 group-hover:opacity-100">{{ s.content }}</span>
                </div>
                
                <!-- Hover Arrow -->
                <div class="absolute right-2 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">
                  <ArrowRight class="w-3 h-3 text-primary/50" />
                </div>
              </div>
            </div>
            <ScrollBar orientation="horizontal" />
          </ScrollArea>
        </div>
      </div>
    </div>

      <!-- Message List State -->
    <template v-else>
      <div key="message-list-state" class="flex-1 relative min-h-0 min-w-0 flex flex-col w-full h-full overflow-hidden">
        <div class="flex-1 min-h-0 min-w-0 w-full relative">
          <MessageList
            ref="messagesContainer"
            :messages="messages"
            :current-agent="currentAgent"
            :is-loading="isLoading"
            :is-streaming="isStreaming"
            :loading-status="loadingStatus"
            :current-mode-id="currentModeId"
            @locate-node="$emit('locate-node', $event)"
            @open-doc-space="$emit('open-doc-space', $event)"
            @quote-message="handleQuoteMessage"
            @excerpt-message="handleExcerptMessage"
            @delete-message="$emit('delete-message', $event)"
            @resend-message="$emit('resend-message', $event)"
            @edit-message="$emit('edit-message', $event)"
          />
        </div>

        <!-- Sticky Input Area positioned at bottom overlaying the list -->
        <!-- Use z-30 to ensure input area is above message list -->
        <div class="flex-none w-full px-4 pt-4 pb-6 z-30 bg-background shrink-0 relative  dark:shadow-[0_-10px_20px_-5px_rgba(0,0,0,0.2)]">
          <div class="max-w-4xl mx-auto relative group/footer">
           <!-- Mode Toggle Trigger (Visible on hover or if no modes shown) -->
           <div v-if="!isModeBarVisible" class="absolute -top-8 left-0 w-full flex justify-center opacity-0 group-hover/footer:opacity-100 transition-opacity duration-300 pointer-events-none group-hover/footer:pointer-events-auto">
               <Button variant="secondary" size="sm" class="h-6 text-[10px] px-2 shadow-sm bg-background/80 backdrop-blur border border-border/50" @click="isModeBarVisible = true">
                   切换模式
               </Button>
           </div>

           <!-- Compact Mode Selection -->
           <div v-if="isModeBarVisible" class="pb-4 animate-in slide-in-from-bottom-2 fade-in duration-200">
              <div class="flex justify-between items-center mb-2 px-1">
                  <span class="text-xs font-medium text-muted-foreground">切换模式</span>
                  <Button variant="ghost" size="icon" class="h-5 w-5 hover:bg-muted/80 rounded-full" @click="isModeBarVisible = false"><X class="w-3 h-3 text-muted-foreground" /></Button>
              </div>
              <div class="grid w-full grid-cols-5 gap-2">
                 <div v-for="m in modes" :key="m.id" 
                    class="relative flex flex-row items-center p-1.5 rounded-lg border bg-background/50 hover:bg-muted/50 transition-all cursor-pointer group h-[46px] gap-2"
                    :class="[
                      (currentModeId || 'quick') === m.id
                        ? `${getTheme(m.themeColor).activeBorder} ${getTheme(m.themeColor).activeBg} ring-1 ${getTheme(m.themeColor).activeRing}`
                        : 'border-border/50'
                    ]"
                    @click="$emit('select-mode', m)">
                    <div class="p-1 rounded-full shrink-0 transition-colors"
                        :class="(currentModeId || 'quick') === m.id ? `${getTheme(m.themeColor).iconBg} ${getTheme(m.themeColor).iconText}` : 'bg-muted text-muted-foreground group-hover:text-foreground group-hover:bg-muted/80'">
                        <component :is="m.icon" class="w-3.5 h-3.5" />
                    </div>
                    <div class="flex flex-col min-w-0 text-left gap-0.5">
                        <div class="flex items-center gap-1 min-w-0">
                          <span
                            class="text-[11px] font-semibold leading-none truncate"
                            :class="(currentModeId || 'quick') === m.id ? getTheme(m.themeColor).titleText : 'text-foreground'"
                          >
                            {{ m.name }}
                          </span>
                          <Badge
                            v-if="m.badge"
                            variant="secondary"
                            class="h-4 px-1.5 text-[9px] font-bold bg-blue-500/10 text-blue-600 border-blue-500/20 dark:bg-blue-500/10 dark:text-blue-300 dark:border-blue-500/30 shrink-0"
                          >
                            {{ m.badge }}
                          </Badge>
                        </div>
                        <span class="text-[9px] text-muted-foreground truncate leading-none opacity-80">{{ m.description }}</span>
                    </div>
                 </div>
              </div>
           </div>

           <SmartQAInput
              v-bind="$props"
              v-model="inputValue"
              :quoted-message="quotedMessage"
              @update:is-network-search-enabled="$emit('update:isNetworkSearchEnabled', $event)"
              @update:selectedAgentId="$emit('update:selectedAgentId', $event)"
              @send="handleSend"
              @stop="$emit('stop')"
              @open-attachment="$emit('open-attachment')"
              @remove-attachment="handleRemoveAttachment"
              @add-attachment="$emit('add-attachment', $event)"
              @clear-quote="quotedMessage = null"
            />
        </div>
      </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { Check, X, Zap, ArrowRight } from 'lucide-vue-next';
import TechAnimation from '../../TechAnimation.vue';
import MessageList from '../../MessageList.vue';
import SmartQAInput from '../chat/SmartQAInput.vue';
import SmartQAIntroFlipCards from '../chat/SmartQAIntroFlipCards.vue';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { getTheme } from '../../../constants/theme';
import type { Agent, Message, Attachment, UserScript, ModeConfig, Team } from '../../../types';

const props = defineProps<{
  messages: Message[];
  modes: ModeConfig[];
  currentModeId: string | null;
  embedded: boolean;
  isLoading: boolean;
  isStreaming: boolean;
  loadingStatus?: string;
  isTaskRunning: boolean;
  isStopping: boolean;
  modelValue: string; // Input value
  selectedAttachments: Attachment[];
  currentAgent: Agent | Team | undefined;
  selectedAgentId: string;
  agentList: (Agent | Team)[];
  userScripts: UserScript[];
  isNetworkSearchEnabled: boolean;
}>();

const emit = defineEmits([
  'update:modelValue',
  'update:selectedAgentId',
  'update:isNetworkSearchEnabled',
  'send',
  'stop',
  'select-mode',
  'send-script',
  'locate-node',
  'open-doc-space',
  'open-attachment',
  'remove-attachment',
  'add-attachment',
  'excerpt-message',
  'delete-message',
  'resend-message',
  'edit-message'
]);

const handleQuoteMessage = (content: string) => {
    quotedMessage.value = content;
};

const handleExcerptMessage = (content: string) => {
    emit('excerpt-message', content);
};

const handleSend = () => {
    if (quotedMessage.value) {
        // Prepend quote to message
        const formattedQuote = quotedMessage.value.split('\n').map(line => `> ${line}`).join('\n') + '\n\n';
        emit('update:modelValue', formattedQuote + inputValue.value);
        // Clear quote after formatting (or wait for send success? Assume immediate send)
        quotedMessage.value = null;
    }
    emit('send');
};

const handleRemoveAttachment = (attachmentOrIndex: number | Attachment) => {
    emit('remove-attachment', attachmentOrIndex);
};

const inputValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

const isModeBarVisible = ref(false);
const quotedMessage = ref<string | null>(null);
const modeEntrance = ref<'auto' | 'manual'>(props.currentModeId ? 'manual' : 'auto');

// 监听 currentModeId 变化，同步 modeEntrance 状态
// 当有具体模式 ID 时，自动切换到 manual 模式展示列表
// 当 ID 为空时，切换到 auto 模式
const unwatchMode = watch(() => props.currentModeId, (newVal) => {
  modeEntrance.value = newVal ? 'manual' : 'auto';
});

const handleSelectEntrance = (next: 'auto' | 'manual') => {
  if (next === 'auto') {
    // 秒懂模式：不预设具体模式，由意图识别决定
    modeEntrance.value = 'auto'; // 保持为 auto，隐藏下方模式列表
    emit('select-mode', { id: null, value: 'auto' } as any); // 清空当前模式
    emit('update:selectedAgentId', ''); // 清空选中的智能体，交由大模型意图识别
  } else {
    modeEntrance.value = next;
    // 切换到手动（极客）模式时，如果当前没有具体模式，默认选中 quick 模式
    if (!props.currentModeId) {
      const quickMode = props.modes.find(m => m.id === 'quick') || props.modes[0];
      if (quickMode) {
        emit('select-mode', quickMode);
      }
    }
  }
};

</script>
