<template>
  <div 
    ref="containerRef"
    class="relative overflow-hidden rounded-full flex items-center justify-center bg-indigo-50/50"
    :style="{ width: sizePx, height: sizePx }"
  >
    <!-- Loading State -->
    <div 
      v-if="isLoading && shouldLoad" 
      class="absolute inset-0 bg-slate-200 animate-pulse z-10"
    ></div>

    <!-- Image -->
    <img 
      v-if="shouldLoad && !isError && displaySrc"
      :src="displaySrc" 
      :alt="name"
      class="w-full h-full object-cover transition-opacity duration-300"
      :class="{ 'opacity-0': isLoading, 'opacity-100': !isLoading }"
      @load="onLoad"
      @error="onError"
    />

    <!-- Fallback / Error State -->
    <div 
      v-if="isError || (!displaySrc && shouldLoad)" 
      class="w-full h-full flex items-center justify-center text-indigo-500"
    >
       <slot name="fallback">
          <svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-2/3 h-2/3">
             <path d="M8 1L14 4V12L8 15L2 12V4L8 1Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
             <path d="M8 5L11 6.5V9.5L8 11L5 9.5V6.5L8 5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
          </svg>
       </slot>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue';

const props = defineProps({
  src: {
    type: String,
    default: ''
  },
  name: {
    type: String,
    default: 'Agent'
  },
  size: {
    type: [Number, String],
    default: 24
  }
});

const containerRef = ref(null);
const shouldLoad = ref(false);
const isLoading = ref(true);
const isError = ref(false);
const retryCount = ref(0);
const maxRetries = 3;
const displaySrc = ref(props.src);
let retryTimeout = null;
let observer = null;

const sizePx = computed(() => {
  return typeof props.size === 'number' ? `${props.size}px` : props.size;
});

// Watch for src changes
watch(() => props.src, (newVal) => {
  resetState();
  displaySrc.value = newVal;
  // If we are already visible, we start loading immediately
  if (shouldLoad.value) {
    isLoading.value = true;
  }
});

const resetState = () => {
  if (retryTimeout) clearTimeout(retryTimeout);
  isLoading.value = true;
  isError.value = false;
  retryCount.value = 0;
};

const onLoad = () => {
  isLoading.value = false;
  isError.value = false;
};

const onError = () => {
  if (retryCount.value < maxRetries) {
    retryCount.value++;
    retryTimeout = setTimeout(() => {
      if (!props.src) return;
      // Append timestamp/retry count to force reload if it's a network issue
      const separator = props.src.includes('?') ? '&' : '?';
      displaySrc.value = `${props.src}${separator}_retry=${Date.now()}`;
    }, 500); // 500ms delay for retry
  } else {
    isLoading.value = false;
    isError.value = true;
  }
};

onMounted(() => {
  // Setup Intersection Observer for Lazy Loading
  if ('IntersectionObserver' in window) {
    observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        shouldLoad.value = true;
        observer.disconnect();
      }
    }, { rootMargin: '50px' }); // Preload when close
    
    if (containerRef.value) {
      observer.observe(containerRef.value);
    }
  } else {
    // Fallback for no IO support
    shouldLoad.value = true;
  }
});

onBeforeUnmount(() => {
  if (observer) observer.disconnect();
  if (retryTimeout) clearTimeout(retryTimeout);
});
</script>
