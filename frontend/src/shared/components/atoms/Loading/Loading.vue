<template>
  <div v-if="loading" class="w-full h-full flex flex-col justify-center items-center min-h-[200px]">
    <!-- Spinner -->
    <div v-if="type === 'spinner'" class="flex flex-col items-center gap-4">
        <svg class="animate-spin h-8 w-8 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span v-if="text" class="text-muted-foreground text-sm">{{ text }}</span>
    </div>

    <!-- Skeleton List -->
    <div v-else-if="type === 'skeleton-list'" class="w-full space-y-3">
        <Skeleton v-for="i in rows" :key="i" class="h-14 w-full rounded-lg border border-slate-200" />
    </div>

    <!-- Skeleton Card -->
    <div v-else-if="type === 'skeleton-card'" class="w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div v-for="i in rows" :key="i" class="rounded-xl border border-slate-200 bg-card p-4 space-y-3 shadow-sm">
          <div class="flex gap-3">
            <Skeleton class="h-10 w-10 rounded-lg" />
            <div class="space-y-2 flex-1 pt-1">
              <Skeleton class="h-4 w-1/2" />
              <Skeleton class="h-3 w-1/4" />
            </div>
          </div>
          <div class="space-y-2 pt-2">
            <Skeleton class="h-3 w-full" />
            <Skeleton class="h-3 w-5/6" />
          </div>
          <div class="pt-3 border-t flex justify-between items-center">
            <Skeleton class="h-3 w-20" />
            <Skeleton class="h-7 w-16 rounded-md" />
          </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ILoadingProps } from './types';
import { Skeleton } from '@/components/ui/skeleton';

withDefaults(defineProps<ILoadingProps>(), {
  loading: true,
  type: 'spinner',
  text: '加载中...',
  rows: 6
});
</script>
