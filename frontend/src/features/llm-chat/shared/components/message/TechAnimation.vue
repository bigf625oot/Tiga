<template>
  <div class="tech-animation-container" :style="{ width: width + 'px', height: height + 'px' }">
    <Vue3Lottie
      :animationData="animationData"
      :height="height"
      :width="width"
      :loop="true"
      :autoPlay="true"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Vue3Lottie } from 'vue3-lottie';
import { useTheme } from '@/composables/useTheme';
import robotAnimationData from '@/assets/data.json';

const props = defineProps({
  width: {
    type: Number,
    default: 200
  },
  height: {
    type: Number,
    default: 200
  }
});

const { isLightMode } = useTheme();

// 使用 computed 根据主题切换动画链接
// 如果有深色/浅色不同的动画，可以在这里判断 isLightMode.value 返回不同的 JSON 数据
const animationData = computed(() => {
  return robotAnimationData;
});

</script>

<style scoped>
.tech-animation-container {
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
