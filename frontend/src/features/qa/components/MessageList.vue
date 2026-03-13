<template>
  <div class="flex-1 relative min-h-0 flex flex-col group/scrollbar">
    <!-- Original Scroll Container -->
    <div 
      class="flex-1 overflow-y-auto px-10 pt-8 pb-12 custom-scrollbar scroll-smooth no-scrollbar" 
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
    <div 
       class="absolute right-4 top-4 bottom-4 w-1 z-50 opacity-100 flex flex-col justify-center pointer-events-none"
    >
        <!-- Track (Visible always or only when needed? User said 'like anchors', so maybe always visible structure) -->
        <div class="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-[1px] bg-[var(--scrollbar-track)] rounded-full opacity-30 pointer-events-auto hover:opacity-50 transition-opacity"></div>

        <!-- Markers Container (Relative to track) -->
        <div class="absolute inset-0 pointer-events-none">
            <div 
                v-for="(marker, idx) in markers"
                :key="idx"
                class="absolute left-1/2 -translate-x-1/2 w-[3px] h-[12px] rounded-full bg-[var(--scrollbar-marker)] shadow-sm cursor-pointer pointer-events-auto transition-all duration-200 hover:scale-x-125 hover:bg-primary z-20 group/marker opacity-60 hover:opacity-100"
                :style="{ top: marker.topPercent + '%' }"
                @click.stop="scrollToGroup(marker.index)"
            >
            <!-- Tooltip -->
            <div class="absolute right-3 top-1/2 -translate-y-1/2 px-3 py-2 bg-popover text-popover-foreground text-xs rounded-md shadow-md border border-border opacity-0 group-hover/marker:opacity-100 whitespace-nowrap pointer-events-none transition-all duration-200 translate-x-2 group-hover/marker:translate-x-0 z-30 max-w-[200px] truncate">
                {{ marker.label }}
            </div>
            </div>
        </div>

        <!-- Thumb (Only visible when scrollable) -->
        <div
           v-if="canScroll"
           class="absolute left-0 w-full bg-[var(--scrollbar-thumb)] opacity-80 rounded-[2px] cursor-pointer select-none touch-none pointer-events-auto"
           :style="{ height: thumbHeight + 'px', top: thumbTop + 'px' }"
           @mousedown="onThumbMouseDown"
           tabindex="0"
           @keydown="onThumbKeyDown"
        ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue';
import { useVirtualList, useResizeObserver, useDebounceFn } from '@vueuse/core';
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

watch(messageGroups, () => {
    nextTick(() => updateScrollMetrics());
}, { deep: true });

const containerRef = containerProps.ref;

// --- Custom Scrollbar Logic ---
const canScroll = ref(false);
const thumbHeight = ref(20);
const thumbTop = ref(0);
const isScrolling = ref(false);
const isHoveringScrollbar = ref(false);
const isDragging = ref(false);
let startY = 0;
let startScrollTop = 0;
let scrollTimeout: number | null = null;

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
    const { clientHeight, scrollHeight, scrollTop } = containerRef.value;
    
    canScroll.value = scrollHeight > clientHeight;
    // We update metrics even if not scrollable, to be safe, but thumb is hidden via v-if
    // If not scrollable, thumbTop is 0, thumbHeight is clientHeight (or close to it)

    // Calculate Thumb Height
    // Proportion: thumbHeight / clientHeight = clientHeight / scrollHeight
    const calculatedHeight = (clientHeight / scrollHeight) * clientHeight;
    thumbHeight.value = Math.max(20, calculatedHeight);

    // Calculate Thumb Top
    // Proportion: thumbTop / (clientHeight - thumbHeight) = scrollTop / (scrollHeight - clientHeight)
    const maxScrollTop = scrollHeight - clientHeight;
    const maxThumbTop = clientHeight - thumbHeight.value;
    
    if (maxScrollTop > 0) {
        thumbTop.value = (scrollTop / maxScrollTop) * maxThumbTop;
    } else {
        thumbTop.value = 0;
    }
};

const handleScroll = () => {
    if (isDragging.value) return; // Skip update if dragging to avoid jitter
    isScrolling.value = true;
    updateScrollMetrics();
    
    if (scrollTimeout) window.clearTimeout(scrollTimeout);
    scrollTimeout = window.setTimeout(() => {
        isScrolling.value = false;
    }, 1000);
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

const onThumbMouseDown = (e: MouseEvent) => {
    e.preventDefault(); // Prevent text selection
    e.stopPropagation();
    if (!containerRef.value) return;
    
    isDragging.value = true;
    isScrolling.value = true; // Keep scrollbar visible
    startY = e.clientY;
    startScrollTop = containerRef.value.scrollTop;
    
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
};

const onMouseMove = (e: MouseEvent) => {
    if (!isDragging.value || !containerRef.value) return;
    
    const deltaY = e.clientY - startY;
    const { scrollHeight, clientHeight } = containerRef.value;
    
    // Calculate new ScrollTop
    // deltaY corresponds to scroll delta: deltaScroll = deltaY * (scrollHeight / clientHeight)
    // Or more precisely based on available track space
    const maxThumbTop = clientHeight - thumbHeight.value;
    const maxScrollTop = scrollHeight - clientHeight;
    
    // Ratio of track movement to scroll movement
    // thumb moves 1px -> scroll moves (maxScrollTop / maxThumbTop) px
    const scrollRatio = maxScrollTop / maxThumbTop;
    
    containerRef.value.scrollTop = startScrollTop + deltaY * scrollRatio;
    
    // Manually update thumbTop for smoothness during drag (though scroll event will also trigger)
    // We rely on scroll event for final position but can pre-calculate for UI responsiveness if needed
    // updateScrollMetrics() is called by scroll event listener
};

const onMouseUp = () => {
    isDragging.value = false;
    isScrolling.value = false;
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
};

const onThumbKeyDown = (e: KeyboardEvent) => {
    if (!containerRef.value) return;
    const { clientHeight } = containerRef.value;
    
    if (e.key === 'ArrowUp') {
        containerRef.value.scrollBy({ top: -100, behavior: 'smooth' });
        e.preventDefault();
    } else if (e.key === 'ArrowDown') {
        containerRef.value.scrollBy({ top: 100, behavior: 'smooth' });
        e.preventDefault();
    } else if (e.key === 'PageUp') {
        containerRef.value.scrollBy({ top: -clientHeight / 2, behavior: 'smooth' });
        e.preventDefault();
    } else if (e.key === 'PageDown') {
        containerRef.value.scrollBy({ top: clientHeight / 2, behavior: 'smooth' });
        e.preventDefault();
    }
};

onMounted(() => {
    // Initial check
    nextTick(() => updateScrollMetrics());
});
// --- End Custom Scrollbar Logic ---

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
