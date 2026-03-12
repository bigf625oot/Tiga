<template>
  <Card class="group relative hover:shadow-xl transition-all duration-300 flex flex-col h-full overflow-hidden border-border/50 bg-card/50 hover:bg-card hover:-translate-y-1">
    <!-- Top Gradient Accent -->
    <div class="absolute top-0 left-0 w-full h-1" :class="item.type === 'mcp' ? 'bg-gradient-to-r from-purple-500/50 to-purple-500/10' : 'bg-gradient-to-r from-green-500/50 to-green-500/10'"></div>

    <div class="p-5 flex gap-4">
      <!-- Icon Box -->
      <div 
        class="relative flex-shrink-0 w-12 h-12 rounded-xl border flex items-center justify-center transition-all shadow-sm group-hover:shadow-md group-hover:scale-105"
        :class="item.type === 'mcp' ? 'bg-purple-50/50 border-purple-100 text-purple-600 dark:bg-purple-900/20 dark:border-purple-800' : 'bg-green-50/50 border-green-100 text-green-600 dark:bg-green-900/20 dark:border-green-800'"
      >
        <img v-if="item.iconUrl" :src="item.iconUrl" class="w-7 h-7 object-contain" alt="icon" />
        <Server v-else-if="item.type === 'mcp'" class="w-6 h-6" />
        <Blocks v-else class="w-6 h-6" />
        
        <!-- Online Status -->
        <span v-if="item.is_active !== false" class="absolute -top-1 -right-1 flex h-2.5 w-2.5">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500 border-2 border-background"></span>
        </span>
      </div>

      <!-- Title & Badges -->
      <div class="flex-1 min-w-0 flex flex-col justify-center">
        <div class="flex justify-between items-start gap-2">
            <h3 class="font-bold text-base truncate leading-tight py-0.5 group-hover:text-primary transition-colors" :title="item.name">{{ item.name }}</h3>
            <!-- Menu -->
            <div v-if="!item.is_official" class="-mr-2 -mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
              <DropdownMenu>
                <DropdownMenuTrigger as-child>
                  <Button variant="ghost" size="icon" class="h-7 w-7 text-muted-foreground hover:text-foreground">
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
        
        <div class="flex items-center gap-2 mt-1.5">
            <Badge variant="secondary" class="h-5 px-1.5 text-[10px] font-medium border-0 bg-secondary/50 text-secondary-foreground hover:bg-secondary/70">
              {{ item.type === 'mcp' ? 'MCP' : 'Skill' }}
            </Badge>
            <Badge v-if="item.is_official" variant="outline" class="h-5 px-1.5 text-[10px] font-medium border-primary/20 text-primary bg-primary/5 gap-1">
              <CheckCircle2 class="w-3 h-3" />
              官方
            </Badge>
        </div>
      </div>
    </div>

    <!-- Description -->
    <div class="px-5 pb-4 flex-1">
      <p class="text-xs text-muted-foreground/80 leading-relaxed line-clamp-2 min-h-[2.5em]" :title="item.description">
          {{ item.description || '暂无描述信息' }}
      </p>
    </div>

    <!-- Footer Actions -->
    <div class="px-5 py-3 bg-muted/30 border-t border-border/50 flex items-center justify-between gap-3 mt-auto">
        <!-- Info -->
        <div class="flex items-center gap-3 text-[10px] text-muted-foreground">
          <div class="flex items-center gap-1.5" :title="item.author">
             <div class="w-4 h-4 rounded-full bg-background border flex items-center justify-center text-[8px] font-bold text-muted-foreground shadow-sm">
               {{ item.author ? item.author.charAt(0).toUpperCase() : 'U' }}
             </div>
             <span class="truncate max-w-[60px] hidden sm:inline-block opacity-80">@{{ item.author || 'User' }}</span>
          </div>
          
          <span v-if="item.downloads" class="flex items-center gap-1 opacity-70">
              <Download class="w-3 h-3" /> {{ item.downloads }}k
          </span>
        </div>

        <!-- Action Button -->
        <Button 
          size="sm"
          class="h-7 text-xs px-3 shadow-sm transition-all active:scale-95"
          :variant="getButtonVariant(item)"
          :class="{'hover:bg-primary hover:text-primary-foreground': !item.installed && item.is_active !== false}"
          :disabled="item.installed || item.isInstalling || (item.is_active === false)"
          @click.stop="$emit('install', item)"
        >
          <template v-if="item.isInstalling">
            <Loader2 class="mr-1.5 h-3 w-3 animate-spin" />
            安装中
          </template>
          <template v-else-if="item.installed">
            <Check class="mr-1.5 h-3 w-3" />
            已安装
          </template>
          <template v-else-if="item.is_active === false">
            <AlertCircle class="mr-1.5 h-3 w-3" />
            不可用
          </template>
          <template v-else>
            <Plus class="mr-1.5 h-3 w-3" />
            获取
          </template>
        </Button>
    </div>
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
  Plus,
  Server,
  Blocks
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
