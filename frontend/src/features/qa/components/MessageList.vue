<template>
  <div class="h-full relative min-h-0 min-w-0 flex flex-col group/scrollbar">
    <!-- Original Scroll Container -->
    <div 
      class="flex-1 overflow-y-auto overscroll-none px-10 pt-8 pb-10 no-scrollbar h-full" 
      v-bind="containerProps"
      @scroll="handleScroll"
    >
      <div class="max-w-4xl mx-auto w-full">
        <div v-bind="wrapperProps">
          <div 
            v-for="item in list" 
            :key="item.index" 
            :data-virtual-index="item.index"
            class="flex flex-col gap-6 pb-8 scroll-mt-8"
          >
            <!-- 1. Normal Message Group -->
            <template v-if="!item.data.isLoader">
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
                    @delete-message="$emit('delete-message', $event)"
                />
            </template>

            <!-- 2. Loading Indicator (As a Virtual Item) -->
            <template v-else>
                <div class="flex gap-4 ml-10 mt-2 pb-4 animate-in fade-in duration-300">
                    <!-- Avatar -->
                    <div class="flex-shrink-0">
                        <Skeleton class="h-8 w-8 rounded-full bg-muted/50" />
                    </div>
                    
                    <!-- Skeleton Loader -->
                    <div class="flex flex-col gap-2 w-full max-w-[80%]">
                        <div class="p-4 rounded-2xl rounded-tl-none bg-muted/20 border border-border/40 backdrop-blur-sm space-y-3">
                           <Skeleton class="h-4 w-[250px] bg-muted/60" />
                           <Skeleton class="h-4 w-[200px] bg-muted/60" />
                        </div>
                    </div>
                </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Custom Scrollbar/Anchor Navigation -->
    <div class="absolute right-0 top-0 bottom-32 w-8 z-40 pointer-events-none">
        <MessageAnchor
            :markers="markers"
            :current-visual-progress="currentVisualProgress"
            :accumulated-offsets="accumulatedHeights.offsets"
            :estimated-total-height="accumulatedHeights.totalHeight"
            :viewport-height="viewportHeight"
            @scroll-to-index="scrollToGroup"
            @update:currentVisualProgress="handleVisualProgressUpdate"
        />
    </div>

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
  isStreaming?: boolean;
}>();

const emit = defineEmits(['locate-node', 'open-doc-space', 'quote-message', 'excerpt-message', 'delete-message']);

// Grouping Logic
const messageGroups = computed(() => {
  const groups: any[] = [];
  
  if (props.messages.length) {
    let currentGroup: any = null;

    props.messages.forEach((msg) => {
      const msgTime = msg.timestamp ? dayjs(msg.timestamp) : dayjs();
      
      let shouldGroup = false;
      if (currentGroup && currentGroup.role === msg.role && !currentGroup.isLoader) {
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
          height: undefined,
          isLoader: false
        };
      }
    });

    if (currentGroup) groups.push(currentGroup);
  }

  // Check if we should append a loader group
  // Logic: Show loader if isLoading is true AND we don't have an active assistant response yet.
  // We check if it's currently streaming. If it's streaming, the loader should disappear 
  // because the actual message is being generated (whether reasoning or text).
  const lastMsg = props.messages[props.messages.length - 1];
  const hasStartedResponse = lastMsg && lastMsg.role !== 'user' && (lastMsg.content || lastMsg.reasoning || props.isStreaming);

  if (props.isLoading && !hasStartedResponse) {
      groups.push({
          isLoader: true,
          role: 'assistant',
          messages: [],
          timestamp: dayjs(),
          lastTimestamp: dayjs(),
          showTime: false,
          index: 'loading-placeholder' // Unique identifier
      });
  }

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

const actualScrollRange = computed(() => Math.max(1, totalHeight.value - viewportHeight.value));

// Height Map Logic for Accurate Visual Scrollbar
const itemHeights = ref<Record<number, number>>({});
const updateItemHeight = (index: number, el: Element | null) => {
    if (el) {
        itemHeights.value[index] = el.clientHeight;
    }
};

const accumulatedHeights = computed(() => {
    const total = messageGroups.value.length;
    const offsets: number[] = [];
    let current = 0;
    
    for (let i = 0; i < total; i++) {
        offsets.push(current);
        // Use recorded height or estimate (100)
        const h = itemHeights.value[i] || 100;
        current += h;
    }
    
    return { offsets, totalHeight: current };
});

const scrollRange = computed(() => Math.max(1, accumulatedHeights.value.totalHeight - viewportHeight.value));

const markers = computed(() => {
    if (!messageGroups.value.length) return [];
    
    const { offsets, totalHeight: estTotalHeight } = accumulatedHeights.value;
    
    const userGroups = messageGroups.value
        .map((g, i) => ({ ...g, originalIndex: i }))
        .filter(g => g.role === 'user');

    const lastGroupIndex = messageGroups.value.length - 1;
    const userMarkers = userGroups.map((g, i) => {
            // Use visual percentage based on height map
            const offset = offsets[g.originalIndex] || 0;
            const topPercent = Math.min(100, Math.max(0, (offset / scrollRange.value) * 100));
            
            const firstMsg = g.messages[0];
            const contentPreview = firstMsg.content ? (firstMsg.content.slice(0, 15) + (firstMsg.content.length > 15 ? '...' : '')) : `第 ${i + 1} 轮`;
            
            return {
                index: g.originalIndex,
                topPercent,
                label: contentPreview,
                isEnd: false
            };
        });

    return [
        ...userMarkers,
        {
            index: lastGroupIndex,
            topPercent: 100,
            label: '最新消息',
            isEnd: true
        }
    ];
});

const currentVisualProgress = computed(() => {
    if (!messageGroups.value.length) return 0;
    if (isUserAtBottom.value) return 1;
    return Math.min(1, Math.max(0, scrollTop.value / actualScrollRange.value));
});

const updateScrollMetrics = () => {
    if (!containerRef.value) return;
    const { clientHeight, scrollHeight, scrollTop: st } = containerRef.value;
    
    scrollTop.value = st;
    totalHeight.value = scrollHeight;
    viewportHeight.value = clientHeight;

    if (list.value.length > 0) {
        for (const item of list.value) {
            const el = containerRef.value.querySelector(`[data-virtual-index="${item.index}"]`);
            updateItemHeight(item.index, el);
        }
    }

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

// Watch for DOM changes in visible items to update height map
let streamObservedIndex = -1;
let rafMetricsId: number | null = null;

const scheduleMetricsUpdate = () => {
    if (rafMetricsId !== null) return;
    rafMetricsId = requestAnimationFrame(() => {
        rafMetricsId = null;
        updateScrollMetrics();
    });
};

const mutationObserver = new MutationObserver(() => {
    if (!props.isStreaming) return;
    if (!containerRef.value) return;
    if (streamObservedIndex < 0) return;
    const el = containerRef.value.querySelector(`[data-virtual-index="${streamObservedIndex}"]`);
    updateItemHeight(streamObservedIndex, el);
    scheduleMetricsUpdate();
});

const startStreamingObserver = () => {
    if (!props.isStreaming) return;
    if (!containerRef.value) return;
    mutationObserver.disconnect();
    streamObservedIndex = messageGroups.value.length - 1;
    const target = containerRef.value.querySelector(`[data-virtual-index="${streamObservedIndex}"]`) as HTMLElement | null;
    mutationObserver.observe(target ?? containerRef.value, {
        childList: true,
        subtree: true,
        characterData: true,
        attributes: false
    });
};

const stopStreamingObserver = () => {
    mutationObserver.disconnect();
    streamObservedIndex = -1;
};

onMounted(() => {
    nextTick(() => {
        updateScrollMetrics();
        startStreamingObserver();
    });
});

watch(() => props.isStreaming, (streaming) => {
    if (streaming) {
        nextTick(() => startStreamingObserver());
        return;
    }
    stopStreamingObserver();
});

watch(() => messageGroups.value.length, () => {
    if (!props.isStreaming) return;
    nextTick(() => startStreamingObserver());
});

onUnmounted(() => {
    if (rafMetricsId !== null) {
        cancelAnimationFrame(rafMetricsId);
        rafMetricsId = null;
    }
    mutationObserver.disconnect();
});


const handleVisualProgressUpdate = (progress: number) => {
    // progress is 0-1
    if (!containerRef.value) return;

    const p = Math.min(1, Math.max(0, progress));
    containerRef.value.scrollTop = p * actualScrollRange.value;
    updateScrollMetrics();
};

const scrollToGroup = (index: number) => {
    
    if (!containerRef.value) return;

    if (index >= messageGroups.value.length - 1) {
        scrollToBottom(true);
        return;
    }
    
    const el = containerRef.value.querySelector(`[data-virtual-index="${index}"]`) as HTMLElement | null;
    
    if (el) {
        // 元素已经渲染在 DOM 中了，直接平滑滚动
        const containerTop = containerRef.value.getBoundingClientRect().top;
        const elTop = el.getBoundingClientRect().top;
        const scrollOffset = elTop - containerTop + containerRef.value.scrollTop - 20; // 留 20px padding
        
        containerRef.value.scrollTo({
            top: scrollOffset,
            behavior: 'smooth'
        });
        setTimeout(updateScrollMetrics, 300);
    } else {
        // 元素还没渲染，需要先跳过去
        scrollTo(index);
        
        // 等待 Vue 渲染完成新的 DOM
        nextTick(() => {
            // 使用 setTimeout 确保浏览器完成了绘制
            setTimeout(() => {
                if (!containerRef.value) return;
                const targetEl = containerRef.value.querySelector(`[data-virtual-index="${index}"]`) as HTMLElement | null;
                
                if (targetEl) {
                    const containerTop = containerRef.value.getBoundingClientRect().top;
                    const elTop = targetEl.getBoundingClientRect().top;
                    const scrollOffset = elTop - containerTop + containerRef.value.scrollTop - 20;
                    
                    // 这里不用 smooth，因为刚刚已经瞬间跳过来了，如果用 smooth 会有来回拉扯的感觉
                    containerRef.value.scrollTo({
                        top: scrollOffset,
                        behavior: 'auto' 
                    });
                }
                updateScrollMetrics();
            }, 50);
        });
    }
};

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

// Watchers for State Sync
watch(() => props.isLoading, (newVal) => {
    if (newVal && isUserAtBottom.value) {
        scrollToBottom();
    }
});

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

// Watch for reasoning content updates (COE)
watch(() => {
    const lastMsg = props.messages[props.messages.length - 1];
    return lastMsg ? lastMsg.reasoning : null;
}, (newVal, oldVal) => {
    // If reasoning updates (stream outputting thought), scroll to bottom if user was at bottom
    if (newVal && newVal !== oldVal) {
        if (isUserAtBottom.value) {
            scrollToBottom();
        } 
        // Optional: show tip if not at bottom? Usually yes.
        else {
             showScrollToBottomTip.value = true;
        }
    }
});

watch(() => props.messages[props.messages.length - 1], (newVal) => {
    if (newVal && newVal.content) {
        if (isUserAtBottom.value) {
            scrollToBottom();
        } 
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
