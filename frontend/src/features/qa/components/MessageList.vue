<template>
  <div class="flex-1 overflow-y-auto p-4 custom-scrollbar scroll-smooth" ref="containerRef">
    <div class="max-w-4xl mx-auto w-full space-y-6">
      <div v-for="(group, gIdx) in messageGroups" :key="gIdx" class="flex flex-col gap-1">


      <!-- Messages in Group -->
      <ChatCard 
        v-for="(msg, mIdx) in group.messages" 
        :key="mIdx"
        :message="msg"
        :type="msg.type || 'knowledge_qa'"
        :is-user="group.role === 'user'"
        :show-avatar="mIdx === 0"
        :show-meta="mIdx === 0 && group.role !== 'user'"
        :agent="currentAgent"
        @locate-node="$emit('locate-node', $event)"
        @open-doc-space="$emit('open-doc-space', $event)"
      />
      </div>

      <!-- Loading Indicator -->
      <div v-if="isLoading" class="flex gap-4 ml-10 mt-2">
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
import ChatCard from './ChatCard.vue';
import dayjs from 'dayjs';

const props = defineProps<{
  messages: any[];
  currentAgent: any;
  isLoading: boolean;
}>();

defineEmits(['locate-node', 'open-doc-space']);

const containerRef = ref<HTMLElement | null>(null);

// Grouping Logic
const messageGroups = computed(() => {
  if (!props.messages.length) return [];
  
  const groups: any[] = [];
  let currentGroup: any = null;

  props.messages.forEach((msg: any) => {
    const msgTime = msg.timestamp ? dayjs(msg.timestamp) : dayjs(); // Fallback to now if no timestamp
    
    // Check if we should start a new group
    let shouldGroup = false;
    if (currentGroup && currentGroup.role === msg.role) {
      const lastMsgTime = currentGroup.lastTimestamp;
      const diffMinutes = msgTime.diff(lastMsgTime, 'minute');
      if (diffMinutes < 5) { // 5 minutes window
        shouldGroup = true;
      }
    }

    if (shouldGroup) {
      currentGroup.messages.push(msg);
      currentGroup.lastTimestamp = msgTime;
    } else {
      // Start new group
      if (currentGroup) groups.push(currentGroup);
      
      const showTime = !currentGroup || msgTime.diff(currentGroup.lastTimestamp, 'minute') > 15; // Show time if > 15 mins gap
      
      currentGroup = {
        role: msg.role,
        messages: [msg],
        timestamp: msgTime,
        lastTimestamp: msgTime,
        showTime
      };
    }
  });

  if (currentGroup) groups.push(currentGroup);
  return groups;
});

const formatGroupTime = (dayjsObj: any) => {
  const now = dayjs();
  if (dayjsObj.isSame(now, 'day')) {
    return dayjsObj.format('HH:mm');
  } else if (dayjsObj.isSame(now.subtract(1, 'day'), 'day')) {
    return '昨天 ' + dayjsObj.format('HH:mm');
  } else {
    return dayjsObj.format('MM-DD HH:mm');
  }
};

const scrollToBottom = () => {
    nextTick(() => {
        if (containerRef.value) {
            containerRef.value.scrollTop = containerRef.value.scrollHeight;
        }
    });
};

watch(() => props.messages.length, () => {
    scrollToBottom();
});

watch(() => props.messages[props.messages.length - 1], (newVal: any) => {
    // Also scroll on content update (streaming)
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
