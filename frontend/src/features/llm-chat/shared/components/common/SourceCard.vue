<script setup lang="ts">
import { computed } from 'vue';
import { Globe, FileText, File, ExternalLink, Download, Clock, Hash } from 'lucide-vue-next';

interface SourceMeta {
  url?: string;
  title?: string;
  favicon?: string;
  docId?: string | number;
  fileSize?: number;
  updateTime?: string | number;
  score?: number;
  text?: string;
  chunkId?: string | number;
}

const props = withDefaults(defineProps<{
  source: SourceMeta;
  type?: 'web' | 'doc' | 'file';
  showMeta?: boolean;
  showScore?: boolean;
  showExternalIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
}>(), {
  type: 'web',
  showMeta: true,
  showScore: false,
  showExternalIcon: true,
  size: 'md',
});

defineEmits<{
  (e: 'click', source: SourceMeta): void;
  (e: 'locate', source: SourceMeta): void;
}>();

const getDomain = (url: string) => {
  if (!url) return 'Web Link';
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return 'Web Link';
  }
};

const formattedSize = computed(() => {
  if (!props.source.fileSize) return null;
  const size = Number(props.source.fileSize);
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
});

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm': return 'p-2 gap-2';
    case 'lg': return 'p-4 gap-4';
    default: return 'p-3 gap-3';
  }
});

const iconSizeClasses = computed(() => {
  switch (props.size) {
    case 'sm': return 'w-8 h-8';
    case 'lg': return 'w-12 h-12';
    default: return 'w-10 h-10';
  }
});

const titleLines = computed(() => props.size === 'sm' ? 1 : 2);

const cardClickHandler = () => {
  if (props.source.url) {
    window.open(props.source.url, '_blank', 'noopener,noreferrer');
  }
};

const isClickable = computed(() => !!props.source.url);
</script>

<template>
  <article
    class="source-card group relative flex rounded-lg border border-border bg-card text-card-foreground transition-all duration-200 select-none"
    :class="[
      sizeClasses,
      isClickable ? 'cursor-pointer hover:shadow-md hover:border-primary/40 hover:bg-muted/30' : 'cursor-default'
    ]"
    :role="isClickable ? 'link' : 'article'"
    :tabindex="isClickable ? 0 : -1"
    @click="isClickable && cardClickHandler()"
    @keydown.enter="isClickable && cardClickHandler()"
    @keydown.space.prevent="isClickable && cardClickHandler()"
  >
    <a
      v-if="source.url"
      :href="source.url"
      target="_blank"
      rel="noopener noreferrer"
      class="absolute inset-0 z-10"
      :aria-label="source.title || 'Open link in new tab'"
      @click.stop
    />

    <div class="flex items-center gap-3 flex-1 min-w-0 py-0.5">
      <div
        class="flex-shrink-0 rounded-lg flex items-center justify-center overflow-hidden bg-muted border border-border/50"
        :class="iconSizeClasses"
      >
        <img
          v-if="type === 'web' && source.favicon"
          :src="source.favicon"
          class="w-1/2 h-1/2 object-contain"
          loading="lazy"
          :alt="getDomain(source.url || '')"
        />
        <component
          v-else
          :is="type === 'doc' ? FileText : type === 'file' ? File : Globe"
          class="w-1/2 h-1/2 text-muted-foreground"
        />
      </div>

      <div class="flex-1 min-w-0 flex flex-col justify-center">
        <div class="min-w-0">
          <h4
            class="text-sm font-medium text-foreground leading-tight line-clamp-2 group-hover:text-primary transition-colors m-0"
            :class="titleLines === 1 ? 'truncate' : ''"
          >
            {{ source.title || (source.url ? getDomain(source.url) : 'Untitled') }}
          </h4>
        </div>

        <div v-if="showMeta" class="flex items-center flex-wrap gap-x-3 gap-y-1 mt-1.5 text-xs text-muted-foreground">
          <span v-if="type === 'web' && source.url" class="truncate max-w-[150px]">
            {{ getDomain(source.url) }}
          </span>

          <span v-if="source.updateTime" class="flex items-center gap-1">
            <Clock class="w-3 h-3" />
            {{ source.updateTime }}
          </span>

          <span v-if="formattedSize" class="flex items-center gap-1">
            <File class="w-3 h-3" />
            {{ formattedSize }}
          </span>

          <span v-if="showScore && source.score !== undefined" class="flex items-center gap-1">
            <Hash class="w-3 h-3" />
            {{ (source.score * 100).toFixed(0) }}%
          </span>
        </div>
      </div>
    </div>

    <div class="flex-shrink-0 flex items-center gap-2 self-center">
      <div
        v-if="showExternalIcon && isClickable && type === 'web'"
        class="text-muted-foreground/50 group-hover:text-primary transition-colors"
      >
        <ExternalLink class="w-4 h-4" />
      </div>

      <slot name="action" />
    </div>

    <div
      v-if="source.chunkId"
      class="absolute top-1 right-1 w-5 h-5 flex items-center justify-center bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 text-[10px] font-semibold rounded"
    >
      {{ source.chunkId }}
    </div>
  </article>
</template>

<style scoped>
.source-card:focus-visible {
  outline: 2px solid hsl(var(--ring));
  outline-offset: 2px;
}
</style>
