<template>
  <div
    class="inline-flex items-center gap-3 px-3 py-2 my-1 rounded-lg border bg-card text-card-foreground shadow-sm hover:shadow hover:border-primary/40 hover:bg-muted/40 cursor-pointer transition-all duration-200 group w-fit max-w-full align-middle"
    @click="handleClick"
    title="点击预览文档"
  >
    <!-- PDF Icon -->
    <div class="flex items-center justify-center w-8 h-8 rounded-md dark:bg-red-950/40  dark:border-red-800/50 shrink-0">
      <svg class="w-7 h-7" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="#ef4444" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M14 2V8H20" stroke="#ef4444" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        <text x="7" y="17.5" font-family="Arial, sans-serif" font-size="5.5" font-weight="700" fill="#ef4444" letter-spacing="0.3">PDF</text>
      </svg>
    </div>

    <!-- Info -->
    <div class="flex flex-col min-w-0">
      <span class="text-sm font-medium text-foreground truncate max-w-[240px]" :title="displayTitle">
        {{ displayTitle }}
      </span>
      <div class="flex items-center gap-2 mt-0.5">
        <span class="text-[11px] text-muted-foreground font-mono">doc#{{ docId }}</span>
        <span v-if="createdAt" class="text-[11px] text-muted-foreground">· {{ createdAt }}</span>
        <span v-else-if="loading" class="text-[11px] text-muted-foreground/50">加载中...</span>
      </div>
    </div>
<ChevronRight class="w-4 h-4 text-muted-foreground/40 group-hover:text-primary/60 transition-colors shrink-0 ml-1" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ChevronRight } from 'lucide-vue-next';
import { knowledgeService } from '@/features/llm-chat/shared/services/knowledgeService';

const props = defineProps<{
  docId: string;
  title: string;
}>();

const emit = defineEmits<{
  (e: 'click', docId: string): void;
}>();

const loading = ref(false);
const fetchedFilename = ref<string | null>(null);
const rawCreatedAt = ref<string | null>(null);

const displayTitle = computed(() => fetchedFilename.value ?? props.title);

const createdAt = computed(() => {
  if (!rawCreatedAt.value) return null;
  try {
    return new Date(rawCreatedAt.value).toLocaleDateString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit'
    });
  } catch {
    return null;
  }
});

onMounted(async () => {
  loading.value = true;
  try {
    const meta = await knowledgeService.getDocMeta(props.docId);
    fetchedFilename.value = meta.filename ?? null;
    rawCreatedAt.value = meta.created_at ?? null;
  } catch {
    // silently fall back to props.title
  } finally {
    loading.value = false;
  }
});

const handleClick = () => emit('click', props.docId);
</script>
