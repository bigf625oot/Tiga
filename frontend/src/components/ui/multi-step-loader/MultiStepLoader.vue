<template>
  <div class="flex flex-col justify-center items-start gap-4 w-full max-w-lg">
    <div 
      v-for="(state, index) in loadingStates" 
      :key="index"
      class="flex items-center gap-3 transition-all duration-500"
      :class="[
        index === currentState 
          ? 'opacity-100 scale-100' 
          : index < currentState 
            ? 'opacity-50 scale-95' 
            : 'opacity-30 scale-90 blur-sm'
      ]"
    >
      <!-- Icon/Status Indicator -->
      <div class="relative flex items-center justify-center w-6 h-6">
        <transition name="scale" mode="out-in">
          <!-- Completed -->
          <div v-if="index < currentState" class="text-primary">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle-check-big"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>
          </div>
          <!-- Current -->
          <div v-else-if="index === currentState" class="text-primary">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-loader-circle animate-spin"><path d="M21 12a9 9 0 1 1-6.21-10.47"/></svg>
          </div>
          <!-- Pending -->
          <div v-else class="text-muted-foreground/40">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle"><circle cx="12" cy="12" r="10"/></svg>
          </div>
        </transition>
      </div>

      <!-- Text -->
      <span 
        class="text-sm font-medium"
        :class="[
          index === currentState ? 'text-foreground' : 'text-muted-foreground'
        ]"
      >
        {{ state.text }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';

const props = defineProps<{
  loadingStates: { text: string }[];
  loading?: boolean;
  duration?: number;
  loop?: boolean;
}>();

const currentState = ref(0);
let interval: any = null;

const startAnimation = () => {
  if (interval) clearInterval(interval);
  currentState.value = 0;
  
  interval = setInterval(() => {
    if (currentState.value < props.loadingStates.length - 1) {
      currentState.value++;
    } else {
      if (props.loop) {
        currentState.value = 0;
      } else {
        clearInterval(interval);
      }
    }
  }, props.duration || 2000);
};

watch(() => props.loading, (newVal) => {
  if (newVal) {
    startAnimation();
  } else {
    if (interval) clearInterval(interval);
    currentState.value = 0;
  }
}, { immediate: true });

onUnmounted(() => {
  if (interval) clearInterval(interval);
});
</script>

<style scoped>
.scale-enter-active,
.scale-leave-active {
  transition: all 0.3s ease;
}

.scale-enter-from,
.scale-leave-to {
  opacity: 0;
  transform: scale(0.5);
}
</style>
