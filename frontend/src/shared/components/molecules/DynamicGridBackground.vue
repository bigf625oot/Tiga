<template>
  <div 
    class="relative w-full h-full overflow-hidden transition-all duration-300"
    :class="[containerClass]"
    :style="{ backgroundColor: backgroundColor }"
  >
    <!-- Blobs Layer -->
    <!-- z-0 but rendered first, so it is at the bottom -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none z-0">
      <div
        v-for="(blob, index) in blobs"
        :key="index"
        class="absolute rounded-full filter blur-3xl animate-blob"
        :style="getBlobStyle(blob)"
      ></div>
    </div>

    <!-- Grid Layer -->
    <!-- Rendered after blobs so it sits on top.
         This allows white grid lines to be visible over colored blobs.
    -->
    <div 
      class="absolute inset-0 pointer-events-none z-0"
      :style="gridStyle"
    ></div>

    <!-- Content Slot -->
    <div class="relative z-10 w-full h-full">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
/**
 * DynamicGridBackground.vue
 * 
 * A reusable component that renders a grid background with animated gradient blobs.
 * 
 * Features:
 * - Configurable grid size and color
 * - Animated floating blobs with customizable colors and speed
 * - Responsive layout
 * - Content slot
 */
import { computed, ref, onMounted } from 'vue';

const props = defineProps({
  /** Background color of the container */
  backgroundColor: { type: String, default: '#ffffff' },
  
  /** Size of the grid squares in pixels */
  gridSize: { type: Number, default: 40 },
  
  /** Color of the grid lines */
  gridColor: { type: String, default: 'rgba(241, 245, 249, 1)' }, // slate-100
  
  /** Number of animated blobs */
  blobCount: { type: Number, default: 3 },
  
  /** Array of colors for the blobs */
  blobColors: { 
    type: Array, 
    default: () => ['rgba(224, 231, 255, 0.6)', 'rgba(250, 232, 255, 0.6)', 'rgba(219, 234, 254, 0.6)'] 
    // indigo-100/60, purple-100/60, blue-100/60
  },
  
  /** Base animation speed in seconds */
  animationSpeed: { type: Number, default: 10 },
  
  /** Additional classes for the container */
  containerClass: { type: String, default: '' },
  
  /** Opacity of the blobs (0-1) */
  blobOpacity: { type: Number, default: 0.7 }
});

// Grid Pattern Style
const gridStyle = computed(() => ({
  backgroundImage: `linear-gradient(to right, ${props.gridColor} 1px, transparent 1px), linear-gradient(to bottom, ${props.gridColor} 1px, transparent 1px)`,
  backgroundSize: `${props.gridSize}px ${props.gridSize}px`
}));

// Blob State
const blobs = ref([]);

onMounted(() => {
  // Generate random blobs on mount
  blobs.value = Array.from({ length: props.blobCount }).map(() => {
    return {
      x: Math.random() * 100, // percentage
      y: Math.random() * 100, // percentage
      size: 100 + Math.random() * 150, // px
      color: props.blobColors[Math.floor(Math.random() * props.blobColors.length)],
      duration: props.animationSpeed + Math.random() * 5 - 2.5, // vary speed slightly
      delay: Math.random() * -5, // negative delay to start mid-animation
      scaleRange: 0.8 + Math.random() * 0.4 // scale factor
    };
  });
});

const getBlobStyle = (blob) => ({
  left: `${blob.x}%`,
  top: `${blob.y}%`,
  width: `${blob.size}px`,
  height: `${blob.size}px`,
  backgroundColor: blob.color,
  opacity: props.blobOpacity,
  animationDuration: `${blob.duration}s`,
  animationDelay: `${blob.delay}s`,
  transform: 'translate(-50%, -50%)' // Center anchor
});
</script>

<style scoped>
@keyframes blob {
  0% {
    transform: translate(-50%, -50%) translate(0px, 0px) scale(1);
  }
  33% {
    transform: translate(-50%, -50%) translate(30px, -50px) scale(1.1);
  }
  66% {
    transform: translate(-50%, -50%) translate(-20px, 20px) scale(0.9);
  }
  100% {
    transform: translate(-50%, -50%) translate(0px, 0px) scale(1);
  }
}

.animate-blob {
  animation: blob infinite ease-in-out;
}
</style>
