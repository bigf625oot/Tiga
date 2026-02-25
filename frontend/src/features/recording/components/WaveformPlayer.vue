<template>
  <div class="flex flex-col h-full bg-slate-50 border-r border-figma-border relative group">
    <!-- Canvas Container -->
    <div class="flex-1 relative w-full h-full overflow-hidden cursor-text select-none" ref="container" @click="seek">
      <canvas ref="canvas" class="w-full h-full block"></canvas>
      
      <!-- Progress Overlay -->
      <div class="absolute top-0 bottom-0 left-0 bg-brand-primary/10 pointer-events-none transition-all duration-75 border-r-2 border-brand-primary" :style="{ width: progress + '%' }"></div>
      
      <!-- Loading State -->
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-slate-50/80 backdrop-blur-sm z-10">
        <div class="flex flex-col items-center">
            <svg class="animate-spin h-8 w-8 text-brand-primary mb-2" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <span class="text-xs text-slate-500 font-medium">加载波形...</span>
        </div>
      </div>
    </div>

    <!-- Controls -->
    <div class="h-16 border-t border-figma-border bg-white flex items-center justify-between px-4 shrink-0 shadow-[0_-2px_10px_rgba(0,0,0,0.02)]">
        <div class="flex items-center gap-4">
            <button @click="togglePlay" class="w-10 h-10 rounded-full flex items-center justify-center bg-brand-primary text-white hover:bg-brand-gradient-end transition-all shadow-lg shadow-brand-primary/30 active:scale-95">
                <svg v-if="isPlaying" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
            </button>
            <div class="flex flex-col">
                <span class="text-sm font-bold font-din text-figma-heading tracking-tight">{{ formatTime(currentTime) }}</span>
                <span class="text-xs font-din text-figma-text-secondary">{{ formatTime(duration) }}</span>
            </div>
        </div>

        <div class="flex items-center gap-2">
            <span class="text-xs text-figma-text-secondary mr-1">倍速</span>
            <div class="flex bg-slate-100 rounded-lg p-0.5">
                <button 
                    v-for="rate in [0.5, 1.0, 1.5, 2.0]" 
                    :key="rate"
                    @click="setSpeed(rate)"
                    :class="['px-2 py-0.5 rounded text-xs font-medium transition-all', playbackRate === rate ? 'bg-white text-brand-primary shadow-sm' : 'text-slate-500 hover:text-slate-700']"
                >
                    {{ rate }}x
                </button>
            </div>
        </div>
    </div>

    <!-- Hidden Audio Element -->
    <audio ref="audio" :src="src" @timeupdate="onTimeUpdate" @loadedmetadata="onLoadedMetadata" @ended="onEnded" crossorigin="anonymous"></audio>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';

const props = defineProps({
  src: String,
});

const emit = defineEmits(['timeupdate']);

const audio = ref(null);
const canvas = ref(null);
const container = ref(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const progress = ref(0);
const loading = ref(false);
const playbackRate = ref(1.0);
let audioContext = null;
let audioBuffer = null;

// Drawing config
const BAR_WIDTH = 3;
const GAP = 2;
const BAR_COLOR = '#D1D5DB'; // gray-300
const ACTIVE_COLOR = '#0052D9'; // brand-primary

const togglePlay = () => {
    if (!audio.value) return;
    if (audio.value.paused) {
        audio.value.play();
        isPlaying.value = true;
    } else {
        audio.value.pause();
        isPlaying.value = false;
    }
};

const setSpeed = (rate) => {
    playbackRate.value = rate;
    if (audio.value) audio.value.playbackRate = rate;
};

const onTimeUpdate = () => {
    if (!audio.value) return;
    currentTime.value = audio.value.currentTime;
    duration.value = audio.value.duration || duration.value;
    progress.value = duration.value ? (currentTime.value / duration.value) * 100 : 0;
    emit('timeupdate', currentTime.value);
};

const onLoadedMetadata = () => {
    if (audio.value) duration.value = audio.value.duration;
};

const onEnded = () => {
    isPlaying.value = false;
    currentTime.value = 0;
    progress.value = 0;
};

const seek = (e) => {
    if (!container.value || !duration.value || !audio.value) return;
    const rect = container.value.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percent = Math.max(0, Math.min(1, x / rect.width));
    audio.value.currentTime = percent * duration.value;
    // If paused, play? No, just seek.
};

const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return "00:00";
    const min = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60);
    return `${min < 10 ? '0' + min : min}:${sec < 10 ? '0' + sec : sec}`;
};

const draw = () => {
    if (!canvas.value || !container.value || !audioBuffer) return;
    
    const ctx = canvas.value.getContext('2d');
    const width = container.value.offsetWidth;
    const height = container.value.offsetHeight;
    
    // Set canvas size for retina
    const dpr = window.devicePixelRatio || 1;
    canvas.value.width = width * dpr;
    canvas.value.height = height * dpr;
    ctx.scale(dpr, dpr);
    
    ctx.clearRect(0, 0, width, height);
    
    const data = audioBuffer.getChannelData(0);
    // Calculate how many bars we can fit
    const numBars = Math.floor(width / (BAR_WIDTH + GAP));
    const step = Math.floor(data.length / numBars);
    const amp = height / 2.5; // Scale factor
    
    ctx.fillStyle = BAR_COLOR;
    
    // Optimization: Use a stride for large steps to avoid freezing UI
    const innerStep = Math.max(1, Math.floor(step / 10)); 

    for (let i = 0; i < numBars; i++) {
        let max = 0;
        const start = i * step;
        
        // Find peak in this chunk
        for (let j = 0; j < step; j += innerStep) {
            const val = Math.abs(data[start + j]);
            if (val > max) max = val;
        }
        
        // Min height 2px
        const h = Math.max(2, max * amp * 2); 
        const x = i * (BAR_WIDTH + GAP);
        const y = (height - h) / 2;
        
        // Rounded Rect
        ctx.beginPath();
        // Use rect for compatibility if roundRect not supported (though modern browsers support it)
        if (ctx.roundRect) {
            ctx.roundRect(x, y, BAR_WIDTH, h, 2);
        } else {
            ctx.rect(x, y, BAR_WIDTH, h);
        }
        ctx.fill();
    }
};

const loadWaveform = async () => {
    if (!props.src) return;
    loading.value = true;
    try {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        const response = await fetch(props.src);
        const arrayBuffer = await response.arrayBuffer();
        audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        nextTick(() => {
            draw();
        });
    } catch (e) {
        console.error("Waveform load failed", e);
    } finally {
        loading.value = false;
    }
};

let resizeObserver = null;

onMounted(() => {
    loadWaveform();
    
    resizeObserver = new ResizeObserver(() => {
        draw();
    });
    if (container.value) {
        resizeObserver.observe(container.value);
    }

    window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
    if (resizeObserver) resizeObserver.disconnect();
    window.removeEventListener('keydown', handleKeydown);
    if (audioContext) audioContext.close();
});

const handleKeydown = (e) => {
    // Only if this component is active/visible (simple check)
    if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
    
    if (e.code === 'Space') {
        e.preventDefault();
        togglePlay();
    } else if (e.code === 'KeyJ') {
        if (audio.value) audio.value.currentTime = Math.max(0, audio.value.currentTime - 5);
    } else if (e.code === 'KeyK') {
        if (audio.value && duration.value) audio.value.currentTime = Math.min(duration.value, audio.value.currentTime + 5);
    }
};

watch(() => props.src, () => {
    loadWaveform();
});
</script>
