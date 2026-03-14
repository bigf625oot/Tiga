<template>
  <div 
    ref="anchorRef"
    class="absolute right-4 top-4 bottom-4 w-4 z-50 flex flex-col justify-center select-none group/scrollbar"
    @mousedown="onTrackMouseDown"
  >
    <!-- Track -->
    <div class="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-[1px] bg-[var(--scrollbar-track)] rounded-full opacity-30 pointer-events-auto transition-opacity duration-200 group-hover/scrollbar:opacity-50 z-10"></div>

    <!-- Markers -->
    <div class="absolute inset-0 pointer-events-none z-30">
      <div 
        v-for="(marker, idx) in markers"
        :key="idx"
        class="absolute left-1/2 -translate-x-1/2 w-2 h-2 rounded-full bg-[var(--scrollbar-marker)] shadow-sm cursor-pointer pointer-events-auto transition-all duration-200 hover:scale-125 hover:bg-primary z-30 group/marker opacity-80 hover:opacity-100 border border-background"
        :style="{ top: marker.topPercent + '%' }"
        @mousedown.stop="onMarkerMouseDown($event, marker.index)"
      >
        <!-- Tooltip -->
        <div class="absolute right-3 top-1/2 -translate-y-1/2 px-3 py-2 bg-popover text-popover-foreground text-xs rounded-md shadow-md border border-border opacity-0 group-hover/marker:opacity-100 whitespace-nowrap pointer-events-none transition-all duration-200 translate-x-2 group-hover/marker:translate-x-0 z-40 max-w-[200px] truncate">
          {{ marker.label }}
        </div>
      </div>
    </div>

    <!-- Thumb -->
    <div
      v-if="canScroll"
      class="absolute left-1/2 -translate-x-1/2 w-1 bg-[var(--scrollbar-thumb)] opacity-80 rounded-[2px] cursor-pointer touch-none pointer-events-auto transition-all duration-200 hover:w-2 hover:opacity-100 z-20"
      :class="{ 'w-2 opacity-100': isDragging || isHovering }"
      :style="{ height: thumbHeight + 'px', top: thumbTop + 'px' }"
      @mousedown.stop="onThumbMouseDown"
      @mouseenter="isHovering = true"
      @mouseleave="isHovering = false"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, toRef } from 'vue';

const props = defineProps<{
  totalHeight: number;
  viewportHeight: number;
  scrollTop: number;
  markers: Array<{ topPercent: number; label: string; index: number }>;
}>();

const emit = defineEmits<{
  (e: 'update:scrollTop', value: number): void;
  (e: 'scroll-to-index', index: number): void;
}>();

const isDragging = ref(false);
const isHovering = ref(false);
const anchorRef = ref<HTMLElement | null>(null);

// Thumb Logic
const canScroll = computed(() => props.totalHeight > props.viewportHeight);

const thumbHeight = computed(() => {
  if (!canScroll.value) return 0;
  // Proportion: thumbHeight / viewportHeight = viewportHeight / totalHeight
  const height = (props.viewportHeight / props.totalHeight) * props.viewportHeight;
  return Math.max(20, height);
});

const thumbTop = computed(() => {
  if (!canScroll.value) return 0;
  const maxScrollTop = props.totalHeight - props.viewportHeight;
  const maxThumbTop = props.viewportHeight - thumbHeight.value;
  if (maxScrollTop <= 0) return 0;
  // Map scrollTop to thumbTop
  return (props.scrollTop / maxScrollTop) * maxThumbTop;
});

// Interaction Logic
let startY = 0;
let startScrollTop = 0;
let pendingMarkerIndex: number | null = null;
let interactionType: 'none' | 'thumb-drag' | 'marker-check' | 'track-drag' = 'none';

// Mouse Down on Track (Jump + Drag)
const onTrackMouseDown = (e: MouseEvent) => {
  if (interactionType !== 'none') return;
  e.preventDefault();
  
  if (!anchorRef.value) return;
  const rect = anchorRef.value.getBoundingClientRect();
  const clickY = e.clientY - rect.top;
  
  // Calculate expected scroll position from click percentage
  // clickY / viewportHeight = scrollTop / totalHeight ? No.
  // Scrollbar logic: clickY / viewportHeight = scrollTop / (totalHeight - viewportHeight) ?
  // Usually track click centers the thumb at click location.
  // thumbTop = clickY - thumbHeight/2
  let targetThumbTop = clickY - thumbHeight.value / 2;
  const maxThumbTop = props.viewportHeight - thumbHeight.value;
  targetThumbTop = Math.max(0, Math.min(targetThumbTop, maxThumbTop));
  
  const maxScrollTop = props.totalHeight - props.viewportHeight;
  const newScrollTop = (targetThumbTop / maxThumbTop) * maxScrollTop;
  
  emit('update:scrollTop', newScrollTop);
  
  // Start dragging from here
  interactionType = 'track-drag';
  isDragging.value = true;
  startY = e.clientY;
  startScrollTop = newScrollTop;
  
  addGlobalListeners();
};

// Mouse Down on Thumb (Drag)
const onThumbMouseDown = (e: MouseEvent) => {
  e.preventDefault();
  e.stopPropagation();
  
  interactionType = 'thumb-drag';
  isDragging.value = true;
  startY = e.clientY;
  startScrollTop = props.scrollTop;
  
  addGlobalListeners();
};

// Mouse Down on Marker (Check Click vs Drag)
const onMarkerMouseDown = (e: MouseEvent, index: number) => {
  e.preventDefault();
  e.stopPropagation();
  
  interactionType = 'marker-check';
  pendingMarkerIndex = index;
  startY = e.clientY;
  startScrollTop = props.scrollTop; // If we start dragging, we start from current pos
  
  addGlobalListeners();
};

const onGlobalMouseMove = (e: MouseEvent) => {
  const deltaY = e.clientY - startY;
  
  if (interactionType === 'marker-check') {
    // Threshold check
    if (Math.abs(deltaY) > 3) {
      interactionType = 'thumb-drag'; // Switch to drag mode
      isDragging.value = true;
      pendingMarkerIndex = null; // Cancel click
    }
  }
  
  if (interactionType === 'thumb-drag' || interactionType === 'track-drag') {
    e.preventDefault();
    
    // Calculate scroll delta
    const maxThumbTop = props.viewportHeight - thumbHeight.value;
    const maxScrollTop = props.totalHeight - props.viewportHeight;
    
    // Ratio: 1px of thumb movement = X px of scroll
    const scrollRatio = maxScrollTop / (maxThumbTop || 1);
    
    const newScrollTop = startScrollTop + deltaY * scrollRatio;
    // Clamp
    const clampedScrollTop = Math.max(0, Math.min(newScrollTop, maxScrollTop));
    
    emit('update:scrollTop', clampedScrollTop);
  }
};

const onGlobalMouseUp = (e: MouseEvent) => {
  if (interactionType === 'marker-check' && pendingMarkerIndex !== null) {
    // It was a click
    emit('scroll-to-index', pendingMarkerIndex);
  }
  
  interactionType = 'none';
  isDragging.value = false;
  pendingMarkerIndex = null;
  removeGlobalListeners();
};

const addGlobalListeners = () => {
  document.addEventListener('mousemove', onGlobalMouseMove);
  document.addEventListener('mouseup', onGlobalMouseUp);
};

const removeGlobalListeners = () => {
  document.removeEventListener('mousemove', onGlobalMouseMove);
  document.removeEventListener('mouseup', onGlobalMouseUp);
};

onUnmounted(() => {
  removeGlobalListeners();
});
</script>

<style scoped>
/* Scoped styles if needed */
</style>
