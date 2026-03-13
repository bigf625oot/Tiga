<template>
  <div class="group relative flex flex-col h-full overflow-hidden border rounded-xl bg-card text-card-foreground shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1">
    <!-- Top Status Accent -->
    <div class="absolute top-0 left-0 w-full h-1" :class="item.is_active ? 'bg-gradient-to-r from-green-500/50 to-green-500/10' : 'bg-gradient-to-r from-muted-foreground/30 to-muted/10'"></div>

    <div class="p-5 flex gap-4">
      <!-- Icon Box -->
      <div 
        class="relative flex-shrink-0 w-12 h-12 rounded-xl border flex items-center justify-center transition-all shadow-sm group-hover:shadow-md group-hover:scale-105"
        :class="item.is_active ? 'bg-primary/5 border-primary/10 text-primary' : 'bg-muted/30 border-muted text-muted-foreground'"
      >
        <div v-if="getProviderCountry(item.provider)" class="w-full h-full rounded-xl overflow-hidden">
            <img 
                :src="`/flags/${getProviderCountry(item.provider)}.svg`" 
                class="w-full h-full object-cover opacity-90"
                alt="country flag"
            />
        </div>
        <Bot v-else class="w-6 h-6" />
        
        <!-- Status Indicator -->
        <span v-if="item.is_active" class="absolute -top-1 -right-1 flex h-2.5 w-2.5">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500 border-2 border-background"></span>
        </span>
      </div>

      <!-- Title & Info -->
      <div class="flex-1 min-w-0 flex flex-col justify-center">
        <div class="flex justify-between items-start gap-2">
            <h3 class="font-bold text-base truncate leading-tight py-0.5 group-hover:text-primary transition-colors" :title="item.name">{{ item.name }}</h3>
            
            <!-- Menu -->
            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <Button variant="ghost" size="icon" class="h-7 w-7 -mr-2 -mt-1.5 text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100 transition-opacity">
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
    <div class="px-5 py-3 bg-muted/30 border-t border-border/50 flex items-center justify-between gap-3 mt-auto">
        <!-- Date -->
        <div class="flex items-center gap-1.5 text-[10px] text-muted-foreground opacity-70">
           <Clock class="w-3 h-3" />
           <span>{{ formatDate(item.created_at) }}</span>
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
          <span>测试连接</span>
        </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
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

const formatDate = (date: string) => {
    return dayjs(date).format('YYYY-MM-DD');
};

const getProviderCountry = (provider: string) => {
    switch (provider) {
        case 'openai':
        case 'anthropic':
        case 'google':
            return 'us';
        case 'aliyun':
        case 'deepseek':
        case 'minimax':
            return 'cn';
        default:
            return null;
    }
};
</script>