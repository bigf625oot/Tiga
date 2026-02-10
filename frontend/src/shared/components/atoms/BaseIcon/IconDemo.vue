<template>
  <div class="p-8 space-y-8 bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-bold mb-6">BaseIcon Demo</h1>

    <!-- Scenario 1: Basic Usage & Sizes -->
    <section class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold mb-4">1. Basic Usage & Sizes</h2>
      <div class="flex items-end gap-4">
        <div class="flex flex-col items-center">
          <BaseIcon icon="mdi:home" size="16" />
          <span class="text-xs mt-2">16px</span>
        </div>
        <div class="flex flex-col items-center">
          <BaseIcon icon="mdi:home" size="24" />
          <span class="text-xs mt-2">24px (Default)</span>
        </div>
        <div class="flex flex-col items-center">
          <BaseIcon icon="mdi:home" size="32" />
          <span class="text-xs mt-2">32px</span>
        </div>
        <div class="flex flex-col items-center">
          <BaseIcon icon="mdi:home" size="48" />
          <span class="text-xs mt-2">48px</span>
        </div>
        <div class="flex flex-col items-center">
          <BaseIcon icon="mdi:home" size="3rem" />
          <span class="text-xs mt-2">3rem</span>
        </div>
      </div>
    </section>

    <!-- Scenario 2: Colors & Themes -->
    <section class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold mb-4">2. Colors & Themes</h2>
      <div class="flex gap-6">
        <BaseIcon icon="mdi:heart" color="red" size="32" />
        <BaseIcon icon="mdi:check-circle" color="#10B981" size="32" />
        <BaseIcon icon="mdi:alert" color="rgb(245, 158, 11)" size="32" />
        <BaseIcon icon="mdi:account" class="text-blue-600 hover:text-blue-800 cursor-pointer transition-colors" size="32" />
      </div>
    </section>

    <!-- Scenario 3: Rotation & Flip -->
    <section class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold mb-4">3. Rotation & Flip</h2>
      <div class="flex gap-6">
        <div class="flex flex-col items-center">
          <BaseIcon icon="mdi:arrow-up" size="32" />
          <span class="text-xs mt-2">0°</span>
        </div>
        <div class="flex flex-col items-center">
          <BaseIcon icon="mdi:arrow-up" :rotate="90" size="32" />
          <span class="text-xs mt-2">90°</span>
        </div>
        <div class="flex flex-col items-center">
          <BaseIcon icon="mdi:arrow-up" :rotate="180" size="32" />
          <span class="text-xs mt-2">180°</span>
        </div>
        <div class="flex flex-col items-center">
          <BaseIcon icon="mdi:thumb-up" flip="horizontal" size="32" />
          <span class="text-xs mt-2">Flip H</span>
        </div>
      </div>
    </section>

    <!-- Scenario 4: Animations (Spin) -->
    <section class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold mb-4">4. Loading & Animations</h2>
      <div class="flex gap-6">
        <BaseIcon icon="mdi:loading" spin size="32" />
        <BaseIcon icon="ei:spinner-3" spin size="32" color="blue" />
        <BaseIcon icon="gg:spinner" spin size="32" color="purple" />
      </div>
    </section>

    <!-- Scenario 5: Error Handling & Fallback -->
    <section class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold mb-4">5. Error Handling & Fallback</h2>
      <div class="flex gap-6 items-center">
        <div class="flex flex-col items-center">
          <BaseIcon icon="invalid:icon-name-123" fallback="mdi:alert-circle" color="red" size="32" />
          <span class="text-xs mt-2">Fallback Icon</span>
        </div>
        <div class="flex flex-col items-center">
          <BaseIcon icon="invalid:icon-name-456" size="32" />
          <span class="text-xs mt-2">Default Error (?)</span>
        </div>
      </div>
    </section>

    <!-- Scenario 6: Performance Test -->
    <section class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold mb-4">6. Performance Test</h2>
      <button @click="runPerfTest" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 mb-4">
        Run Render Test (100 icons)
      </button>
      <div v-if="perfResult" class="text-sm">
        <p>Total Time: {{ perfResult.time }}ms</p>
        <p>Average per icon: {{ perfResult.avg }}ms</p>
      </div>
      <div v-if="showPerfIcons" class="flex flex-wrap gap-1 mt-4">
        <BaseIcon v-for="i in 100" :key="i" icon="mdi:star" size="16" color="gold" />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue';
import BaseIcon from './BaseIcon.vue';

const showPerfIcons = ref(false);
const perfResult = ref<{ time: number; avg: number } | null>(null);

const runPerfTest = async () => {
  showPerfIcons.value = false;
  perfResult.value = null;
  await nextTick();
  
  const start = performance.now();
  showPerfIcons.value = true;
  await nextTick();
  // Wait for a frame or reasonable time for mount, though actual painting is async
  // This measures Vue mount time roughly
  const end = performance.now();
  const time = Math.round(end - start);
  perfResult.value = {
    time,
    avg: time / 100
  };
};
</script>
