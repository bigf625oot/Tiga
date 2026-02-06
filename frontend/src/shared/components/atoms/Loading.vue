<template>
  <div class="flex items-center justify-center p-4">
    <div v-if="type === 'skeleton-card'" class="w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="i in 3" :key="i" class="h-40 bg-slate-100 rounded-xl animate-pulse"></div>
    </div>
    <div v-else-if="type === 'skeleton-list'" class="w-full space-y-3">
        <div v-for="i in 5" :key="i" class="h-12 bg-slate-50 rounded-lg animate-pulse"></div>
    </div>
    <div v-else class="flex flex-col items-center gap-2">
        <svg class="animate-spin h-8 w-8 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span class="text-slate-500 text-sm">Loading...</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: 'spinner' // spinner, skeleton-card, skeleton-list
  }
})
</script>
