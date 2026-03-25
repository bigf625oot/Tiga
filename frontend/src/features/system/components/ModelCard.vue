<template>
  <Card 
    class="group relative overflow-hidden transition-all duration-300 cursor-pointer flex flex-col h-full min-h-[180px] border-muted hover:shadow-lg hover:border-primary/40 bg-gradient-to-br from-card to-muted/10 hover:-translate-y-1"
    @click="$emit('edit', item)"
  >
    
    <div class="p-5 pb-3 flex gap-4">
      <!-- Icon Box -->
      <div 
        class="relative flex-shrink-0 w-12 h-12 rounded-xl border flex items-center justify-center transition-all shadow-sm group-hover:scale-105"
        :class="item.is_active ? 'bg-primary/5 border-primary/10 text-primary' : 'bg-muted/30 border-muted text-muted-foreground'"
      >
        <div v-if="!imageError" class="w-full h-full rounded-xl overflow-hidden bg-white flex items-center justify-center p-1">
            <img 
                :key="providerLogoSrc"
                :src="providerLogoSrc" 
                class="w-full h-full object-contain"
                alt="provider logo"
                @error="imageError = true"
            />
        </div>
        <Bot v-else class="w-6 h-6" />
        
        <!-- Country Flag -->
        <img 
            v-if="providerCountry"
            :src="`/flags/${providerCountry}.svg`" 
            class="absolute -bottom-1 -right-1 w-[18px] h-[13px] rounded-[2px] shadow-sm border border-muted/50 object-cover"
            :alt="providerCountry"
        />
      </div>

      <!-- Title & Info -->
      <div class="flex-1 min-w-0 flex flex-col justify-center">
        <div class="flex justify-between items-start gap-2">
            <h3 class="font-bold text-base truncate leading-tight py-0.5 group-hover:text-primary transition-colors" :title="item.name">{{ item.name }}</h3>
            
            <!-- Menu -->
            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <Button variant="ghost" size="icon" class="h-8 w-8 -mr-2 -mt-1.5 text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100 transition-opacity" @click.stop>
                  <MoreVertical class="h-4 w-4" />
                  <span class="sr-only">Open menu</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" class="w-40">
                <DropdownMenuItem @click="$emit('edit', item)">
                  <Edit2 class="mr-2 h-3.5 w-3.5" />
                  <span>编辑配置</span>
                </DropdownMenuItem>
                <DropdownMenuItem @click="$emit('toggle-status', item)">
                  <Power class="mr-2 h-3.5 w-3.5" />
                  <span>{{ item.is_active ? '禁用模型' : '启用模型' }}</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem @click="$emit('delete', item)" class="text-destructive focus:text-destructive">
                  <Trash2 class="mr-2 h-3.5 w-3.5" />
                  <span>删除模型</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
        </div>
        
        <div class="flex items-center gap-2 mt-1.5">
            <Badge variant="secondary" class="h-5 px-1.5 text-[10px] font-medium border-0 bg-secondary/50 text-secondary-foreground hover:bg-secondary/70 capitalize">
              {{ item.provider }}
            </Badge>
            <Badge variant="outline" class="h-5 px-1.5 text-[10px] font-medium border-primary/20 text-muted-foreground bg-primary/5 capitalize">
              {{ item.model_type }}
            </Badge>
        </div>
      </div>
    </div>

    <!-- Details -->
    <div class="px-5 pb-4 flex-1 space-y-2">
      <div class="text-xs text-muted-foreground/80 flex items-center gap-2" title="Model ID">
        <Cpu class="w-3.5 h-3.5 flex-shrink-0" />
        <span class="font-mono truncate">{{ item.model_id }}</span>
      </div>
      <div v-if="item.base_url" class="text-xs text-muted-foreground/60 flex items-center gap-2" title="Base URL">
        <Globe class="w-3.5 h-3.5 flex-shrink-0" />
        <span class="font-mono truncate">{{ item.base_url }}</span>
      </div>
    </div>

    <!-- Footer Actions -->
    <div class="px-5 pt-0 flex items-center justify-between mt-auto border-t border-border/30 pt-3 pb-5">
        <!-- Status Indicator -->
        <div class="flex items-center gap-2">
            <div class="relative flex h-2 w-2">
              <span v-if="item.is_active" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2" :class="item.is_active ? 'bg-green-500' : 'bg-slate-300'"></span>
            </div>
            <span class="text-[10px] text-muted-foreground font-medium">{{ item.is_active ? '运行中' : '未启用' }}</span>
        </div>

        <!-- Action Button -->
        <Button 
          size="sm"
          class="h-7 text-xs px-3 shadow-sm transition-all active:scale-95 gap-1.5"
          variant="outline"
          @click.stop="$emit('test', item)"
          :disabled="testingId === item.id"
        >
          <Loader2 v-if="testingId === item.id" class="h-3 w-3 animate-spin" />
          <Network v-else class="h-3 w-3" />
          <span>测试</span>
        </Button>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { 
  MoreVertical, 
  Edit2, 
  Trash2, 
  Loader2, 
  Bot,
  Power,
  Cpu,
  Globe,
  Clock,
  Network,
  Zap,
  Box,
  Brain
} from 'lucide-vue-next';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import dayjs from 'dayjs';

const props = defineProps<{
  item: {
    id: number;
    name: string;
    provider: string;
    model_id: string;
    model_type: string;
    is_active: boolean;
    created_at: string;
    base_url?: string;
    [key: string]: any;
  };
  testingId?: number | null;
}>();

defineEmits(['edit', 'delete', 'toggle-status', 'test']);

const imageError = ref(false);
const providerLogoSrc = computed(() => getProviderLogo(props.item.provider));
const providerCountry = computed(() => getProviderCountry(props.item.provider));

watch(
  () => props.item.provider,
  () => {
    imageError.value = false;
  },
  { immediate: true }
);

const formatDate = (date: string) => {
    return dayjs(date).format('YYYY-MM-DD');
};

const getProviderLogo = (provider: string) => {
    const providerMap: Record<string, string> = {
        'openai': 'openai',
        'anthropic': 'anthropic',
        'google': 'google',
        'gemini': 'gemini',
        'aliyun': 'qwen',
        'dashscope': 'qwen',
        'deepseek': 'deepseek',
        'claude': 'claude',
        'aws': 'aws',
        'bedrock': 'bedrock',
        'azure': 'azureai',
        'mistral': 'mistral',
        'groq': 'groq',
        'xai': 'xai',
        'cohere': 'cohere',
        'perplexity': 'perplexity',
        'together': 'together',
        'openrouter': 'openrouter',
        'nvidia': 'nvidia',
        'ollama': 'ollama',
        'fireworks': 'fireworks',
        'nebius': 'nebius',
        'vertexai': 'vertexai'
    };
    const key = provider?.toLowerCase().trim() || '';
    const logoName = providerMap[key] || key;
    return `/flags/llm/${logoName}.svg`;
};

const getProviderCountry = (provider: string) => {
    const countryMap: Record<string, string> = {
        'openai': 'us',
        'anthropic': 'us',
        'google': 'us',
        'gemini': 'us',
        'claude': 'us',
        'aws': 'us',
        'bedrock': 'us',
        'azure': 'us',
        'groq': 'us',
        'xai': 'us',
        'perplexity': 'us',
        'together': 'us',
        'openrouter': 'us',
        'nvidia': 'us',
        'fireworks': 'us',
        'vertexai': 'us',
        'aliyun': 'cn',
        'dashscope': 'cn',
        'deepseek': 'cn'
    };
    const key = provider?.toLowerCase().trim() || '';
    return countryMap[key] || '';
};
</script>
