<template>
  <Card 
    class="group hover:shadow-lg transition-all duration-300 cursor-pointer border-border bg-card text-card-foreground" 
    @click="$emit('click', agent)"
  >
    <CardHeader class="p-6 pb-2 space-y-0">
      <div class="flex items-start justify-between gap-4">
        <div class="flex items-center gap-4">
           <!-- Icon -->
           <div 
             class="h-12 w-12 rounded-lg flex items-center justify-center overflow-hidden border border-border/50 transition-colors"
             :class="isTemplate ? 'bg-muted/50' : 'bg-primary/5'"
           >
               <img v-if="isImage" :src="agent.icon" class="h-full w-full object-cover" />
               <component v-else :is="agent.iconComponent" class="h-6 w-6 text-foreground/80" />
           </div>
           <div class="space-y-1">
              <CardTitle class="text-base font-semibold leading-none tracking-tight line-clamp-1" :title="agent.name">
                {{ agent.name }}
              </CardTitle>
              <div class="flex items-center">
                 <Badge 
                   variant="secondary" 
                   class="text-xs font-normal h-5 px-1.5" 
                   v-if="isTemplate"
                 >
                   模版
                 </Badge>
                 <Badge 
                   variant="outline" 
                   class="text-xs font-normal h-5 px-1.5 text-primary bg-primary/5 border-primary/20" 
                   v-else
                 >
                   我的助手
                 </Badge>
              </div>
           </div>
        </div>
        
        <!-- Actions (Dropdown) -->
        <div v-if="!isTemplate" @click.stop>
            <DropdownMenu>
                <DropdownMenuTrigger as-child>
                    <Button variant="ghost" size="icon" class="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity">
                        <MoreVertical class="h-4 w-4 text-muted-foreground" />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                    <DropdownMenuItem @click="$emit('edit', agent)" class="cursor-pointer">
                        <Edit class="mr-2 h-4 w-4" /> 编辑
                    </DropdownMenuItem>
                    <DropdownMenuItem @click="$emit('delete', agent)" class="text-destructive focus:text-destructive cursor-pointer">
                        <Trash2 class="mr-2 h-4 w-4" /> 删除
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
      </div>
    </CardHeader>
    <CardContent class="p-6 pt-4 pb-4 h-[88px]">
       <p class="text-xs text-muted-foreground line-clamp-3 leading-relaxed">
         {{ agent.description || '暂无描述信息...' }}
       </p>
    </CardContent>
    <CardFooter class="p-6 pt-0 flex items-center justify-between">
        <div class="flex items-center gap-2">
            <div class="h-2 w-2 rounded-full" :class="agent.is_active !== false ? 'bg-green-500' : 'bg-muted-foreground/30'" />
            <span class="text-xs text-muted-foreground font-medium">{{ agent.is_active !== false ? 'Active' : 'Inactive' }}</span>
        </div>
        <span class="text-xs text-muted-foreground font-mono opacity-60">ID: {{ agent.id ? agent.id.substring(0, 6) : '---' }}</span>
    </CardFooter>
  </Card>
</template>

<script setup>
import { computed } from 'vue';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui/dropdown-menu';
import { MoreVertical, Edit, Trash2 } from 'lucide-vue-next';

const props = defineProps({
  agent: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['click', 'edit', 'delete']);

const isTemplate = computed(() => props.agent.is_template);

const isImage = computed(() => {
    const icon = props.agent.icon;
    if (!icon || typeof icon !== 'string') return false;
    const value = icon.trim();
    if (!value) return false;
    if (value.startsWith('data:image')) return true;
    if (value.startsWith('blob:')) return true;
    if (/^https?:\/\//i.test(value)) return true;
    if (value.startsWith('/') || value.startsWith('./') || value.startsWith('../')) return true;
    return /\.(png|jpe?g|gif|webp|svg)(\?.*)?$/i.test(value);
});
</script>
