<template>
  <div class="flex-1 flex flex-col h-full relative min-w-0">
    <!-- Empty State -->
    <div v-if="messages.length === 0" class="flex-1 flex flex-col items-center justify-start pt-[15vh] px-4 overflow-y-auto relative custom-scrollbar">
      <div class="w-full max-w-2xl flex flex-col items-center gap-6">
        <div class="flex flex-col items-center gap-4">
          <TechAnimation :width="200" :height="200" class="mb-4" />
          <h1 v-if="!embedded" class="text-3xl font-bold tracking-tight text-foreground text-center">
            让我们创造点厉害的东西！
          </h1>
          <h1 v-else class="text-xl font-semibold text-foreground text-center">有什么可以帮您？</h1>
        </div>

        <!-- Mode Selection -->
        <div class="w-full pb-6 px-1">
          <div class="grid w-full grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div v-for="m in modes" :key="m.id"
              class="relative flex flex-col items-start justify-between p-4 rounded-xl border transition-all duration-300 cursor-pointer group h-[120px] overflow-hidden"
              :class="[
                (currentModeId || 'quick') === m.id
                  ? 'border-blue-500 bg-gradient-to-b from-blue-50 to-white shadow-md ring-1 ring-blue-200'
                  : 'border-transparent bg-white shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_24px_-4px_rgba(0,0,0,0.1)] hover:-translate-y-0.5'
              ]"
              @click="$emit('select-mode', m)"
            >
              <!-- Active State Check Icon -->
              <div v-if="(currentModeId || 'quick') === m.id" 
                class="absolute top-3 right-3 bg-blue-500 rounded-full p-0.5 animate-in fade-in zoom-in duration-200">
                <Check class="w-3 h-3 text-white" stroke-width="3" />
              </div>

              <!-- Icon -->
              <div v-if="(currentModeId || 'quick') === m.id" 
                class="p-2.5 rounded-lg mb-2 bg-blue-100 text-blue-600 animate-in fade-in zoom-in duration-300">
                <component :is="m.icon" class="w-5 h-5" stroke-width="2" />
              </div>

              <!-- Content -->
              <div class="flex flex-col w-full z-10 gap-1 mt-auto">
                <span class="text-sm font-bold tracking-wide transition-colors duration-300"
                  :class="(currentModeId || 'quick') === m.id ? 'text-blue-700' : 'text-gray-900'">
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
          <span class="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-1">快捷指令</span>
          <ScrollArea class="w-full whitespace-nowrap pb-4">
            <div class="flex w-max space-x-4 p-1">
              <Card v-for="s in userScripts" :key="s.id"
                class="w-[240px] h-[140px] flex flex-col justify-between p-5 cursor-pointer hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group relative overflow-hidden border-border/50 bg-card/50 backdrop-blur-sm"
                @click="$emit('send-script', s.content)"
              >
                <div class="absolute -right-8 -top-8 w-24 h-24 bg-primary/10 rounded-full blur-2xl group-hover:bg-primary/20 transition-colors"></div>
                <div class="flex flex-col gap-2 relative z-10">
                  <p class="text-xs text-muted-foreground group-hover:text-foreground line-clamp-3 leading-relaxed whitespace-normal transition-colors">
                    {{ s.content }}
                  </p>
                </div>
                <div class="relative z-10 flex items-center justify-between pt-4 border-t border-border/50 group-hover:border-primary/20 transition-colors">
                  <span class="text-sm font-semibold text-foreground group-hover:text-primary transition-colors truncate">{{ s.title }}</span>
                </div>
              </Card>
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
        <div class="max-w-4xl mx-auto relative">
           <!-- Compact Mode Selection -->
           <div class="pb-4">
              <div class="grid w-full grid-cols-5 gap-2">
                 <div v-for="m in modes" :key="m.id" 
                    class="relative flex flex-row items-center p-1.5 rounded-lg border bg-background/50 hover:bg-muted/50 transition-all cursor-pointer group h-[46px] gap-2"
                    :class="{'border-primary bg-primary/5 ring-1 ring-primary/20': (currentModeId || 'quick') === m.id, 'border-border/50': (currentModeId || 'quick') !== m.id}"
                    @click="$emit('select-mode', m)">
                    <div class="p-1 rounded-full shrink-0 transition-colors"
                        :class="(currentModeId || 'quick') === m.id ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground group-hover:text-foreground group-hover:bg-muted/80'">
                        <component :is="m.icon" class="w-3.5 h-3.5" />
                    </div>
                    <div class="flex flex-col min-w-0 text-left gap-0.5">
                        <span class="text-[11px] font-semibold leading-none truncate"
                            :class="(currentModeId || 'quick') === m.id ? 'text-primary' : 'text-foreground'">{{ m.name }}</span>
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
import { computed } from 'vue';
import { Check } from 'lucide-vue-next';
import TechAnimation from '../TechAnimation.vue';
import MessageList from '../MessageList.vue';
import SmartQAInput from './SmartQAInput.vue';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
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
</script>
