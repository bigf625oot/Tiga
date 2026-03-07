<script setup lang="ts">
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

interface Props {
  rows?: number // Just for interface compatibility if needed, though card is fixed
  height?: string
  animated?: boolean
}

withDefaults(defineProps<Props>(), {
  animated: true
})
</script>

<template>
  <Card class="overflow-hidden flex flex-col justify-between h-full group transition-all duration-300">
    <CardContent class="p-6">
      <!-- Header -->
      <div class="flex justify-between items-start mb-4">
        <div class="flex items-center gap-4 w-full">
          <Skeleton class="w-12 h-12 rounded-lg shrink-0" />
          <div class="space-y-2 flex-1 min-w-0">
            <Skeleton class="h-5 w-3/4 rounded" />
            <div class="flex items-center gap-1.5 mt-1">
              <Skeleton class="w-1.5 h-1.5 rounded-full" />
              <Skeleton class="h-3 w-16 rounded" />
            </div>
          </div>
        </div>
      </div>

      <!-- Metrics Placeholder -->
      <!-- Simulate the grid layout in real card -->
      <div class="grid grid-cols-2 gap-4 mb-4">
        <div>
          <Skeleton class="h-3 w-12 mb-1 rounded" />
          <Skeleton class="h-6 w-16 rounded" />
        </div>
        <div>
          <Skeleton class="h-3 w-12 mb-1 rounded" />
          <Skeleton class="h-6 w-16 rounded" />
        </div>
      </div>

      <!-- Bottom Placeholder -->
      <div class="flex justify-between items-end mb-4">
        <Skeleton class="h-3 w-16 rounded" />
        <Skeleton class="h-5 w-20 rounded" />
      </div>
    </CardContent>

    <!-- Footer Actions -->
    <CardFooter class="p-0 border-t bg-muted/10 h-9 flex">
      <div class="flex-1 flex items-center justify-center border-r border-border h-full">
        <Skeleton class="h-3 w-12 rounded" />
      </div>
      <div class="flex-1 flex items-center justify-center h-full">
        <Skeleton class="h-3 w-12 rounded" />
      </div>
    </CardFooter>
  </Card>
</template>
