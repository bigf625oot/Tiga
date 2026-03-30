<template>
  <div class="media-block-renderer my-4 max-w-full overflow-hidden rounded-lg border bg-card text-card-foreground shadow-sm">
    <!-- Header -->
    <div class="flex items-center gap-2 px-4 py-2 border-b bg-muted/30">
      <component :is="mediaIcon" class="h-4 w-4 text-primary" />
      <span class="text-sm font-medium">{{ block.name || defaultTitle }}</span>
      <Badge v-if="block.duration" variant="secondary" class="ml-auto text-[10px]">
        {{ formatDuration(block.duration) }}
      </Badge>
    </div>

    <!-- Content -->
    <div class="p-0 relative flex justify-center bg-black/5">
      <template v-if="block.media_type === 'video'">
        <video 
          :src="block.url" 
          :poster="block.cover_url"
          controls 
          class="max-h-[400px] w-full object-contain bg-black"
          controlsList="nodownload"
        >
          您的浏览器不支持视频播放。
        </video>
      </template>
      <template v-else-if="block.media_type === 'audio'">
        <div class="w-full p-6 flex flex-col items-center gap-4">
          <div v-if="block.cover_url" class="w-24 h-24 rounded-full overflow-hidden border-4 border-background shadow-md">
            <img :src="block.cover_url" class="w-full h-full object-cover" alt="cover" />
          </div>
          <audio 
            :src="block.url" 
            controls 
            class="w-full max-w-md"
          >
            您的浏览器不支持音频播放。
          </audio>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Film, Music } from 'lucide-vue-next';
import { Badge } from '@/components/ui/badge';
import type { MediaBlock } from '@/features/llm-chat/shared/types';

const props = defineProps<{
  block: MediaBlock;
}>();

const mediaIcon = computed(() => {
  return props.block.media_type === 'video' ? Film : Music;
});

const defaultTitle = computed(() => {
  return props.block.media_type === 'video' ? '视频内容' : '音频内容';
});

const formatDuration = (seconds: number) => {
  if (!seconds) return '';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
};
</script>

<style scoped>
.media-block-renderer {
  transition: all 0.2s ease-in-out;
}
</style>
