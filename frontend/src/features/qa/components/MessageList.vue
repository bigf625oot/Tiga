<template>
  <div class="flex-1 overflow-y-auto p-4 custom-scrollbar scroll-smooth" ref="containerRef">
    <div class="max-w-4xl mx-auto w-full" v-bind="containerProps">
      <div v-bind="wrapperProps">
        <div 
          v-for="item in list" 
          :key="item.index" 
          class="flex flex-col gap-1 mb-6"
          :style="{ height: `${item.data.height}px` }"
        >
          <!-- Time Separator -->
          <div v-if="item.data.showTime" class="flex justify-center my-4">
            <span class="text-xs text-muted-foreground bg-muted/30 px-2 py-1 rounded-full">
              {{ formatGroupTime(item.data.timestamp) }}
            </span>
          </div>

          <!-- Messages in Group -->
          <ChatCard 
            v-for="(msg, mIdx) in item.data.messages" 
            :key="mIdx"
            :message="msg"
            :type="msg.type || 'knowledge_qa'"
            :is-user="item.data.role === 'user'"
            :show-avatar="mIdx === 0"
            :show-meta="mIdx === 0 && item.data.role !== 'user'"
            :agent="currentAgent"
            @locate-node="$emit('locate-node', $event)"
            @open-doc-space="$emit('open-doc-space', $event)"
          />
        </div>
      </div>

      <!-- Loading Indicator -->
      <div v-if="isLoading" class="flex gap-4 ml-10 mt-2 pb-4">
          <div class="px-4 p-4 bg-muted/50 rounded-lg rounded-tl-sm text-muted-foreground text-xs flex items-center gap-1">
              <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0s"></span>
              <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></span>
              <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></span>
          </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import { useVirtualList } from '@vueuse/core';
import ChatCard from './ChatCard.vue';
import dayjs from 'dayjs';
import { formatGroupTime } from '../utils/dateUtils';
import type { Message, Agent, Team } from '../types';

const props = defineProps<{
  messages: Message[];
  currentAgent: Agent | Team | undefined;
  isLoading: boolean;
}>();

defineEmits(['locate-node', 'open-doc-space']);

// Grouping Logic
const messageGroups = computed(() => {
  if (!props.messages.length) return [];
  
  const groups: any[] = [];
  let currentGroup: any = null;

  props.messages.forEach((msg) => {
    const msgTime = msg.timestamp ? dayjs(msg.timestamp) : dayjs();
    
    let shouldGroup = false;
    if (currentGroup && currentGroup.role === msg.role) {
      const lastMsgTime = currentGroup.lastTimestamp;
      const diffMinutes = msgTime.diff(lastMsgTime, 'minute');
      if (diffMinutes < 5) {
        shouldGroup = true;
      }
    }

    if (shouldGroup) {
      currentGroup.messages.push(msg);
      currentGroup.lastTimestamp = msgTime;
    } else {
      if (currentGroup) groups.push(currentGroup);
      
      const showTime = !currentGroup || msgTime.diff(currentGroup.lastTimestamp, 'minute') > 15;
      
      currentGroup = {
        role: msg.role,
        messages: [msg],
        timestamp: msgTime,
        lastTimestamp: msgTime,
        showTime,
        // Estimate height: base 60px + 40px per message + extra for content
        // This is rough estimation, useVirtualList handles dynamic height if configured but simple estimation helps
        height: undefined 
      };
    }
  });

  if (currentGroup) groups.push(currentGroup);
  return groups;
});

// Virtual List
const { list, containerProps, wrapperProps, scrollTo } = useVirtualList(
  messageGroups,
  {
    itemHeight: 100 // Estimate height
  }
);

const containerRef = ref<HTMLElement | null>(null);

const scrollToBottom = () => {
    nextTick(() => {
        // Scroll to the last item index
        scrollTo(messageGroups.value.length - 1);
        
        // Also ensure container is scrolled to bottom (for loading indicator visibility)
        if (containerRef.value) {
            containerRef.value.scrollTop = containerRef.value.scrollHeight;
        }
    });
};

watch(() => props.messages.length, () => {
    scrollToBottom();
});

watch(() => props.messages[props.messages.length - 1], (newVal) => {
    if (newVal && newVal.content) {
        scrollToBottom();
    }
}, { deep: true });

defineExpose({
    scrollToBottom
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
