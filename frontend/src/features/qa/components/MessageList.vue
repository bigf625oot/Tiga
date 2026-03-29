<template>
  <div class="h-full relative min-h-0 min-w-0 flex flex-col group/scrollbar">
    <!-- Virtual Scroll Container -->
    <DynamicScroller
      ref="scrollerRef"
      class="flex-1 min-h-0 overflow-y-auto overscroll-none px-10 pt-8 pb-16 no-scrollbar scroller-container"
      :items="messageGroupsWithId"
      :min-item-size="100"
      key-field="id"
      @scroll="handleScroll"
    >
      <template v-slot="{ item: group, index: idx, active }">
        <DynamicScrollerItem
          :item="group"
          :active="active"
          :size-dependencies="[
            group.messages.length,
            group.messages[group.messages.length - 1]?.content?.length,
            group.messages[group.messages.length - 1]?.reasoning?.length,
            props.isStreaming && idx === messageGroupsWithId.length - 1
          ]"
          :data-index="idx"
          class="max-w-4xl mx-auto w-full pb-8 scroll-mt-8"
        >
          <!-- 1. Normal Message Group -->
          <template v-if="!group.isLoader">
              <!-- Time Separator -->
              <div v-if="group.showTime" class="flex justify-center my-4">
                  <span class="text-[10px] text-muted-foreground/40 px-2 py-0.5 rounded-full select-none">
                  {{ formatGroupTime(group.timestamp) }}
                  </span>
              </div>
      
              <!-- Messages in Group -->
              <ChatCard 
                  v-for="(msg, mIdx) in group.messages" 
                  :key="msg.id || mIdx"
                  class="mb-6 last:mb-0"
                  :message="msg"
                  :type="msg.type || 'knowledge_qa'"
                  :is-user="group.role === 'user'"
                  :show-avatar="group.role === 'user' ? true : (mIdx === 0)"
                  :show-meta="mIdx === 0 && group.role !== 'user'"
                  :agent="currentAgent"
                  :is-last="idx === messageGroupsWithId.length - 1 && mIdx === group.messages.length - 1"
                  :is-streaming="props.isStreaming"
                  :current-mode-id="currentModeId ?? undefined"
                  @locate-node="$emit('locate-node', $event)"
                  @open-doc-space="$emit('open-doc-space', $event)"
                  @quote-message="$emit('quote-message', $event)"
                  @excerpt-message="$emit('excerpt-message', $event)"
                  @delete-message="$emit('delete-message', $event)"
                  @resend-message="$emit('resend-message', $event)"
                  @edit-message="$emit('edit-message', $event)"
              />
          </template>

          <!-- 2. Loading Indicator -->
          <template v-else>
              <div class="flex gap-4 mt-2 pb-4 animate-in fade-in duration-300">
                  <div class="flex-shrink-0">
                      <Skeleton class="h-8 w-8 rounded-full bg-muted/50" />
                  </div>
                  <div class="flex flex-col gap-2 w-full max-w-[80%]">
                      <div class="p-4 rounded-2xl rounded-tl-none bg-muted/20 border border-border/40 backdrop-blur-sm space-y-3">
                         <Skeleton class="h-4 w-[250px] bg-muted/60" />
                         <Skeleton class="h-4 w-[200px] bg-muted/60" />
                      </div>
                  </div>
              </div>
          </template>
        </DynamicScrollerItem>
      </template>
    </DynamicScroller>

    <!-- Custom Scrollbar/Anchor Navigation -->
    <div class="absolute right-0 top-0 bottom-0 w-8 z-40 pointer-events-none">
        <MessageAnchor
            :markers="markers"
            :current-visual-progress="currentVisualProgress"
            :accumulated-offsets="accumulatedOffsets"
            :estimated-total-height="totalHeight"
            :viewport-height="viewportHeight"
            :pulse-end="showScrollToBottomTip"
            :marker-every-n="anchorDensity.everyN"
            :marker-min-gap-px="anchorDensity.minGapPx"
            @scroll-to-index="scrollToGroup"
            @scroll-to-edge="handleScrollToEdge"
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
import { useResizeObserver, useDebounceFn } from '@vueuse/core';
import { ArrowDown } from 'lucide-vue-next';
import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller';
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';
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
  currentModeId?: string | null;
}>();

const emit = defineEmits(['locate-node', 'open-doc-space', 'quote-message', 'excerpt-message', 'delete-message', 'resend-message', 'edit-message']);

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

const messageGroupsWithId = computed(() => {
  return messageGroups.value.map((g, idx) => ({
    ...g,
    id: g.isLoader ? 'loading' : `group-${idx}`
  }));
});

const scrollerRef = ref<any>(null);
const containerRef = computed(() => scrollerRef.value?.$el);

watch(messageGroupsWithId, () => {
    nextTick(() => updateScrollMetrics());
}, { deep: true });

// --- Custom Scrollbar Logic ---
const scrollTop = ref(0);
const totalHeight = ref(0);
const viewportHeight = ref(0);
const isUserAtBottom = ref(true);
const showScrollToBottomTip = ref(false);

const actualScrollRange = computed(() => Math.max(1, totalHeight.value - viewportHeight.value));

const accumulatedOffsets = computed(() => {
    // vue-virtual-scroller calculates sizes, but we might just use a simple estimate or read from scroller
    const total = messageGroupsWithId.value.length;
    const offsets: number[] = [];
    let current = 0;
    
    // In DynamicScroller, sizes are kept internally. If we can't access them easily, we use fallback
    for (let i = 0; i < total; i++) {
        offsets.push(current);
        // We use a flat estimate if we don't query DOM anymore
        const h = scrollerRef.value?.vscrollData?.sizes?.[messageGroupsWithId.value[i].id] || 150;
        current += h;
    }
    
    return offsets;
});

const scrollRange = computed(() => Math.max(1, totalHeight.value - viewportHeight.value));

const anchorDensity = computed(() => {
    // Only count "normal" (non special) markers; specials should always be shown.
    const normalCount = markers.value.filter((m: any) => !m.isStart && !m.isEnd).length;

    const baseEveryN = 5;
    const baseMinGapPx = 16;

    // Target how many markers we want visible on the rail, based on viewport height.
    // Roughly: one marker per ~18px, clamped into a sane range.
    const targetVisible = Math.min(60, Math.max(12, Math.floor(viewportHeight.value / 18)));

    // Interval sampling factor: show 1 per everyN markers.
    // Make `everyN` grow in multiples of `baseEveryN`: 5, 10, 15, 20...
    const rawEveryN = Math.max(1, Math.ceil(normalCount / Math.max(1, targetVisible)));
    const everyNMultiplier = Math.max(1, Math.ceil(rawEveryN / baseEveryN));
    const everyN = baseEveryN * everyNMultiplier;

    // Height bucketing / merge gap: keep at least ~one marker per 16-22px.
    // As the viewport grows, we can afford a larger gap; keep within [12, 24].
    const minGapPx = Math.min(24, Math.max(baseMinGapPx, Math.round(viewportHeight.value / Math.max(1, targetVisible))));

    return { everyN, minGapPx };
});

const markers = computed(() => {
    if (!messageGroupsWithId.value.length) return [];
    
    const offsets = accumulatedOffsets.value;
    
    const userGroups = messageGroupsWithId.value
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
                // markerId must be unique and not collide with special markers
                index: g.originalIndex,
                scrollToIndex: g.originalIndex,
                topPercent,
                label: contentPreview,
                isEnd: false
            };
        });

    return [
        {
            index: -1,
            scrollToIndex: 0,
            topPercent: 0,
            label: '开始',
            isStart: true
        },
        ...userMarkers,
        {
            index: -2,
            scrollToIndex: lastGroupIndex,
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
    scheduleMetricsUpdate();
});

const startStreamingObserver = () => {
    if (!props.isStreaming) return;
    if (!containerRef.value) return;
    mutationObserver.disconnect();
    mutationObserver.observe(containerRef.value, {
        childList: true,
        subtree: true,
        characterData: true,
        attributes: false
    });
};

const stopStreamingObserver = () => {
    mutationObserver.disconnect();
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
    if (!scrollerRef.value) return;

    if (index <= 0) {
        scrollerRef.value.scrollToItem(0);
        setTimeout(updateScrollMetrics, 300);
        return;
    }

    if (index >= messageGroupsWithId.value.length - 1) {
        scrollToBottom(true);
        return;
    }
    
    scrollerRef.value.scrollToItem(index);
    setTimeout(updateScrollMetrics, 300);
};

const handleScrollToEdge = (edge: 'top' | 'bottom') => {
    if (!scrollerRef.value) return;
    if (edge === 'top') {
        scrollerRef.value.scrollToItem(0);
        setTimeout(updateScrollMetrics, 300);
        return;
    }
    scrollToBottom(true, true);
};

const scrollToBottom = (_force = false, smooth = false) => {
    nextTick(() => {
        if (scrollerRef.value) {
            scrollerRef.value.scrollToBottom();
            setTimeout(updateScrollMetrics, 350);
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
