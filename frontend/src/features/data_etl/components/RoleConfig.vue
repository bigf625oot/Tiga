<script setup lang="ts">
import { ref } from 'vue';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useToast } from '@/components/ui/toast/use-toast';
import { 
  ShieldAlert, Plus, Users, Save, Undo, AlertCircle 
} from 'lucide-vue-next';
import { useRBAC } from '../composables/useRBAC';

const { toast } = useToast();
const {
  roles,
  activeRoleId,
  activeRole,
  hasUnsavedChanges,
  selectRole,
  hasPermission,
  togglePermission,
  isRowFullySelected,
  toggleRowSelection,
  saveConfig,
  discardChanges,
  addRole,
  MODULES
} = useRBAC();

const activeTab = ref(MODULES[0].id);

// New role form
const isAddRoleOpen = ref(false);
const newRoleForm = ref({ name: '', code: '', description: '' });

const handleAddRole = () => {
  if (!newRoleForm.value.name || !newRoleForm.value.code) {
    toast({
      title: '验证失败',
      description: '角色名称和角色代码不能为空',
      variant: 'destructive',
    });
    return;
  }
  
  try {
    addRole({ ...newRoleForm.value });
    isAddRoleOpen.value = false;
    newRoleForm.value = { name: '', code: '', description: '' };
    toast({
      title: '角色添加成功',
      description: '请为新角色配置权限',
    });
  } catch (e: any) {
    toast({
      title: '无法添加角色',
      description: e.message === 'UNSAVED_CHANGES' ? '请先保存或放弃当前未保存的修改' : '发生未知错误',
      variant: 'destructive',
    });
  }
};

const handleSelectRole = (id: string) => {
  try {
    selectRole(id);
  } catch (e: any) {
    if (e.message === 'UNSAVED_CHANGES') {
      toast({
        title: '无法切换角色',
        description: '您有未保存的更改，请先保存或撤销后再切换角色。',
        variant: 'destructive',
      });
    }
  }
};

const handleSave = async () => {
  await saveConfig();
  toast({
    title: '保存成功',
    description: '角色配置已更新',
  });
};

const handleDiscard = () => {
  discardChanges();
  toast({
    title: '已撤销',
    description: '所有未保存的更改已撤销',
  });
};
</script>

<template>
  <div class="flex h-full min-h-[600px] gap-6">
    <!-- Left Panel: Role List -->
    <Card class="w-80 flex flex-col dark:bg-slate-950 dark:border-slate-800">
      <CardHeader class="pb-4">
        <div class="flex items-center justify-between">
          <div>
            <CardTitle class="text-lg">系统角色</CardTitle>
            <CardDescription class="mt-1">管理系统中的访问角色</CardDescription>
          </div>
          <Dialog v-model:open="isAddRoleOpen">
            <DialogTrigger as-child>
              <Button variant="outline" size="icon" :disabled="hasUnsavedChanges">
                <Plus class="w-4 h-4" />
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>新建角色</DialogTitle>
                <DialogDescription>创建一个新的业务角色，创建后可配置其权限。</DialogDescription>
              </DialogHeader>
              <div class="space-y-4 py-4">
                <div class="space-y-2">
                  <Label>角色名称 <span class="text-destructive">*</span></Label>
                  <Input v-model="newRoleForm.name" placeholder="例如：产品经理" />
                </div>
                <div class="space-y-2">
                  <Label>角色代码 <span class="text-destructive">*</span></Label>
                  <Input v-model="newRoleForm.code" placeholder="例如：product_mgr" />
                </div>
                <div class="space-y-2">
                  <Label>角色描述</Label>
                  <Input v-model="newRoleForm.description" placeholder="该角色的职责说明" />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" @click="isAddRoleOpen = false">取消</Button>
                <Button @click="handleAddRole">创建</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent class="flex-1 overflow-hidden p-0">
        <ScrollArea class="h-[calc(100vh-16rem)] px-4 pb-4 space-y-2">
          <div class="px-4 pb-4 space-y-2">
            <div 
              v-for="role in roles" 
              :key="role.id"
              @click="handleSelectRole(role.id)"
              class="flex items-center p-3 rounded-lg border cursor-pointer transition-colors"
              :class="[
                activeRoleId === role.id 
                  ? 'bg-primary/10 border-primary/50 dark:bg-primary/20 dark:border-primary/50' 
                  : 'hover:bg-muted dark:hover:bg-slate-900 border-transparent dark:border-transparent'
              ]"
            >
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-medium text-sm truncate">{{ role.name }}</span>
                  <Badge v-if="role.isSystem" variant="secondary" class="text-[10px] px-1.5 py-0 h-4">系统</Badge>
                </div>
                <div class="text-xs text-muted-foreground truncate">{{ role.description }}</div>
              </div>
              <div class="flex items-center gap-2 ml-2">
                <div class="flex items-center text-xs text-muted-foreground">
                  <Users class="w-3 h-3 mr-1" />
                  {{ role.userCount }}
                </div>
              </div>
            </div>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>

    <!-- Right Panel: Permissions -->
    <Card class="flex-1 flex flex-col dark:bg-slate-950 dark:border-slate-800">
      <CardHeader class="pb-4 border-b">
        <div class="flex items-center justify-between">
          <div>
            <div class="flex items-center gap-3">
              <CardTitle>{{ activeRole?.name }}</CardTitle>
              <Badge v-if="hasUnsavedChanges" variant="destructive" class="flex items-center gap-1">
                <AlertCircle class="w-3 h-3" /> 未保存更改
              </Badge>
            </div>
            <CardDescription class="mt-1.5">{{ activeRole?.description }}</CardDescription>
          </div>
          <div class="flex items-center gap-2">
            <Button v-if="hasUnsavedChanges" variant="outline" @click="handleDiscard">
              <Undo class="w-4 h-4 mr-2" />
              撤销
            </Button>
            <Button :disabled="!hasUnsavedChanges" @click="handleSave">
              <Save class="w-4 h-4 mr-2" />
              保存配置
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent class="flex-1 p-0 flex flex-col min-h-0">
        <div v-if="activeRole?.isSystem" class="p-4 bg-amber-50/50 dark:bg-amber-950/20 border-b flex items-start gap-3 text-sm text-muted-foreground">
          <ShieldAlert class="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <p class="font-medium text-foreground dark:text-amber-50">系统内置超级管理员</p>
            <p class="dark:text-amber-200/70">此角色具有系统的最高控制权，默认拥有所有模块的完全访问权限，不可修改或删除。</p>
          </div>
        </div>

        <Tabs v-model="activeTab" class="flex-1 flex flex-col">
          <div class="px-6 pt-4 border-b">
            <TabsList class="w-full justify-start h-auto p-0 bg-transparent gap-6">
              <TabsTrigger 
                v-for="module in MODULES" 
                :key="module.id" 
                :value="module.id"
                class="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-0 pb-3 pt-2 font-medium"
              >
                {{ module.name }}
              </TabsTrigger>
            </TabsList>
          </div>

          <ScrollArea class="flex-1 h-[calc(100vh-22rem)]">
            <div class="p-6">
              <TabsContent 
                v-for="module in MODULES" 
                :key="module.id" 
                :value="module.id"
                class="m-0 focus-visible:outline-none"
              >
                <div class="border rounded-lg overflow-hidden">
                  <table class="w-full text-sm">
                    <thead class="bg-muted/50 dark:bg-slate-900">
                      <tr>
                        <th class="px-4 py-3 text-left font-medium w-1/4 dark:text-slate-200">资源</th>
                        <th class="px-4 py-3 text-left font-medium w-1/2 dark:text-slate-200">操作权限</th>
                        <th class="px-4 py-3 text-right font-medium w-1/4 dark:text-slate-200">全选</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y dark:divide-slate-800">
                      <tr v-for="resource in module.resources" :key="resource.id" class="dark:hover:bg-slate-900/50 transition-colors">
                        <td class="px-4 py-4 font-medium dark:text-slate-300">{{ resource.name }}</td>
                        <td class="px-4 py-4">
                          <div class="flex flex-wrap gap-6">
                            <label 
                              v-for="action in resource.actions" 
                              :key="action.id"
                              class="flex items-center gap-2 cursor-pointer"
                              :class="{'opacity-50 cursor-not-allowed': activeRole?.isSystem}"
                            >
                              <Checkbox 
                                :checked="hasPermission(resource.id, action.id)"
                                @update:checked="(val) => togglePermission(resource.id, action.id, val)"
                                :disabled="activeRole?.isSystem"
                              />
                              <span class="text-sm select-none dark:text-slate-400">{{ action.name }}</span>
                            </label>
                          </div>
                        </td>
                        <td class="px-4 py-4 text-right">
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger as-child>
                                <div class="inline-flex items-center justify-end">
                                  <Checkbox 
                                    :checked="isRowFullySelected(resource)"
                                    @update:checked="(val) => toggleRowSelection(resource, val)"
                                    :disabled="activeRole?.isSystem"
                                  />
                                </div>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>选择/取消该资源的所有操作</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </TabsContent>
            </div>
          </ScrollArea>
        </Tabs>
      </CardContent>
    </Card>
  </div>
</template>
