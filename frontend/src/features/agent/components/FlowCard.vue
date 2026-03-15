<template>
  <Card 
    class="group relative overflow-hidden transition-all duration-300 cursor-pointer flex flex-col h-full min-h-[180px]" 
    :class="[
      'border-muted hover:shadow-lg hover:border-primary/40 bg-gradient-to-br from-card to-muted/10 hover:-translate-y-1'
    ]"
    @click="$emit('click', flow)"
  >
    <CardHeader class="p-5 pb-3 space-y-0 relative z-10">
      <div class="flex items-start justify-between gap-4">
        <div class="flex items-center gap-4 w-full overflow-hidden">
           <!-- Icon -->
           <div 
             class="h-12 w-12 rounded-xl flex-shrink-0 flex items-center justify-center overflow-hidden transition-all bg-blue-500/10 text-blue-500 group-hover:scale-105"
           >
               <GitBranch class="h-6 w-6" />
           </div>
           
           <div class="space-y-1.5 flex-1 min-w-0 relative">
              <div class="flex items-center justify-between">
                <CardTitle class="text-base font-bold leading-tight tracking-tight truncate pr-8" :title="flow.name">
                    {{ flow.name }}
                </CardTitle>
                
                <!-- Actions (Dropdown) -->
                <div @click.stop class="absolute right-[-8px] top-[-4px] opacity-0 group-hover:opacity-100 transition-opacity z-20">
                    <DropdownMenu>
                        <DropdownMenuTrigger as-child>
                            <Button variant="ghost" size="icon" class="h-8 w-8 hover:bg-muted/80">
                                <MoreVertical class="h-4 w-4 text-muted-foreground" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <slot name="actions"></slot>
                            <DropdownMenuItem @click="$emit('edit', flow)" class="cursor-pointer">
                                <Edit2 class="mr-2 h-4 w-4" /> 编辑
                            </DropdownMenuItem>
                            <DropdownMenuItem @click="$emit('delete', flow)" class="text-destructive focus:text-destructive cursor-pointer">
                                <Trash2 class="mr-2 h-4 w-4" /> 删除
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
              </div>
              
              <div class="flex items-center gap-2">
                 <Badge 
                   :variant="flow.is_active ? 'default' : 'secondary'"
                   class="text-[10px] font-medium px-1.5 py-0 h-5 rounded-md" 
                   :class="flow.is_active ? 'bg-green-500 hover:bg-green-600' : 'bg-muted text-muted-foreground'"
                 >
                   {{ flow.is_active ? '已启用' : '已禁用' }}
                 </Badge>
              </div>
           </div>
        </div>
      </div>
    </CardHeader>
    
    <CardContent class="p-5 pt-2 pb-4 min-h-[5rem]">
       <p class="text-xs text-muted-foreground/80 line-clamp-3 leading-relaxed">
         {{ flow.description || '暂无描述信息...' }}
       </p>
    </CardContent>
    
    <CardFooter class="p-5 pt-0 mt-auto border-t border-border/30 pt-3">
        <div class="w-full flex items-center justify-between">
            <div class="flex items-center gap-2 text-xs text-muted-foreground">
              <Clock class="h-3.5 w-3.5" />
              <span class="font-medium opacity-70">更新于 {{ formatDate(flow.updated_at) }}</span>
            </div>
            
            <div class="flex items-center gap-2">
                 <div class="relative flex h-2 w-2">
                   <span v-if="flow.is_active" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                   <span class="relative inline-flex rounded-full h-2 w-2" :class="flow.is_active ? 'bg-green-500' : 'bg-slate-300'"></span>
                 </div>
            </div>
        </div>
    </CardFooter>
  </Card>
</template>

<script setup>
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui/dropdown-menu';
import { MoreVertical, Edit2, Trash2, GitBranch, Clock } from 'lucide-vue-next';
import dayjs from 'dayjs';

const props = defineProps({
  flow: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['click', 'edit', 'delete']);

const formatDate = (date) => {
    if (!date) return '-';
    return dayjs(date).format('YYYY-MM-DD');
};
</script>
