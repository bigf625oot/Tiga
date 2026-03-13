<template>
  <div class="flex-1 flex flex-col min-h-0 relative min-w-0 overflow-hidden">
    <!-- Empty State -->
    <div v-if="messages.length === 0" class="flex-1 flex flex-col items-center justify-start pt-[15vh] px-4 overflow-y-auto relative custom-scrollbar">
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
        <div class="w-full px-1 transition-all duration-500 ease-in-out overflow-hidden"
             :class="inputValue ? 'max-h-0 opacity-0 pb-0 -translate-y-4 scale-95' : 'max-h-[500px] opacity-100 pb-6'">
          <div class="grid w-full grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div v-for="m in modes" :key="m.id"
              class="relative flex flex-col items-start justify-between p-4 rounded-xl border transition-all duration-300 cursor-pointer group h-[120px] overflow-hidden"
              :class="[
                (currentModeId || 'quick') === m.id
                  ? `${getTheme(m.themeColor).activeBorder} ${getTheme(m.themeColor).activeBg} shadow-md ring-1 ${getTheme(m.themeColor).activeRing}`
                  : `border-transparent bg-white/60 backdrop-blur-md shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05)] hover:shadow-xl hover:-translate-y-1 ${getTheme(m.themeColor).hoverBorder} ${getTheme(m.themeColor).hoverShadow}`
              ]"
              @click="$emit('select-mode', m)"
            >
              <!-- Active State Check Icon -->
              <div v-if="(currentModeId || 'quick') === m.id" 
                class="absolute top-3 right-3 rounded-full p-0.5 animate-in fade-in zoom-in duration-200"
                :class="getTheme(m.themeColor).checkBg">
                <Check class="w-3 h-3 text-white" stroke-width="3" />
              </div>

              <!-- Icon -->
              <div v-if="(currentModeId || 'quick') === m.id" 
                class="p-2.5 rounded-lg mb-2 animate-in fade-in zoom-in duration-300"
                :class="`${getTheme(m.themeColor).iconBg} ${getTheme(m.themeColor).iconText}`">
                <component :is="m.icon" class="w-5 h-5" stroke-width="2" />
              </div>

              <!-- Content -->
              <div class="flex flex-col w-full z-10 gap-1 mt-auto">
                <span class="text-sm font-bold tracking-wide transition-colors duration-300"
                  :class="(currentModeId || 'quick') === m.id ? getTheme(m.themeColor).titleText : 'text-gray-900'">
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
          v-model="inputValue"
          :is-loading="isLoading"
          :is-task-running="isTaskRunning"
          :is-stopping="isStopping"
          :selected-attachments="selectedAttachments"
          :current-agent="currentAgent"
          :selected-agent-id="selectedAgentId"
          :agent-list="agentList"
          :current-mode-id="currentModeId"
          :embedded="embedded"
          :is-network-search-enabled="isNetworkSearchEnabled"
          @update:is-network-search-enabled="$emit('update:isNetworkSearchEnabled', $event)"
          @update:selectedAgentId="$emit('update:selectedAgentId', $event)"
          @send="$emit('send')"
          @stop="$emit('stop')"
          @open-attachment="$emit('open-attachment')"
          @remove-attachment="$emit('remove-attachment', $event)"
        />


        <!-- User Scripts -->
        <div v-if="userScripts.length > 0" class="flex flex-col gap-4 w-full animate-fade-in-up">
          <div class="flex items-center justify-between px-1">
            <span class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">快捷指令</span>
            <div class="flex gap-2">
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-100 cursor-pointer hover:bg-blue-100 transition-colors">全部</span>
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-muted/50 text-muted-foreground border border-transparent cursor-pointer hover:bg-muted hover:text-foreground transition-colors">生产力</span>
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-muted/50 text-muted-foreground border border-transparent cursor-pointer hover:bg-muted hover:text-foreground transition-colors">代码</span>
            </div>
          </div>
          
          <!-- Recent Used / Horizontal Scroll -->
          <ScrollArea class="w-full whitespace-nowrap pb-2">
            <div class="flex w-max space-x-3 p-1">
              <div v-for="s in userScripts" :key="s.id"
                class="group relative flex items-center gap-3 p-3 pr-4 rounded-xl border border-border/40 bg-white/40 backdrop-blur-md hover:bg-white/80 hover:shadow-md hover:border-primary/20 transition-all duration-300 cursor-pointer min-w-[180px] max-w-[240px]"
                @click="$emit('send-script', s.content)"
              >
                <!-- Icon Placeholder based on content type (mock logic) -->
                <div class="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center border border-blue-100/50 group-hover:scale-110 transition-transform duration-300">
                  <Zap class="w-4 h-4 text-blue-500/70 group-hover:text-blue-600" />
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
      <MessageList
        ref="messagesContainer"
        :messages="messages"
        :current-agent="currentAgent"
        :is-loading="isLoading"
        @locate-node="$emit('locate-node', $event)"
        @open-doc-space="$emit('open-doc-space', $event)"
      />

      <!-- Sticky Input Area -->
      <div class="flex-none w-full p-4 pb-6 z-30 sticky bottom-0 bg-transparent">
        <div class="absolute -top-12 left-0 w-full h-12 bg-gradient-to-t from-background to-transparent pointer-events-none"></div>
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
                        <span class="text-[11px] font-semibold leading-none truncate"
                            :class="(currentModeId || 'quick') === m.id ? getTheme(m.themeColor).titleText : 'text-foreground'">{{ m.name }}</span>
                        <span class="text-[9px] text-muted-foreground truncate leading-none opacity-80">{{ m.description }}</span>
                    </div>
                 </div>
              </div>
           </div>

           <SmartQAInput
              v-model="inputValue"
              :is-loading="isLoading"
              :is-task-running="isTaskRunning"
              :is-stopping="isStopping"
              :selected-attachments="selectedAttachments"
              :current-agent="currentAgent"
              :selected-agent-id="selectedAgentId"
              :agent-list="agentList"
              :current-mode-id="currentModeId"
              :embedded="embedded"
              :is-network-search-enabled="isNetworkSearchEnabled"
              @update:is-network-search-enabled="$emit('update:isNetworkSearchEnabled', $event)"
              @update:selectedAgentId="$emit('update:selectedAgentId', $event)"
              @send="$emit('send')"
              @stop="$emit('stop')"
              @open-attachment="$emit('open-attachment')"
              @remove-attachment="$emit('remove-attachment', $event)"
            />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { Check, X, Zap, ArrowRight } from 'lucide-vue-next';
import TechAnimation from '../TechAnimation.vue';
import MessageList from '../MessageList.vue';
import SmartQAInput from './SmartQAInput.vue';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { Agent, Message, Attachment, UserScript, ModeConfig, Team } from '../../types';

const props = defineProps<{
  messages: Message[];
  modes: ModeConfig[];
  currentModeId: string | null;
  embedded: boolean;
  isLoading: boolean;
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
  'remove-attachment'
]);

const inputValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

const isModeBarVisible = ref(false);

const themeConfig = {
  blue: {
    activeBorder: 'border-blue-500',
    activeRing: 'ring-blue-200',
    activeBg: 'bg-gradient-to-b from-blue-50/80 to-white/80 backdrop-blur-md',
    iconBg: 'bg-blue-100',
    iconText: 'text-blue-600',
    titleText: 'text-blue-700',
    checkBg: 'bg-blue-500',
    hoverBorder: 'hover:border-blue-200',
    hoverShadow: 'hover:shadow-blue-500/10',
  },
  green: {
    activeBorder: 'border-emerald-500',
    activeRing: 'ring-emerald-200',
    activeBg: 'bg-gradient-to-b from-emerald-50/80 to-white/80 backdrop-blur-md',
    iconBg: 'bg-emerald-100',
    iconText: 'text-emerald-600',
    titleText: 'text-emerald-700',
    checkBg: 'bg-emerald-500',
    hoverBorder: 'hover:border-emerald-200',
    hoverShadow: 'hover:shadow-emerald-500/10',
  },
  purple: {
    activeBorder: 'border-purple-500',
    activeRing: 'ring-purple-200',
    activeBg: 'bg-gradient-to-b from-purple-50/80 to-white/80 backdrop-blur-md',
    iconBg: 'bg-purple-100',
    iconText: 'text-purple-600',
    titleText: 'text-purple-700',
    checkBg: 'bg-purple-500',
    hoverBorder: 'hover:border-purple-200',
    hoverShadow: 'hover:shadow-purple-500/10',
  },
  orange: {
    activeBorder: 'border-orange-500',
    activeRing: 'ring-orange-200',
    activeBg: 'bg-gradient-to-b from-orange-50/80 to-white/80 backdrop-blur-md',
    iconBg: 'bg-orange-100',
    iconText: 'text-orange-600',
    titleText: 'text-orange-700',
    checkBg: 'bg-orange-500',
    hoverBorder: 'hover:border-orange-200',
    hoverShadow: 'hover:shadow-orange-500/10',
  },
  rose: {
    activeBorder: 'border-rose-500',
    activeRing: 'ring-rose-200',
    activeBg: 'bg-gradient-to-b from-rose-50/80 to-white/80 backdrop-blur-md',
    iconBg: 'bg-rose-100',
    iconText: 'text-rose-600',
    titleText: 'text-rose-700',
    checkBg: 'bg-rose-500',
    hoverBorder: 'hover:border-rose-200',
    hoverShadow: 'hover:shadow-rose-500/10',
  },
  slate: {
    activeBorder: 'border-slate-500',
    activeRing: 'ring-slate-200',
    activeBg: 'bg-gradient-to-b from-slate-50/80 to-white/80 backdrop-blur-md',
    iconBg: 'bg-slate-100',
    iconText: 'text-slate-600',
    titleText: 'text-slate-700',
    checkBg: 'bg-slate-500',
    hoverBorder: 'hover:border-slate-200',
    hoverShadow: 'hover:shadow-slate-500/10',
  }
};

const getTheme = (color: string = 'blue') => themeConfig[color as keyof typeof themeConfig] || themeConfig.blue;
</script>
