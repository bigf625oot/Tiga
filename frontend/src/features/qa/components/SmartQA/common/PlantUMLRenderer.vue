<template>
  <div class="plantuml-container my-4 p-4 bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800 flex justify-center overflow-x-auto relative">
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-zinc-900/50 z-10">
      <Loader2 class="w-6 h-6 animate-spin text-zinc-500" />
    </div>
    <img 
      v-if="imageUrl" 
      :src="imageUrl" 
      alt="PlantUML Diagram" 
      class="max-w-full h-auto"
      @load="loading = false"
      @error="handleError"
    />
    <div v-if="error" class="text-red-500 text-sm p-2 bg-red-50 dark:bg-red-950/30 rounded w-full text-left font-mono whitespace-pre-wrap">
      Failed to load PlantUML diagram.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import plantumlEncoder from 'plantuml-encoder';
import { Loader2 } from 'lucide-vue-next';

const props = defineProps<{
  code: string;
}>();

const imageUrl = ref<string>('');
const loading = ref(true);
const error = ref(false);

const generateUrl = () => {
  if (!props.code) return;
  loading.value = true;
  error.value = false;
  try {
    const encoded = plantumlEncoder.encode(props.code.trim());
    imageUrl.value = `https://www.plantuml.com/plantuml/svg/${encoded}`;
  } catch (err) {
    console.error('PlantUML encoding failed:', err);
    error.value = true;
    loading.value = false;
  }
};

const handleError = () => {
  error.value = true;
  loading.value = false;
};

onMounted(generateUrl);
watch(() => props.code, generateUrl);
</script>