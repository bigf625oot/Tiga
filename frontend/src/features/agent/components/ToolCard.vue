<template>
  <Card class="group hover:shadow-lg transition-all duration-300 flex flex-col h-[280px] overflow-hidden border-border bg-card text-card-foreground">
    <CardHeader class="p-6 pb-2 space-y-0 flex flex-row gap-4 items-start">
      <!-- Icon -->
      <div 
        v-if="item.iconUrl" 
        class="relative flex-shrink-0 w-12 h-12 bg-muted rounded-lg p-0.5 group-hover:scale-105 transition-transform duration-300 flex items-center justify-center"
      >
        <img :src="item.iconUrl" class="w-full h-full object-contain" alt="icon" />
        <!-- Status Indicator -->
        <span v-if="item.is_active !== false" class="absolute -bottom-1 -right-1 flex h-3 w-3">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-3 w-3 bg-green-500 border-2 border-background"></span>
        </span>
      </div>
      
      <div 
        v-else 
        class="relative flex-shrink-0 w-12 h-12 flex items-center justify-center text-xl font-bold text-muted-foreground bg-muted rounded-lg border border-border shadow-sm group-hover:scale-105 transition-transform duration-300"
      >
        {{ item.icon || item.name.charAt(0).toUpperCase() }}
        <!-- Status Indicator -->
        <span v-if="item.is_active !== false" class="absolute -bottom-1 -right-1 flex h-3 w-3">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-3 w-3 bg-green-500 border-2 border-background"></span>
        </span>
      </div>

      <div class="flex-1 min-w-0 space-y-1">
        <div class="flex justify-between items-start">
          <CardTitle class="text-base font-semibold leading-tight truncate group-hover:text-primary transition-colors py-0.5" :title="item.name">
            {{ item.name }}
          </CardTitle>

          <!-- Menu Trigger -->
          <div v-if="!item.is_official" class="-mr-2 -mt-1 ml-2">
            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <Button variant="ghost" size="icon" class="h-8 w-8 text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                  <MoreVertical class="h-4 w-4" />
                  <span class="sr-only">Open menu</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" class="w-32">
                <DropdownMenuItem @click="$emit('edit', item)">
                  <Edit class="mr-2 h-3.5 w-3.5" />
                  <span>编辑配置</span>
                </DropdownMenuItem>
                <DropdownMenuItem @click="$emit('delete', item)" class="text-destructive focus:text-destructive">
                  <Trash2 class="mr-2 h-3.5 w-3.5" />
                  <span>移除工具</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        <!-- Tags -->
        <div class="flex flex-wrap items-center gap-2">
          <Badge :variant="item.type === 'mcp' ? 'secondary' : 'outline'" class="text-[10px] uppercase tracking-wide">
            {{ item.type === 'mcp' ? 'MCP' : 'Skill' }}
          </Badge>
          <Badge v-if="item.is_official" variant="secondary" class="bg-primary/10 text-primary border-primary/20 gap-1 text-[10px]">
            <CheckCircle2 class="w-3 h-3" />
            官方认证
          </Badge>
        </div>
      </div>
    </CardHeader>

    <CardContent class="p-6 pt-2 flex-1 min-h-0">
      <CardDescription class="text-xs leading-relaxed line-clamp-3 h-[4.5em]" :title="item.description">
        {{ item.description || '暂无描述信息' }}
      </CardDescription>
    </CardContent>

    <CardFooter class="p-6 pt-0 mt-auto flex flex-col gap-4 border-t border-border/50 pt-4">
      <div class="w-full flex items-center justify-between text-[11px] text-muted-foreground">
        <div class="flex items-center gap-1.5">
          <div class="w-5 h-5 rounded-full bg-muted flex items-center justify-center text-[10px] font-semibold text-muted-foreground/70">
            {{ item.author ? item.author.charAt(0).toUpperCase() : 'U' }}
          </div>
          <span class="truncate max-w-[80px]" :title="item.author">@{{ item.author }}</span>
        </div>
        <div class="flex items-center gap-3">
          <span v-if="item.downloads" class="flex items-center gap-1" title="下载量">
            <Download class="w-3 h-3" />
            {{ item.downloads }}k
          </span>
          <span class="bg-muted px-1.5 py-0.5 rounded text-muted-foreground font-mono text-[10px]">v{{ item.version }}</span>
        </div>
      </div>

      <Button 
        class="w-full h-9 text-xs font-medium"
        :variant="getButtonVariant(item)"
        :disabled="item.installed || item.isInstalling || (item.is_active === false)"
        @click.stop="$emit('install', item)"
      >
        <template v-if="item.isInstalling">
          <Loader2 class="mr-2 h-3.5 w-3.5 animate-spin" />
          安装中...
        </template>
        <template v-else-if="item.installed">
          <Check class="mr-2 h-3.5 w-3.5" />
          已安装
        </template>
        <template v-else-if="item.is_active === false">
          <AlertCircle class="mr-2 h-3.5 w-3.5" />
          不可用
        </template>
        <template v-else>
          <Plus class="mr-2 h-3.5 w-3.5" />
          获取工具
        </template>
      </Button>
    </CardFooter>
  </Card>
</template>

<script setup lang="ts">
import { 
  MoreVertical, 
  Edit, 
  Trash2, 
  Download, 
  CheckCircle2, 
  Loader2, 
  Check, 
  AlertCircle, 
  Plus 
} from 'lucide-vue-next';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const props = defineProps<{
  item: {
    id: string;
    name: string;
    description?: string;
    type: 'mcp' | 'skill';
    version: string;
    author?: string;
    downloads?: number;
    iconUrl?: string;
    icon?: string;
    is_official?: boolean;
    is_active?: boolean;
    installed?: boolean;
    isInstalling?: boolean;
    [key: string]: any;
  };
}>();

defineEmits(['edit', 'delete', 'install']);

const getButtonVariant = (item: any) => {
  if (item.installed || item.is_active === false) return 'ghost';
  return 'outline';
};
</script>
