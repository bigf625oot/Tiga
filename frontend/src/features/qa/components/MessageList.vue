<template>
  <div class="h-full relative min-h-0 min-w-0 flex flex-col group/scrollbar">
    <div 
      class="flex-1 overflow-y-auto overscroll-none px-10 pt-8 no-scrollbar h-full" 
      v-bind="containerProps"
      @scroll="handleScroll"
      @wheel="handleUserInteraction"
      @touchstart="handleUserInteraction"
      @mousedown="handleUserInteraction"
      @keydown="handleUserInteraction"
    >
      <div class="max-w-4xl mx-auto w-full">
        <div v-bind="wrapperProps">
          <div 
            v-for="item in list" 
            :key="item.index" 
            :data-virtual-index="item.index"
            class="flex flex-col gap-6 scroll-mt-8"
            :class="{ 'pb-8': !item.data.isSpacer }"
          >
            <!-- Normal Message Group -->
            <template v-if="!item.data.isLoader && !item.data.isSpacer">
                <div v-if="item.data.showTime" class="flex justify-center my-4">
                    <span class="text-[10px] text-muted-foreground/40 px-2 py-0.5 rounded-full select-none">
                    {{ formatGroupTime(item.data.timestamp) }}
                    </span>
                </div>
        
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
                    :is-last="msg === messages[messages.length - 1]"
                    :is-streaming="isStreaming"
                    @locate-node="$emit('locate-node', $event)"
                    @open-doc-space="$emit('open-doc-space', $event)"
                    @quote-message="$emit('quote-message', $event)"
                    @excerpt-message="$emit('excerpt-message', $event)"
                    @delete-message="$emit('delete-message', $event)"
                    @resend-message="$emit('resend-message', $event)"
                    @edit-message="$emit('edit-message', $event)"
                />
            </template>

            <!-- Loading Indicator -->
            <template v-else-if="item.data.isLoader">
                <div class="flex gap-4 ml-10 mt-2 pb-4 animate-in fade-in duration-300">
                    <div class="flex-shrink-0">
                        <div class="h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 flex items-center justify-center shadow-sm">
                            <div class="relative flex h-3 w-3">
                              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                              <span class="relative inline-flex rounded-full h-3 w-3 bg-indigo-500"></span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="flex flex-col gap-2 w-full max-w-[80%]">
                        <div class="p-4 rounded-2xl rounded-tl-none bg-muted/30 border border-border/60 backdrop-blur-md shadow-sm">
                           <template v-if="loadingStatus">
                               <div class="flex items-center gap-3">
                                   <!-- Animated AI Thinking Icon -->
                                   <div class="flex space-x-1 h-4 items-center">
                                       <div class="w-1.5 h-1.5 bg-indigo-500/70 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
                                       <div class="w-1.5 h-1.5 bg-purple-500/70 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
                                       <div class="w-1.5 h-1.5 bg-pink-500/70 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
                                   </div>
                                   <span class="text-xs font-medium text-muted-foreground bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-purple-600 animate-pulse">
                                       {{ loadingStatus }}
                                   </span>
                               </div>
                           </template>
                           <template v-else>
                               <!-- Fallback Loading State -->
                               <div class="flex items-center gap-3">
                                   <div class="flex space-x-1 h-4 items-center">
                                       <div class="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
                                       <div class="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
                                       <div class="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
                                   </div>
                                   <span class="text-xs text-muted-foreground/60 font-medium">正在思考...</span>
                               </div>
                           </template>
                        </div>
                    </div>
                </div>
            </template>
            <!-- Bottom Spacer -->
            <template v-else-if="item.data.isSpacer">
                <div class="h-32 w-full flex-shrink-0 pointer-events-none"></div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Custom Scrollbar/Anchor Navigation -->
    <div class="absolute right-0 top-0 bottom-4 w-8 z-40 pointer-events-none">
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

    <!-- Scroll to Bottom Button -->
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
  loadingStatus?: string;
}>();

const emit = defineEmits(['locate-node', 'open-doc-space', 'quote-message', 'excerpt-message', 'delete-message', 'resend-message', 'edit-message']);

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

  groups.push({
      isSpacer: true,
      role: 'assistant',
      messages: [],
      timestamp: dayjs(),
      lastTimestamp: dayjs(),
      showTime: false,
      index: 'bottom-spacer'
  });

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
          index: 'loading-placeholder'
      });
  }

  return groups;
});

const ESTIMATED_ITEM_HEIGHT = 150;

const { list, containerProps, wrapperProps, scrollTo } = useVirtualList(
  messageGroups,
  {
    itemHeight: ESTIMATED_ITEM_HEIGHT
  }
);

const containerRef = containerProps.ref;

watch(messageGroups, (newVal, oldVal) => {
    const isFirstLoad = !oldVal || oldVal.length === 0;
    const wasAtBottom = isUserAtBottom.value;

    nextTick(() => {
        updateScrollMetrics(false);
        
        const lastMsg = props.messages[props.messages.length - 1];
        const isUserMessage = lastMsg && lastMsg.role === 'user';
        
        if (isFirstLoad) {
            scrollToBottom(true);
            return;
        }

        if (isUserMessage) {
            scrollToBottom(true);
            return;
        }

        if (wasAtBottom) {
            scrollToBottom();
        } else {
            showScrollToBottomTip.value = true;
        }
    });
}, { deep: true });

const scrollTop = ref(0);
const totalHeight = ref(0);
const viewportHeight = ref(0);
const isUserAtBottom = ref(true);
const showScrollToBottomTip = ref(false);

const actualScrollRange = computed(() => Math.max(1, totalHeight.value - viewportHeight.value));

const itemHeights = ref<Record<number, number>>({});
const updateItemHeight = (index: number, el: Element | null) => {
    if (el) {
        itemHeights.value[index] = el.clientHeight;
    }
};

const accumulatedHeights = computed(() => {
    const visibleGroups = messageGroups.value.filter(g => !g.isSpacer);
    const total = visibleGroups.length;
    const offsets: number[] = [];
    let current = 0;
    
    for (let i = 0; i < total; i++) {
        offsets.push(current);
        const h = itemHeights.value[i] || ESTIMATED_ITEM_HEIGHT;
        current += h;
    }
    
    return { offsets, totalHeight: current };
});

const scrollRange = computed(() => Math.max(1, accumulatedHeights.value.totalHeight - viewportHeight.value));

let isUserInteracting = false;
let userInteractionTimeout: number | null = null;

const handleUserInteraction = () => {
    isUserInteracting = true;
    if (userInteractionTimeout) clearTimeout(userInteractionTimeout);
    userInteractionTimeout = setTimeout(() => {
        isUserInteracting = false;
    }, 1000) as unknown as number;
};

const markers = computed(() => {
    const visibleGroups = messageGroups.value.filter(g => !g.isSpacer);
    if (!visibleGroups.length) return [];
    
    const { offsets, totalHeight: estTotalHeight } = accumulatedHeights.value;
    
    const userGroups = visibleGroups
        .map((g, i) => ({ ...g, originalIndex: i }))
        .filter(g => g.role === 'user');

    const lastGroupIndex = visibleGroups.length - 1;
    const userMarkers = userGroups.map((g, i) => {
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
    const visibleGroups = messageGroups.value.filter(g => !g.isSpacer);
    if (!visibleGroups.length) return 0;
    
    return Math.min(1, Math.max(0, scrollTop.value / scrollRange.value));
});

const updateScrollMetrics = (isScrollEvent = false) => {
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

    const isBottom = scrollHeight - st - clientHeight <= 150;

    if (isScrollEvent) {
        if (isUserInteracting) {
            isUserAtBottom.value = isBottom;
        } else {
            if (!isUserAtBottom.value) {
                isUserAtBottom.value = isBottom;
            }
        }
    } else {
        if (!isUserAtBottom.value) {
            isUserAtBottom.value = isBottom;
        }
    }

    if (isUserAtBottom.value) {
        showScrollToBottomTip.value = false;
    }
};

const handleScroll = () => {
    updateScrollMetrics(true);
};

const handleScrollUpdate = (val: number) => {
    if (containerRef.value) {
        containerRef.value.scrollTo({
            top: val,
            behavior: 'auto'
        });
    }
};

const onResize = useDebounceFn(() => {
    if (isUserAtBottom.value) {
        pinToBottom();
    }
    updateScrollMetrics(false);
}, 150);

useResizeObserver(containerRef, onResize);

let streamObservedIndex = -1;
let rafMetricsId: number | null = null;

const scheduleMetricsUpdate = () => {
    if (rafMetricsId !== null) return;
    rafMetricsId = requestAnimationFrame(() => {
        rafMetricsId = null;
        updateScrollMetrics();
    });
};

const pinToBottom = () => {
    if (!containerRef.value) return;
    containerRef.value.scrollTo({
        top: containerRef.value.scrollHeight,
        behavior: 'auto'
    });
};

const mutationObserver = new MutationObserver(() => {
    if (!props.isStreaming) return;
    if (!containerRef.value) return;
    if (streamObservedIndex < 0) return;
    const el = containerRef.value.querySelector(`[data-virtual-index="${streamObservedIndex}"]`);
    updateItemHeight(streamObservedIndex, el);
    
    if (isUserAtBottom.value) {
        pinToBottom();
    }
    
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
        if (props.messages.length > 0) {
            scrollToBottom(true);
        }
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
    if (!containerRef.value) return;

    const p = Math.min(1, Math.max(0, progress));
    
    containerRef.value.scrollTo({
        top: p * scrollRange.value,
        behavior: 'auto'
    });
    
    handleUserInteraction();
    updateScrollMetrics(false);
};

const scrollToGroup = (index: number) => {
    
    if (!containerRef.value) return;

    handleUserInteraction();

    if (index >= messageGroups.value.length - 1) {
        scrollToBottom(true);
        return;
    }
    
    const el = containerRef.value.querySelector(`[data-virtual-index="${index}"]`) as HTMLElement | null;
    
    if (el) {
        const containerTop = containerRef.value.getBoundingClientRect().top;
        const elTop = el.getBoundingClientRect().top;
        const scrollOffset = elTop - containerTop + containerRef.value.scrollTop - 20;
        
        containerRef.value.scrollTo({
            top: scrollOffset,
            behavior: 'smooth'
        });
        setTimeout(updateScrollMetrics, 300);
    } else {
        scrollTo(index);
        
        nextTick(() => {
            setTimeout(() => {
                if (!containerRef.value) return;
                const targetEl = containerRef.value.querySelector(`[data-virtual-index="${index}"]`) as HTMLElement | null;
                
                if (targetEl) {
                    const containerTop = containerRef.value.getBoundingClientRect().top;
                    const elTop = targetEl.getBoundingClientRect().top;
                    const scrollOffset = elTop - containerTop + containerRef.value.scrollTop - 20;
                    
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
        if (!containerRef.value) return;

        const lastIndex = messageGroups.value.length - 1;
        if (lastIndex < 0) return;

        scrollTo(lastIndex);

        setTimeout(() => {
            if (!containerRef.value) return;
            containerRef.value.scrollTo({
                top: containerRef.value.scrollHeight,
                behavior: 'auto'
            });
            updateScrollMetrics(false);
            
            setTimeout(() => {
                if (!containerRef.value) return;
                containerRef.value.scrollTo({
                    top: containerRef.value.scrollHeight,
                    behavior: 'auto'
                });
                updateScrollMetrics(false);
            }, 100);
        }, 50);
    });
};

const handleScrollToBottomClick = () => {
    scrollToBottom();
    showScrollToBottomTip.value = false;
    isUserAtBottom.value = true;
};

watch(() => props.isLoading, (newVal) => {
    if (newVal && isUserAtBottom.value) {
        scrollToBottom();
    }
});

watch(() => props.messages.length, () => {
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

watch(() => {
    const lastMsg = props.messages[props.messages.length - 1];
    return lastMsg ? lastMsg.reasoning : null;
}, (newVal, oldVal) => {
    if (newVal && newVal !== oldVal) {
        if (isUserAtBottom.value) {
            nextTick(() => pinToBottom());
        } else {
             showScrollToBottomTip.value = true;
        }
    }
});

watch(() => props.messages[props.messages.length - 1], (newVal) => {
    if (newVal && newVal.content) {
        if (isUserAtBottom.value) {
            nextTick(() => pinToBottom());
        } else {
             showScrollToBottomTip.value = true;
        }
    }
}, { deep: true });

defineExpose({
    scrollToBottom
});
</script>

<style>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

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
