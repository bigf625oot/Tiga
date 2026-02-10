<template>
  <div class="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar scroll-smooth" ref="containerRef">
    <div v-for="(group, gIdx) in messageGroups" :key="gIdx" class="flex flex-col gap-1">
      <!-- Time Separator (Optional) -->
      <div v-if="group.showTime" class="flex justify-center my-4">
        <span class="text-xs text-slate-300 bg-slate-50/50 px-2 py-0.5 rounded-full">{{ formatGroupTime(group.timestamp) }}</span>
      </div>

      <!-- Messages in Group -->
      <MessageItem 
        v-for="(msg, mIdx) in group.messages" 
        :key="mIdx"
        :message="msg"
        :is-user="group.role === 'user'"
        :show-avatar="mIdx === 0"
        :show-meta="mIdx === 0 && group.role !== 'user'"
        :agent="currentAgent"
        :unique-id="`${gIdx}-${mIdx}`"
      />
    </div>

    <!-- Loading Indicator -->
    <div v-if="isLoading" class="flex gap-4 ml-10 mt-2">
        <div class="px-4 py-3 bg-slate-50 rounded-2xl rounded-tl-sm text-slate-400 text-xs flex items-center gap-1">
            <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0s"></span>
            <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></span>
            <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></span>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import MessageItem from './MessageItem.vue';
import dayjs from 'dayjs';

const props = defineProps({
  messages: { type: Array, default: () => [] },
  currentAgent: { type: Object, default: null },
  isLoading: { type: Boolean, default: false }
});

const containerRef = ref(null);

// Grouping Logic
const messageGroups = computed(() => {
  if (!props.messages.length) return [];
  
  const groups = [];
  let currentGroup = null;

  props.messages.forEach((msg, index) => {
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

const formatGroupTime = (dayjsObj) => {
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

watch(() => props.messages[props.messages.length - 1]?.content, () => {
    // Also scroll on content update (streaming)
    scrollToBottom();
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