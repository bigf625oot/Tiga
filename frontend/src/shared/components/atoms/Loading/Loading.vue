<template>
  <div v-if="loading" class="w-full h-full flex flex-col justify-center items-center min-h-[200px]">
    <!-- Spinner -->
    <div v-if="type === 'spinner'" class="flex flex-col items-center gap-3">
        <svg class="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span v-if="text" class="text-slate-400 text-sm">{{ text }}</span>
    </div>

    <!-- Skeleton List -->
    <div v-else-if="type === 'skeleton-list'" class="w-full space-y-3 animate-pulse">
        <div v-for="i in rows" :key="i" class="h-14 bg-slate-100 rounded-xl w-full border border-slate-200"></div>
    </div>

    <!-- Skeleton Card -->
    <div v-else-if="type === 'skeleton-card'" class="w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 animate-pulse">
        <div v-for="i in rows" :key="i" class="h-40 bg-slate-100 rounded-2xl w-full border border-slate-200"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ILoadingProps } from './types';

withDefaults(defineProps<ILoadingProps>(), {
  loading: true,
  type: 'spinner',
  text: '加载中...',
  rows: 6
});
</script>
