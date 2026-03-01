<template>
  <div class="w-full bg-white border-t border-slate-200 px-6 py-3 flex items-center gap-4 select-none">
    <!-- Play/Pause Button -->
    <button 
      @click="togglePlay"
      class="w-10 h-10 rounded-full bg-brand-primary text-white flex items-center justify-center hover:bg-brand-gradient-end transition-all shadow-md shrink-0"
    >
      <svg v-if="!isPlaying" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" stroke="none">
        <path d="M8 5v14l11-7z"/>
      </svg>
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor" stroke="none">
        <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
      </svg>
    </button>

    <!-- Time Display -->
    <div class="text-xs font-mono text-slate-500 w-24 text-center shrink-0">
      {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
    </div>

    <!-- Progress Bar -->
    <div class="flex-1 relative group h-8 flex items-center">
      <!-- Background Track -->
      <div class="absolute inset-x-0 h-1 bg-slate-200 rounded-full overflow-hidden">
        <!-- Buffered -->
        <div class="h-full bg-slate-300 transition-all duration-200" :style="{ width: bufferedPercentage + '%' }"></div>
      </div>
      <!-- Progress -->
      <div class="absolute left-0 h-1 bg-brand-primary rounded-full" :style="{ width: progressPercentage + '%' }"></div>
      
      <!-- Scrubber Input -->
      <input 
        type="range" 
        min="0" 
        :max="duration" 
        step="0.1"
        :value="currentTime"
        @input="onSeek"
        class="absolute inset-x-0 w-full h-full opacity-0 cursor-pointer z-10"
      />
      
      <!-- Thumb (Visual only) -->
      <div 
        class="absolute h-3 w-3 bg-white border-2 border-brand-primary rounded-full shadow-sm pointer-events-none transform -translate-x-1/2 transition-transform duration-75"
        :style="{ left: progressPercentage + '%' }"
      ></div>
    </div>

    <!-- Speed Control -->
    <div class="relative shrink-0">
      <button 
        @click="showSpeedMenu = !showSpeedMenu"
        class="px-2 py-1 rounded text-xs font-medium text-slate-600 hover:bg-slate-100 transition-colors w-12 text-center"
      >
        {{ playbackRate }}x
      </button>
      
      <!-- Speed Menu -->
      <div 
        v-if="showSpeedMenu"
        class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-white rounded-lg shadow-xl border border-slate-100 py-1 min-w-[80px] z-50 animate-[fadeIn_0.1s_ease-out]"
      >
        <button 
          v-for="rate in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]" 
          :key="rate"
          @click="changeSpeed(rate)"
          class="block w-full px-3 py-1.5 text-xs text-left hover:bg-slate-50 transition-colors"
          :class="{ 'text-brand-primary font-bold bg-brand-primary/5': rate === playbackRate, 'text-slate-700': rate !== playbackRate }"
        >
          {{ rate }}x
        </button>
      </div>
      <!-- Backdrop to close menu -->
      <div v-if="showSpeedMenu" class="fixed inset-0 z-40" @click="showSpeedMenu = false"></div>
    </div>

    <!-- Hidden Audio Element -->
    <audio 
      ref="audio" 
      :src="src" 
      @timeupdate="onTimeUpdate" 
      @loadedmetadata="onLoadedMetadata" 
      @ended="onEnded" 
      @progress="onProgress"
    ></audio>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';

const props = defineProps({
  src: String,
  seekTime: Number // Prop to control seeking from parent
});

const emit = defineEmits(['timeupdate']);

const audio = ref(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const buffered = ref(0);
const playbackRate = ref(1.0);
const showSpeedMenu = ref(false);

const progressPercentage = computed(() => {
  if (!duration.value) return 0;
  return (currentTime.value / duration.value) * 100;
});

const bufferedPercentage = computed(() => {
  if (!duration.value) return 0;
  return (buffered.value / duration.value) * 100;
});

// Watch for external seek requests
watch(() => props.seekTime, (newVal) => {
  if (newVal !== undefined && audio.value) {
    audio.value.currentTime = newVal;
    if (!isPlaying.value) {
        audio.value.play();
        isPlaying.value = true;
    }
  }
});

// Watch for src changes to reset state
watch(() => props.src, () => {
    if (audio.value) {
        audio.value.load();
        currentTime.value = 0;
        duration.value = 0;
        buffered.value = 0;
        isPlaying.value = false;
    }
});

const togglePlay = async () => {
    if (!audio.value) return;
    try {
        if (audio.value.paused) {
            await audio.value.play();
            isPlaying.value = true;
        } else {
            audio.value.pause();
            isPlaying.value = false;
        }
    } catch (err) {
        console.error("Playback failed:", err);
    }
};

const onSeek = (e) => {
    const time = parseFloat(e.target.value);
    if (audio.value) {
        audio.value.currentTime = time;
        currentTime.value = time;
    }
};

const changeSpeed = (rate) => {
    playbackRate.value = rate;
    if (audio.value) {
        audio.value.playbackRate = rate;
    }
    showSpeedMenu.value = false;
};

const onTimeUpdate = () => {
    if (!audio.value) return;
    currentTime.value = audio.value.currentTime;
    // Handle infinite duration (streaming) or NaN
    if (isFinite(audio.value.duration)) {
        duration.value = audio.value.duration;
    }
    emit('timeupdate', currentTime.value);
};

const onProgress = () => {
    if (audio.value && audio.value.buffered.length > 0) {
        buffered.value = audio.value.buffered.end(audio.value.buffered.length - 1);
    }
};

const onLoadedMetadata = () => {
    if (audio.value) {
        duration.value = audio.value.duration;
        audio.value.playbackRate = playbackRate.value;
    }
};

const onEnded = () => {
    isPlaying.value = false;
    currentTime.value = 0;
};

const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return "00:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
};

const skip = (seconds) => {
    if (!audio.value) return;
    audio.value.currentTime = Math.max(0, Math.min(duration.value || 0, audio.value.currentTime + seconds));
};

onMounted(() => {
    window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown);
});

const handleKeydown = (e) => {
    if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
    
    if (e.code === 'Space') {
        e.preventDefault();
        togglePlay();
    } else if (e.code === 'ArrowLeft') {
        skip(-5);
    } else if (e.code === 'ArrowRight') {
        skip(5);
    }
};
</script>