<template>
  <div class="error-callout w-full my-2">
    <Alert variant="destructive" class="bg-destructive/10 border-destructive/20 relative">
      <AlertCircle class="w-4 h-4" />
      <div class="flex flex-col gap-2">
        <div>
          <AlertTitle class="text-sm font-semibold mb-1">{{ title || '出错了' }}</AlertTitle>
          <AlertDescription class="text-xs text-destructive/90 whitespace-pre-wrap leading-relaxed">
            {{ message }}
          </AlertDescription>
        </div>
        
        <div v-if="canRetry" class="mt-1">
          <Button 
            variant="outline" 
            size="sm" 
            class="h-7 text-xs border-destructive/30 hover:bg-destructive/20 text-destructive font-medium"
            @click="$emit('retry')"
          >
            <RefreshCcw class="w-3 h-3 mr-1.5" />
            重试
          </Button>
        </div>
      </div>
    </Alert>
  </div>
</template>

<script setup lang="ts">
import { AlertCircle, RefreshCcw } from 'lucide-vue-next';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

defineProps<{
  title?: string;
  message: string;
  canRetry?: boolean;
}>();

defineEmits(['retry']);
</script>