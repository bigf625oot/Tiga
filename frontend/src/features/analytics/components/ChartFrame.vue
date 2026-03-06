<template>
  <div class="w-full h-full relative">
    <iframe
      ref="iframeRef"
      src="/chart-renderer.html"
      class="w-full h-full border-none bg-transparent"
      sandbox="allow-scripts allow-same-origin"
      @load="onLoad"
    ></iframe>
    
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white/50 backdrop-blur-sm">
      <svg class="w-6 h-6 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>
    
    <div v-if="error" class="absolute inset-0 flex flex-col items-center justify-center bg-red-50 text-red-500 p-4 text-center">
      <svg class="w-8 h-8 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
      <span class="text-xs">{{ error }}</span>
      <button @click="retry" class="mt-2 text-xs underline hover:text-red-700">重试</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue';

const props = defineProps({
  option: {
    type: Object,
    required: true
  }
});

const iframeRef = ref(null);
const loaded = ref(false);
const loading = ref(true);
const error = ref(null);

const sendData = () => {
  if (!iframeRef.value || !iframeRef.value.contentWindow || !loaded.value) return;
  
  try {
    iframeRef.value.contentWindow.postMessage({
      type: 'RENDER_CHART',
      data: props.option
    }, '*');
    loading.value = false;
  } catch (e) {
    console.error("Failed to send chart data", e);
    error.value = "图表渲染通信失败";
    loading.value = false;
  }
};

const onLoad = () => {
  loaded.value = true;
  sendData();
};

const retry = () => {
    error.value = null;
    loading.value = true;
    if (iframeRef.value) {
        iframeRef.value.src = iframeRef.value.src; // Reload
    }
};

// Listen for messages from iframe
const handleMessage = (event) => {
    // Ideally check origin
    const { type, success, error: errMsg } = event.data;
    if (type === 'CHART_ERROR') {
        error.value = errMsg || "渲染错误";
        loading.value = false;
    } else if (type === 'CHART_RENDERED') {
        loading.value = false;
    }
};

onMounted(() => {
    window.addEventListener('message', handleMessage);
});

onBeforeUnmount(() => {
    window.removeEventListener('message', handleMessage);
});

watch(() => props.option, () => {
  loading.value = true;
  error.value = null;
  sendData();
}, { deep: true });

</script>
