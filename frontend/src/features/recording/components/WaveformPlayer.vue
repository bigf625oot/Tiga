<template>
  <div class="w-full bg-background border-t border-border px-4 py-3 flex items-center gap-4 select-none shadow-sm">
    <!-- Play/Pause Button -->
    <Button 
      variant="ghost" 
      size="icon" 
      class="h-10 w-10 rounded-full hover:bg-muted text-primary hover:text-primary/90 transition-colors shrink-0"
      @click="togglePlay"
    >
      <Play v-if="!isPlaying" class="h-6 w-6 fill-current" />
      <Pause v-else class="h-6 w-6 fill-current" />
    </Button>

    <!-- Time Display -->
    <div class="text-xs font-mono text-muted-foreground w-24 text-center shrink-0 tabular-nums">
      {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
    </div>

    <!-- Progress Slider -->
    <div class="flex-1 relative flex items-center min-w-0">
      <Slider
        v-model="sliderValue"
        :max="duration"
        :step="0.1"
        class="w-full cursor-pointer"
        @valueCommit="onSeekCommit"
      />
    </div>

    <!-- Speed Control -->
    <DropdownMenu>
      <DropdownMenuTrigger as-child>
        <Button variant="ghost" size="sm" class="h-8 px-2 text-xs font-medium text-muted-foreground hover:text-foreground w-16 shrink-0">
          {{ playbackRate }}x
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" class="min-w-[80px]">
        <DropdownMenuItem 
          v-for="rate in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]" 
          :key="rate"
          @click="changeSpeed(rate)"
          :class="{ 'bg-accent text-accent-foreground': rate === playbackRate }"
        >
          {{ rate }}x
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>

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
import { Play, Pause } from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const props = defineProps({
  src: String,
  seekTime: Number
});

const emit = defineEmits(['timeupdate']);

const audio = ref(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const playbackRate = ref(1.0);
const isDragging = ref(false);

const sliderValue = computed({
  get: () => [currentTime.value],
  set: (val) => {
    isDragging.value = true;
    if (val && val.length > 0) {
        currentTime.value = val[0];
    }
  }
});

const onSeekCommit = (val) => {
    isDragging.value = false;
    if (val && val.length > 0) {
        const time = val[0];
        if (audio.value) {
            audio.value.currentTime = time;
        }
    }
};

watch(() => props.seekTime, (newVal) => {
  if (newVal !== undefined && audio.value) {
    audio.value.currentTime = newVal;
    if (!isPlaying.value) {
        audio.value.play();
        isPlaying.value = true;
    }
  }
});

watch(() => props.src, () => {
    if (audio.value) {
        audio.value.load();
        currentTime.value = 0;
        duration.value = 0;
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

const changeSpeed = (rate) => {
    playbackRate.value = rate;
    if (audio.value) {
        audio.value.playbackRate = rate;
    }
};

const onTimeUpdate = () => {
    if (!audio.value || isDragging.value) return;
    currentTime.value = audio.value.currentTime;
    if (isFinite(audio.value.duration)) {
        duration.value = audio.value.duration;
    }
    emit('timeupdate', currentTime.value);
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

const onProgress = () => {
    // Optional: Add buffering visualization if needed
};

// Keyboard shortcuts
const skip = (seconds) => {
    if (!audio.value) return;
    audio.value.currentTime = Math.max(0, Math.min(duration.value || 0, audio.value.currentTime + seconds));
};

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

onMounted(() => {
    window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown);
});
</script>
