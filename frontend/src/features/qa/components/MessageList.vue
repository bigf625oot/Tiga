<template>
  <div class="flex-1 relative min-h-0 flex flex-col group/scrollbar">
    <!-- Original Scroll Container -->
    <div 
      class="flex-1 overflow-y-auto px-10 pt-8 pb-32 custom-scrollbar scroll-smooth" 
      v-bind="containerProps"
      @scroll="handleScroll"
    >
      <div class="max-w-4xl mx-auto w-full">
        <div v-bind="wrapperProps">
          <div 
            v-for="item in list" 
            :key="item.index" 
            class="flex flex-col gap-6 mb-8"
          >
            <!-- Time Separator -->
          <div v-if="item.data.showTime" class="flex justify-center my-4">
            <span class="text-[10px] text-muted-foreground/40 px-2 py-0.5 rounded-full select-none">
              {{ formatGroupTime(item.data.timestamp) }}
            </span>
          </div>

            <!-- Messages in Group -->
            <ChatCard 
              v-for="(msg, mIdx) in item.data.messages" 
              :key="mIdx"
              class="mb-6 last:mb-0"
              :message="msg"
              :type="msg.type || 'knowledge_qa'"
              :is-user="item.data.role === 'user'"
              :show-avatar="mIdx === 0"
              :show-meta="mIdx === 0 && item.data.role !== 'user'"
              :agent="currentAgent"
              @locate-node="$emit('locate-node', $event)"
              @open-doc-space="$emit('open-doc-space', $event)"
              @quote-message="$emit('quote-message', $event)"
              @excerpt-message="$emit('excerpt-message', $event)"
            />
          </div>
        </div>

        <!-- Loading Indicator (Skeleton) -->
        <div v-if="isLoading" class="flex gap-4 ml-10 mt-2 pb-4 animate-in fade-in duration-300">
            <!-- Avatar -->
            <div class="flex-shrink-0">
                <Skeleton class="h-8 w-8 rounded-full bg-muted/50" />
            </div>
            
            <!-- Message Bubble Skeleton -->
            <div class="flex flex-col gap-2 w-full max-w-[80%]">
                <div class="flex items-center gap-2 mb-1">
                    <Skeleton class="h-4 w-24 rounded bg-muted/50" />
                    <Skeleton class="h-3 w-12 rounded bg-muted/30" />
                </div>
                <div class="space-y-2 p-4 rounded-2xl rounded-tl-none bg-muted/20 border border-border/40 backdrop-blur-sm">
                    <Skeleton class="h-4 w-full bg-muted/40" />
                    <Skeleton class="h-4 w-[90%] bg-muted/40" />
                    <Skeleton class="h-4 w-[95%] bg-muted/40" />
                    <div class="flex gap-2 pt-2">
                         <Skeleton class="h-20 w-32 rounded-lg bg-muted/30" />
                         <Skeleton class="h-20 w-32 rounded-lg bg-muted/30" />
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>

    <!-- Custom Scrollbar/Anchor Navigation -->
    <MessageAnchor
        :markers="markers"
        :total-height="totalHeight"
        :viewport-height="viewportHeight"
        :scroll-top="scrollTop"
        @update:scroll-top="handleScrollUpdate"
        @scroll-to-index="scrollToGroup"
    />

    <!-- New Message Notification / Scroll to Bottom Button -->
    <transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 translate-y-4"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-4"
    >
      <button
        v-if="showScrollToBottomTip"
        @click="handleScrollToBottomClick"
        class="absolute bottom-6 right-8 z-50 flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-full shadow-lg hover:bg-primary/90 hover:shadow-xl hover:-translate-y-0.5 transition-all duration-200"
      >
        <ArrowDown class="w-4 h-4 animate-bounce" />
        <span>下方有新消息</span>
      </button>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue';
import { useVirtualList, useResizeObserver, useDebounceFn } from '@vueuse/core';
import { ArrowDown } from 'lucide-vue-next';
import MessageAnchor from './MessageAnchor.vue';
import ChatCard from './ChatCard.vue';
import { Skeleton } from '@/components/ui/skeleton';
import dayjs from 'dayjs';
import { formatGroupTime } from '../utils/dateUtils';
import type { Message, Agent, Team } from '../types';

const props = defineProps<{
  messages: Message[];
  currentAgent: Agent | Team | undefined;
  isLoading: boolean;
}>();

const emit = defineEmits(['locate-node', 'open-doc-space', 'quote-message', 'excerpt-message']);

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

watch(messageGroups, () => {
    nextTick(() => updateScrollMetrics());
}, { deep: true });

const containerRef = containerProps.ref;

// --- Custom Scrollbar Logic ---
const scrollTop = ref(0);
const totalHeight = ref(0);
const viewportHeight = ref(0);
const isUserAtBottom = ref(true);
const showScrollToBottomTip = ref(false);

const markers = computed(() => {
    if (!messageGroups.value.length) return [];
    
    // Filter groups to find start of turns (User messages)
    // Map to percentage based on index
    const total = messageGroups.value.length;
    return messageGroups.value
        .map((g, i) => ({ ...g, originalIndex: i }))
        .filter(g => g.role === 'user')
        .map((g, i) => {
            const topPercent = (g.originalIndex / (total - 1 || 1)) * 100;
            const firstMsg = g.messages[0];
            const contentPreview = firstMsg.content ? (firstMsg.content.slice(0, 15) + (firstMsg.content.length > 15 ? '...' : '')) : `第 ${i + 1} 轮`;
            
            return {
                index: g.originalIndex,
                topPercent,
                label: contentPreview
            };
        });
});

const updateScrollMetrics = () => {
    if (!containerRef.value) return;
    const { clientHeight, scrollHeight, scrollTop: st } = containerRef.value;
    
    scrollTop.value = st;
    totalHeight.value = scrollHeight;
    viewportHeight.value = clientHeight;

    // Check if user is at bottom (with 100px threshold)
    const isBottom = scrollHeight - st - clientHeight <= 100;
    isUserAtBottom.value = isBottom;

    if (isBottom) {
        showScrollToBottomTip.value = false;
    }
};

const handleScroll = () => {
    updateScrollMetrics();
};

const handleScrollUpdate = (val: number) => {
    if (containerRef.value) {
        containerRef.value.scrollTop = val;
    }
};

// Debounced resize observer
const onResize = useDebounceFn(() => {
    updateScrollMetrics();
}, 150);

useResizeObserver(containerRef, onResize);

const scrollToGroup = (index: number) => {
    scrollTo(index);
    // Force immediate update after scroll initiation to update thumb position
    setTimeout(updateScrollMetrics, 50);
};

onMounted(() => {
    // Initial check
    nextTick(() => updateScrollMetrics());
});
// --- End Custom Scrollbar Logic ---

const scrollToBottom = (force = false) => {
    nextTick(() => {
        // Scroll to the last item index
        if (messageGroups.value.length > 0) {
            scrollTo(messageGroups.value.length - 1);
        }
        
        // Also ensure container is scrolled to bottom (for loading indicator visibility)
        if (containerRef.value) {
            containerRef.value.scrollTop = containerRef.value.scrollHeight;
        }
    });
};

const handleScrollToBottomClick = () => {
    scrollToBottom();
    showScrollToBottomTip.value = false;
    // We assume the user wants to be at the bottom now
    isUserAtBottom.value = true;
};

watch(() => props.messages.length, () => {
    // Always scroll to bottom if the last message is from user (they just sent it)
    const lastMsg = props.messages[props.messages.length - 1];
    if (lastMsg && lastMsg.role === 'user') {
         scrollToBottom(true);
         return;
    }

    if (isUserAtBottom.value) {
        scrollToBottom();
    } else {
        showScrollToBottomTip.value = true;
    }
});

watch(() => props.messages[props.messages.length - 1], (newVal) => {
    if (newVal && newVal.content) {
        if (isUserAtBottom.value) {
            scrollToBottom();
        } 
        // Note: For streaming updates, we might not want to show the tip repeatedly 
        // if the user is scrolling up. The tip should already be shown if they are not at bottom 
        // and a new message (length change) happened. 
        // But if the message is just growing, and the user hasn't seen the tip yet (maybe they just scrolled up),
        // we might want to show it?
        // Let's stick to showing it if content updates and we are not at bottom.
        else {
             showScrollToBottomTip.value = true;
        }
    }
}, { deep: true });

defineExpose({
    scrollToBottom
});
</script>

<style>
/* 隐藏原生滚动条 */
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}

/* 使用 :deep 或移除 scoped 以确保滚动条样式生效，这里尝试使用非 scoped 的方式或者更强的选择器 */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 transparent;
}

:root {
  --scrollbar-track: #e2e8f0;
  --scrollbar-thumb: #94a3b8;
  --scrollbar-marker: #3b82f6;
}
.dark {
  --scrollbar-track: #334155;
  --scrollbar-thumb: #64748b;
  --scrollbar-marker: #60a5fa;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
