<script setup lang="ts">
import { ref } from 'vue';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Search, Loader2, FileText, AlertCircle } from 'lucide-vue-next';
import { Card } from '@/components/ui/card';

const props = defineProps<{
  config?: any;
}>();

const query = ref('');
const isLoading = ref(false);
const results = ref<any[]>([]);
const error = ref<string | null>(null);

// Mock retrieval function
// In a real app, this would call an API endpoint
const testRetrieval = async () => {
  if (!query.value.trim()) return;
  
  isLoading.value = true;
  error.value = null;
  results.value = [];
  
  try {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Mock results based on query
    const mockDocs = [
      { 
        content: "Tiga 平台支持实时数据同步（CDC）和批处理（ETL）两种模式。", 
        source: "product_intro.md", 
        score: 0.92 
      },
      { 
        content: "用户可以通过可视化编辑器拖拽节点来构建数据管道。", 
        source: "user_guide.md", 
        score: 0.85 
      },
      { 
        content: "支持的数据源包括 MySQL, PostgreSQL, Kafka, SFTP 等。", 
        source: "integrations.md", 
        score: 0.78 
      },
      {
        content: "知识库检索节点利用 RAG 技术增强 LLM 的回答准确性。",
        source: "rag_features.md",
        score: 0.71
      }
    ];
    
    // Filter and sort mock results
    const threshold = props.config?.score_threshold || 0.0;
    const topK = props.config?.top_k || 3;
    
    // Simple mock search logic: return all if query is generic, else filter randomly
    // For demo purposes, we just return the mock docs sorted by score
    results.value = mockDocs
      .filter(d => d.score >= threshold)
      .slice(0, topK);
      
  } catch (e) {
    error.value = "检索失败，请检查网络连接或知识库配置。";
    console.error(e);
  } finally {
    isLoading.value = false;
  }
};

const reset = () => {
  query.value = '';
  results.value = [];
  error.value = null;
};
</script>

<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <Label class="text-xs font-semibold text-primary flex items-center gap-1">
        <Search class="w-3 h-3" />
        检索测试 (Retrieval Test)
      </Label>
    </div>
    
    <div class="flex gap-2">
      <Input 
        v-model="query" 
        placeholder="输入问题测试召回效果..." 
        class="h-8 text-xs"
        @keyup.enter="testRetrieval"
      />
      <Button 
        size="sm" 
        class="h-8 px-3"
        :disabled="!query || isLoading"
        @click="testRetrieval"
      >
        <Loader2 v-if="isLoading" class="w-3 h-3 animate-spin" />
        <span v-else>测试</span>
      </Button>
      <Button 
        v-if="query || results.length > 0"
        variant="outline" 
        size="icon" 
        class="h-8 w-8 shrink-0"
        title="重置"
        @click="reset"
      >
        <RotateCcw class="w-3 h-3" />
      </Button>
    </div>

    <!-- Results Area -->
    <div v-if="results.length > 0" class="space-y-2 animate-in fade-in slide-in-from-top-2 duration-300">
      <p class="text-[10px] text-muted-foreground">召回结果 (Top {{ results.length }})</p>
      <div class="space-y-2 max-h-[200px] overflow-y-auto pr-1 custom-scrollbar">
        <Card v-for="(doc, i) in results" :key="i" class="p-2 border-l-2 border-l-primary bg-muted/10">
          <div class="flex justify-between items-start mb-1">
            <span class="text-[10px] font-mono text-muted-foreground flex items-center gap-1">
              <FileText class="w-3 h-3" />
              {{ doc.source }}
            </span>
            <span class="text-[10px] font-bold text-primary bg-primary/10 px-1.5 rounded-full">
              {{ doc.score }}
            </span>
          </div>
          <p class="text-xs text-foreground leading-relaxed line-clamp-3">
            {{ doc.content }}
          </p>
        </Card>
      </div>
    </div>

    <div v-else-if="!isLoading && query && results.length === 0 && !error" class="text-center py-4 text-xs text-muted-foreground bg-muted/20 rounded-md">
      未找到相关知识 (No results found)
    </div>

    <div v-if="error" class="flex items-center gap-2 text-xs text-destructive bg-destructive/10 p-2 rounded-md">
      <AlertCircle class="w-3 h-3" />
      {{ error }}
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: hsl(var(--muted));
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--muted-foreground) / 0.5);
}
</style>