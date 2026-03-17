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
        v-for="(marker, idx) in markersWithPosition"
        :key="idx"
        class="absolute left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-[var(--scrollbar-marker)] shadow-sm cursor-pointer pointer-events-auto transition-all duration-200 hover:scale-125 hover:bg-primary z-30 group/marker opacity-80 hover:opacity-100 border border-background"
        :class="{
          'bg-primary opacity-100 animate-pulse': marker.isEnd === true,
          'scale-150 bg-primary opacity-100': snappedMarkerIndex === marker.index
        }"
        :style="{ top: marker.topPx + 'px' }"
        @mousedown.stop="onMarkerMouseDown($event, marker.index)"
      >
        <!-- Tooltip -->
        <div
          class="absolute right-3 top-1/2 -translate-y-1/2 px-3 py-2 bg-popover text-popover-foreground text-xs rounded-md shadow-md border border-border opacity-0 group-hover/marker:opacity-100 whitespace-nowrap pointer-events-none transition-all duration-200 translate-x-2 group-hover/marker:translate-x-0 z-40 max-w-[200px] truncate"
          :class="{ 'opacity-100 translate-x-0': snappedMarkerIndex === marker.index }"
        >
          {{ marker.label }}
        </div>
      </div>
    </div>

    <!-- Thumb -->
    <div
      v-if="canScroll"
      class="absolute left-1/2 -translate-x-1/2 w-1 bg-[var(--scrollbar-thumb)] opacity-80 rounded-[2px] cursor-pointer touch-none pointer-events-auto transition-[width,opacity] duration-200 hover:w-2 hover:opacity-100 z-20"
      :class="{ 'w-2 opacity-100': isDragging || isHovering }"
      :style="{ height: thumbHeight + 'px', top: animatedThumbTop + 'px' }"
      @mousedown.stop="onThumbMouseDown"
      @mouseenter="isHovering = true"
      @mouseleave="isHovering = false"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useResizeObserver } from '@vueuse/core';

const props = defineProps<{
  currentVisualProgress: number;
  accumulatedOffsets: number[];
  estimatedTotalHeight: number;
  viewportHeight: number;
  markers: Array<{ topPercent: number; label: string; index: number; isEnd?: boolean }>;
}>();

const emit = defineEmits<{
  (e: 'scroll-to-index', index: number): void;
  (e: 'update:currentVisualProgress', value: number): void;
}>();

const isDragging = ref(false);
const isHovering = ref(false);
const anchorRef = ref<HTMLElement | null>(null);

const trackHeight = ref(0);

const updateTrackHeight = () => {
  if (anchorRef.value) {
    trackHeight.value = anchorRef.value.clientHeight;
  }
};

useResizeObserver(anchorRef, updateTrackHeight);

onMounted(() => {
  updateTrackHeight();
});



const canScroll = computed(() => props.estimatedTotalHeight > props.viewportHeight + 1);

const thumbHeight = computed(() => {
  if (!canScroll.value) return 40;
  return 40;
});

const trackRange = computed(() => Math.max(0, trackHeight.value - thumbHeight.value));

const thumbTop = computed(() => {
  if (!canScroll.value) return 0;
  if (trackRange.value <= 0) return 0;
  const p = Math.max(0, Math.min(1, props.currentVisualProgress));
  return p * trackRange.value;
});

const animatedThumbTop = ref(0);
const targetThumbTop = ref(0);
let rafId: number | null = null;

const startTopAnimation = () => {
  if (rafId !== null) return;
  const step = () => {
    rafId = null;
    if (isDragging.value) return;
    const target = targetThumbTop.value;
    const current = animatedThumbTop.value;
    const next = current + (target - current) * 0.22;
    if (Math.abs(target - next) < 0.5) {
      animatedThumbTop.value = target;
      return;
    }
    animatedThumbTop.value = next;
    rafId = requestAnimationFrame(step);
  };
  rafId = requestAnimationFrame(step);
};

watch(thumbTop, (val) => {
  if (isDragging.value) {
    return;
  }
  targetThumbTop.value = val;
  startTopAnimation();
}, { immediate: true });

watch(isDragging, (dragging) => {
  if (dragging) {
    if (rafId !== null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
    return;
  }
  targetThumbTop.value = thumbTop.value;
  startTopAnimation();
});

const markersWithPosition = computed(() => {
  return props.markers.map(marker => {
    const p = Math.max(0, Math.min(1, marker.topPercent / 100));
    const topPx = p * trackRange.value + thumbHeight.value / 2;
    return {
      ...marker,
      topPx
    };
  });
});

const snappedMarkerIndex = ref<number | null>(null);

const updateSnappedMarker = () => {
  if (!isDragging.value || !canScroll.value) {
    snappedMarkerIndex.value = null;
    return;
  }

  const thumbCenterY = animatedThumbTop.value + thumbHeight.value / 2;
  let bestIndex: number | null = null;
  let bestDist = Number.POSITIVE_INFINITY;

  for (const marker of markersWithPosition.value) {
    const d = Math.abs(marker.topPx - thumbCenterY);
    if (d < bestDist) {
      bestDist = d;
      bestIndex = marker.index;
    }
  }

  snappedMarkerIndex.value = bestDist <= 12 ? bestIndex : null;
};

watch([animatedThumbTop, isDragging], updateSnappedMarker, { immediate: true });
watch(() => props.markers, updateSnappedMarker, { deep: true });

// Interaction Logic
let startY = 0;
let startThumbTop = 0;
let pendingMarkerIndex: number | null = null;
let interactionType: 'none' | 'thumb-drag' | 'marker-check' | 'track-drag' = 'none';

// Mouse Down on Track (Jump + Drag)
const onTrackMouseDown = (e: MouseEvent) => {
  if (interactionType !== 'none') return;
  e.preventDefault();
  
  if (!anchorRef.value) return;
  if (!canScroll.value) return;
  const rect = anchorRef.value.getBoundingClientRect();
  const clickY = e.clientY - rect.top;

  const range = trackRange.value;
  const targetTop = Math.max(0, Math.min(range, clickY - thumbHeight.value / 2));
  
  // Start dragging
  interactionType = 'track-drag';
  isDragging.value = true;
  startY = e.clientY;
  startThumbTop = targetTop;
  
  // Immediate update
  animatedThumbTop.value = targetTop;
  
  const targetProgress = range > 0 ? targetTop / range : 0;
  emit('update:currentVisualProgress', targetProgress);
  
  addGlobalListeners();
};

// Mouse Down on Thumb (Drag)
const onThumbMouseDown = (e: MouseEvent) => {
  e.preventDefault();
  e.stopPropagation();
  if (!canScroll.value) return;
  
  interactionType = 'thumb-drag';
  isDragging.value = true;
  startY = e.clientY;
  startThumbTop = animatedThumbTop.value;
  
  addGlobalListeners();
};

// Mouse Down on Marker (Check Click vs Drag)
const onMarkerMouseDown = (e: MouseEvent, index: number) => {
  e.preventDefault();
  e.stopPropagation();
  
  interactionType = 'marker-check';
  pendingMarkerIndex = index;
  startY = e.clientY;
  startThumbTop = animatedThumbTop.value;
  
  addGlobalListeners();
};

const onGlobalMouseMove = (e: MouseEvent) => {
  const deltaY = e.clientY - startY;
  
  if (interactionType === 'marker-check') {
    if (Math.abs(deltaY) > 3) {
      interactionType = 'thumb-drag'; 
      isDragging.value = true;
      pendingMarkerIndex = null; 
    }
  }
  
  if (interactionType === 'thumb-drag' || interactionType === 'track-drag') {
    e.preventDefault();
    
    // Calculate new visual progress
    const range = Math.max(1, trackRange.value);
    let newTop = startThumbTop + deltaY;
    newTop = Math.max(0, Math.min(range, newTop));
    
    // Drive by absolute mouse position
    animatedThumbTop.value = newTop;
    
    const newProgress = newTop / range;
    emit('update:currentVisualProgress', newProgress);
  }
};

const onGlobalMouseUp = (e: MouseEvent) => {
  if (interactionType === 'marker-check' && pendingMarkerIndex !== null) {
    emit('scroll-to-index', pendingMarkerIndex);
  } else if ((interactionType === 'thumb-drag' || interactionType === 'track-drag') && snappedMarkerIndex.value !== null) {
    emit('scroll-to-index', snappedMarkerIndex.value);
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
  if (rafId !== null) {
    cancelAnimationFrame(rafId);
    rafId = null;
  }
  removeGlobalListeners();
});
</script>

<style scoped>
/* Scoped styles if needed */
</style>
