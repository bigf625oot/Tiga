<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '@/components/ui/table';
import {
  Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue
} from '@/components/ui/select';
import {
  Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle
} from '@/components/ui/sheet';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger
} from '@/components/ui/alert-dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useToast } from '@/components/ui/toast/use-toast';
import {
  Search, Plus, Pencil, Trash2, Users, Building2, ChevronRight, ChevronDown,
  RefreshCw, AlertTriangle, ArrowRightLeft, Undo2, HelpCircle, Loader2,
  CheckCircle, XCircle, Home, ArrowLeft, Info, List, AlertCircle
} from 'lucide-vue-next';
import ListBody from 'ant-design-vue/es/transfer/ListBody';

interface Department {
  id: number;
  name: string;
  code: string;
  parent_id: number | null;
  parent?: Department;
  children?: Department[];
  description?: string;
  leader?: string;
  phone?: string;
  userCount: number;
  created_at: string;
  updated_at: string;
  _level?: number;
  _path?: string[];
}

interface DeptFormData {
  id?: number;
  name: string;
  code: string;
  parent_id: number | undefined;
  description: string;
  leader: string;
  phone: string;
}

interface User {
  id: number;
  username: string;
  email: string;
  department_id?: number;
  department_name?: string;
}

interface OperationLog {
  id: string;
  type: 'create' | 'update' | 'delete' | 'transfer';
  target: string;
  description: string;
  timestamp: string;
  canUndo: boolean;
  undoData?: any;
}

const { toast } = useToast();

const mockDepartments: Department[] = [
  { id: 1, name: '技术研发部', code: 'TECH', parent_id: null, description: '负责产品技术研发', leader: '张技术', phone: '13800138001', userCount: 15, created_at: '2025-01-15 08:00:00', updated_at: '2026-03-15 10:20:00' },
  { id: 2, name: '产品设计部', code: 'PROD', parent_id: null, description: '负责产品设计与规划', leader: '李产品', phone: '13800138002', userCount: 8, created_at: '2025-01-15 08:00:00', updated_at: '2026-02-20 14:30:00' },
  { id: 3, name: '市场营销部', code: 'MKT', parent_id: null, description: '负责市场推广与销售', leader: '王市场', phone: '13800138003', userCount: 12, created_at: '2025-02-01 09:00:00', updated_at: '2026-03-10 11:00:00' },
  { id: 4, name: '人力资源部', code: 'HR', parent_id: null, description: '负责人才招聘与管理', leader: '赵人力', phone: '13800138004', userCount: 6, created_at: '2025-02-15 10:00:00', updated_at: '2026-01-20 16:00:00' },
  { id: 5, name: '前端开发组', code: 'TECH-FE', parent_id: 1, description: '前端技术开发', leader: '孙前端', phone: '13800138005', userCount: 5, created_at: '2025-03-01 08:30:00', updated_at: '2026-03-18 09:00:00' },
  { id: 6, name: '后端开发组', code: 'TECH-BE', parent_id: 1, description: '后端技术开发', leader: '周后端', phone: '13800138006', userCount: 7, created_at: '2025-03-01 08:30:00', updated_at: '2026-03-19 10:00:00' },
  { id: 7, name: 'UI设计组', code: 'PROD-UI', parent_id: 2, description: '界面视觉设计', leader: '吴UI', phone: '13800138007', userCount: 3, created_at: '2025-04-10 09:00:00', updated_at: '2026-02-28 15:00:00' },
];

const mockUsers: User[] = [
  { id: 1, username: 'admin', email: 'admin@example.com', department_id: 1, department_name: '技术研发部' },
  { id: 2, username: 'zhang_san', email: 'zhangsan@example.com', department_id: 1, department_name: '技术研发部' },
  { id: 3, username: 'li_si', email: 'lisi@example.com', department_id: 2, department_name: '产品设计部' },
  { id: 4, username: 'wang_wu', email: 'wangwu@example.com', department_id: 5, department_name: '前端开发组' },
  { id: 5, username: 'zhao_liu', email: 'zhaoliu@example.com', department_id: 6, department_name: '后端开发组' },
  { id: 6, username: 'qian_qi', email: 'qianqi@example.com', department_id: 3, department_name: '市场营销部' },
  { id: 7, username: 'sun_ba', email: 'sunba@example.com', department_id: undefined, department_name: undefined },
];

const departments = ref<Department[]>([...mockDepartments]);
const users = ref<User[]>([...mockUsers]);

const selectedDepartment = ref<Department | null>(null);
const expandedDepts = ref<Set<number>>(new Set([1]));
const searchQuery = ref('');
const activeTab = ref('tree');
const isLoading = ref(false);
const operationLogs = ref<OperationLog[]>([]);
const showUndoToast = ref(false);
const lastOperation = ref<OperationLog | null>(null);

const isDialogOpen = ref(false);
const isDeleteDialogOpen = ref(false);
const isTransferDialogOpen = ref(false);
const currentDept = ref<Department | null>(null);
const selectedUserIds = ref<number[]>([]);
const parentSelectValue = ref<string>('none');
const operationInProgress = ref(false);

const treeWidth = ref(350);
const isDragging = ref(false);

const startDrag = (e: MouseEvent) => {
  isDragging.value = true;
  document.body.style.cursor = 'col-resize';
  document.body.style.userSelect = 'none';

  const startX = e.clientX;
  const startWidth = treeWidth.value;

  const handleMouseMove = (moveEvent: MouseEvent) => {
    if (!isDragging.value) return;
    let newWidth = startWidth + (moveEvent.clientX - startX);
    if (newWidth < 200) newWidth = 200;
    if (newWidth > 800) newWidth = 800;
    treeWidth.value = newWidth;
  };

  const handleMouseUp = () => {
    isDragging.value = false;
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    window.removeEventListener('mousemove', handleMouseMove);
    window.removeEventListener('mouseup', handleMouseUp);
  };

  window.addEventListener('mousemove', handleMouseMove);
  window.addEventListener('mouseup', handleMouseUp);
};

const deptForm = reactive<DeptFormData>({
  name: '',
  code: '',
  parent_id: undefined,
  description: '',
  leader: '',
  phone: '',
});

const formErrors = reactive<Partial<Record<keyof DeptFormData, string>>>({});

const buildTree = (depts: Department[]): Department[] => {
  const map = new Map<number, Department>();
  const roots: Department[] = [];

  depts.forEach(d => {
    map.set(d.id, { ...d, children: [] });
  });

  map.forEach(dept => {
    if (dept.parent_id === null) {
      roots.push(dept);
    } else {
      const parent = map.get(dept.parent_id);
      if (parent) {
        parent.children = parent.children || [];
        parent.children.push(dept);
      }
    }
  });

  return roots;
};

const getDepartmentPath = (dept: Department): string[] => {
  const path: string[] = [];
  let current = dept;
  while (current) {
    path.unshift(current.name);
    if (current.parent_id) {
      current = departments.value.find(d => d.id === current.parent_id) || current;
    } else {
      break;
    }
  }
  return path;
};

const departmentTree = computed(() => buildTree(departments.value));

const flattenedDepartments = computed(() => {
  const result: Department[] = [];
  const flatten = (depts: Department[], level = 0) => {
    depts.forEach(dept => {
      const path = getDepartmentPath(dept);
      result.push({ ...dept, _level: level, _path: path });
      if (expandedDepts.value.has(dept.id) && dept.children) {
        flatten(dept.children, level + 1);
      }
    });
  };
  flatten(departmentTree.value);
  return result;
});

const filteredDepartments = computed(() => {
  if (!searchQuery.value) return flattenedDepartments.value;
  const query = searchQuery.value.toLowerCase();
  return flattenedDepartments.value.filter(d =>
    d.name.toLowerCase().includes(query) ||
    d.code.toLowerCase().includes(query) ||
    (d.description && d.description.toLowerCase().includes(query))
  );
});

const availableParents = computed(() => {
  return departments.value.filter(d => !currentDept.value || d.id !== currentDept.value.id);
});

const usersInDepartment = computed(() => {
  if (!selectedDepartment.value) return [];
  return users.value.filter(u => u.department_id === selectedDepartment.value!.id);
});

const usersNotInDepartment = computed(() => {
  if (!selectedDepartment.value) return users.value;
  return users.value.filter(u => u.department_id !== selectedDepartment.value!.id);
});

const currentDeptChildrenCount = computed(() => {
  if (!currentDept.value) return 0;
  return departments.value.filter(d => d.parent_id === currentDept.value!.id).length;
});

const getChildrenCount = (dept: Department): number => {
  let count = 0;
  const countRecursive = (d: Department) => {
    if (d.children) {
      d.children.forEach(child => {
        count++;
        countRecursive(child);
      });
    }
  };
  countRecursive(dept);
  return count;
};

const currentBreadcrumb = computed(() => {
  if (!selectedDepartment.value) return [];
  return selectedDepartment.value._path || getDepartmentPath(selectedDepartment.value);
});

function toggleExpand(deptId: number) {
  if (expandedDepts.value.has(deptId)) {
    expandedDepts.value.delete(deptId);
  } else {
    expandedDepts.value.add(deptId);
  }
}

function resetForm() {
  deptForm.id = undefined;
  deptForm.name = '';
  deptForm.code = '';
  deptForm.parent_id = undefined;
  deptForm.description = '';
  deptForm.leader = '';
  deptForm.phone = '';
  parentSelectValue.value = 'none';
  Object.keys(formErrors).forEach(key => delete formErrors[key as keyof DeptFormData]);
}

function validateForm(): boolean {
  let isValid = true;
  Object.keys(formErrors).forEach(key => delete formErrors[key as keyof DeptFormData]);

  if (!deptForm.name || deptForm.name.length < 2) {
    formErrors.name = '部门名称至少2个字符';
    isValid = false;
  }
  if (!deptForm.code || !/^[A-Z][A-Z0-9_-]{1,10}$/.test(deptForm.code)) {
    formErrors.code = '部门代码格式：2-10位大写字母/数字';
    isValid = false;
  }
  if (deptForm.phone && !/^1[3-9]\d{9}$/.test(deptForm.phone)) {
    formErrors.phone = '请输入有效的手机号码';
    isValid = false;
  }

  return isValid;
}

function openCreateDialog(parentDept?: Department) {
  resetForm();
  deptForm.parent_id = parentDept?.id;
  parentSelectValue.value = parentDept ? String(parentDept.id) : 'none';
  isDialogOpen.value = true;
}

function openEditDialog(dept: Department) {
  resetForm();
  deptForm.id = dept.id;
  deptForm.name = dept.name;
  deptForm.code = dept.code;
  deptForm.parent_id = dept.parent_id || undefined;
  parentSelectValue.value = dept.parent_id ? String(dept.parent_id) : 'none';
  deptForm.description = dept.description || '';
  deptForm.leader = dept.leader || '';
  deptForm.phone = dept.phone || '';
  isDialogOpen.value = true;
}

function openDeleteDialog(dept: Department) {
  currentDept.value = dept;
  isDeleteDialogOpen.value = true;
}

function openTransferDialog(dept: Department) {
  selectedDepartment.value = dept;
  selectedUserIds.value = [];
  isTransferDialogOpen.value = true;
}

function selectDepartment(dept: Department) {
  selectedDepartment.value = dept;
}

function goBackToParent() {
  if (selectedDepartment.value?.parent_id) {
    const parent = departments.value.find(d => d.id === selectedDepartment.value?.parent_id);
    if (parent) {
      selectedDepartment.value = parent;
      expandedDepts.value.add(parent.id);
    }
  } else {
    selectedDepartment.value = null;
  }
}

function goToRoot() {
  selectedDepartment.value = null;
}

async function handleSaveDept() {
  if (!validateForm()) return;

  operationInProgress.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 500));

    if (deptForm.id) {
      const index = departments.value.findIndex(d => d.id === deptForm.id);
      if (index !== -1) {
        const parent = departments.value.find(d => d.id === deptForm.parent_id);
        const oldData = { ...departments.value[index] };
        departments.value[index] = {
          ...departments.value[index],
          name: deptForm.name,
          code: deptForm.code,
          parent_id: deptForm.parent_id || null,
          parent: parent,
          description: deptForm.description,
          leader: deptForm.leader,
          phone: deptForm.phone,
          updated_at: new Date().toISOString().replace('T', ' ').substring(0, 19),
        };
        addOperationLog('update', deptForm.name, `更新了部门"${deptForm.name}"的信息`, true, oldData);
      }
      showSuccessToast('更新成功', `部门 "${deptForm.name}" 信息已更新`);
    } else {
      const parent = departments.value.find(d => d.id === deptForm.parent_id);
      const newDept: Department = {
        id: Math.max(...departments.value.map(d => d.id)) + 1,
        name: deptForm.name,
        code: deptForm.code,
        parent_id: deptForm.parent_id || null,
        parent: parent,
        description: deptForm.description,
        leader: deptForm.leader,
        phone: deptForm.phone,
        userCount: 0,
        created_at: new Date().toISOString().replace('T', ' ').substring(0, 19),
        updated_at: new Date().toISOString().replace('T', ' ').substring(0, 19),
      };
      departments.value.push(newDept);
      addOperationLog('create', deptForm.name, `创建了新部门"${deptForm.name}"`, true, newDept);
      showSuccessToast('创建成功', `部门 "${deptForm.name}" 已创建`);
    }

    isDialogOpen.value = false;
    resetForm();
  } catch {
    showErrorToast('操作失败', '请稍后重试');
  } finally {
    operationInProgress.value = false;
  }
}

async function handleDeleteDept() {
  if (!currentDept.value) return;

  operationInProgress.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 300));

    const childDepts = departments.value.filter(d => d.parent_id === currentDept.value!.id);
    if (childDepts.length > 0) {
      showErrorToast('删除失败', `请先删除 "${currentDept.value.name}" 的 ${childDepts.length} 个子部门`);
      isDeleteDialogOpen.value = false;
      return;
    }

    if (usersInDepartment.value.length > 0) {
      showErrorToast('删除失败', `该部门仍有 ${usersInDepartment.value.length} 名用户，请先转移`);
      isDeleteDialogOpen.value = false;
      return;
    }

    const deletedData = { ...currentDept.value };
    departments.value = departments.value.filter(d => d.id !== currentDept.value!.id);

    if (selectedDepartment.value?.id === currentDept.value.id) {
      selectedDepartment.value = null;
    }

    addOperationLog('delete', currentDept.value.name, `删除了部门"${currentDept.value.name}"`, true, deletedData);
    showSuccessToast('删除成功', `部门 "${currentDept.value.name}" 已删除`);
    isDeleteDialogOpen.value = false;
    currentDept.value = null;
  } catch {
    showErrorToast('操作失败', '请稍后重试');
  } finally {
    operationInProgress.value = false;
  }
}

async function handleTransferUsers() {
  if (!selectedDepartment.value || selectedUserIds.value.length === 0) return;

  operationInProgress.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 300));

    const oldAssignments = selectedUserIds.value.map(id => {
      const user = users.value.find(u => u.id === id);
      return { userId: id, oldDeptId: user?.department_id, oldDeptName: user?.department_name };
    });

    selectedUserIds.value.forEach(userId => {
      const user = users.value.find(u => u.id === userId);
      if (user) {
        user.department_id = selectedDepartment.value!.id;
        user.department_name = selectedDepartment.value!.name;
      }
    });

    const newDept = departments.value.find(d => d.id === selectedDepartment.value!.id);
    if (newDept) {
      newDept.userCount = usersInDepartment.value.length;
    }

    addOperationLog('transfer', selectedDepartment.value.name,
      `将 ${selectedUserIds.value.length} 名用户转移至 "${selectedDepartment.value.name}"`,
      true, oldAssignments);

    showSuccessToast('转移成功', `已将 ${selectedUserIds.value.length} 名用户转移至 ${selectedDepartment.value!.name}`);

    selectedUserIds.value = [];
    isTransferDialogOpen.value = false;
  } catch {
    showErrorToast('操作失败', '请稍后重试');
  } finally {
    operationInProgress.value = false;
  }
}

async function handleUndo() {
  if (!lastOperation.value || !lastOperation.value.canUndo) return;

  const op = lastOperation.value;
  operationInProgress.value = true;

  try {
    await new Promise(resolve => setTimeout(resolve, 300));

    switch (op.type) {
      case 'create':
        if (op.undoData) {
          departments.value = departments.value.filter(d => d.id !== op.undoData.id);
        }
        break;
      case 'update':
        if (op.undoData) {
          const index = departments.value.findIndex(d => d.id === op.undoData.id);
          if (index !== -1) {
            departments.value[index] = { ...op.undoData };
          }
        }
        break;
      case 'delete':
        if (op.undoData) {
          departments.value.push({ ...op.undoData });
        }
        break;
      case 'transfer':
        if (op.undoData && Array.isArray(op.undoData)) {
          op.undoData.forEach((item: any) => {
            const user = users.value.find(u => u.id === item.userId);
            if (user) {
              user.department_id = item.oldDeptId;
              user.department_name = item.oldDeptName;
            }
          });
        }
        break;
    }

    operationLogs.value = operationLogs.value.filter(log => log.id !== op.id);
    lastOperation.value = operationLogs.value[0] || null;
    showUndoSuccessToast('已撤销', op.description.replace('已', '撤销了'));
  } catch {
    showErrorToast('撤销失败', '请稍后重试');
  } finally {
    operationInProgress.value = false;
  }
}

function addOperationLog(type: OperationLog['type'], target: string, description: string, canUndo: boolean, undoData?: any) {
  const log: OperationLog = {
    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    type,
    target,
    description,
    timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
    canUndo,
    undoData,
  };
  operationLogs.value.unshift(log);
  lastOperation.value = log;

  if (operationLogs.value.length > 10) {
    operationLogs.value = operationLogs.value.slice(0, 10);
  }
}

function showSuccessToast(title: string, description: string) {
  toast({ title, description, variant: 'default' });
}

function showErrorToast(title: string, description: string) {
  toast({ title, description, variant: 'destructive' });
}

function showUndoSuccessToast(title: string, description: string) {
  toast({ title, description, variant: 'default' });
}

async function refreshData() {
  isLoading.value = true;
  await new Promise(resolve => setTimeout(resolve, 800));
  isLoading.value = false;
  toast({ title: '刷新成功', description: '部门数据已更新', variant: 'default' });
}

function handleSearch() {
}

function handleTabChange(value: string | number) {
  activeTab.value = String(value);
  selectedDepartment.value = null;
}

onMounted(() => {
  expandedDepts.value.add(1);
});
</script>

<template>
  <TooltipProvider>
    <div class="space-y-4">
      <Card class="border-0 shadow-none dark:bg-transparent">
        <CardHeader class="px-0 pt-0">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
            </div>
            <div class="flex gap-2 items-center">
              <div class="flex items-center bg-muted/50 p-1 rounded-md mr-2 border dark:border-slate-800">
                <Tooltip>
                  <TooltipTrigger as-child>
                    <Button
                      variant="ghost"
                      size="sm"
                      class="h-7 px-2"
                      :class="activeTab === 'tree' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'"
                      @click="activeTab = 'tree'"
                    >
                      <Building2 class="w-4 h-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>树形视图</TooltipContent>
                </Tooltip>
                
                <Tooltip>
                  <TooltipTrigger as-child>
                    <Button
                      variant="ghost"
                      size="sm"
                      class="h-7 px-2"
                      :class="activeTab === 'list' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'"
                      @click="activeTab = 'list'"
                    >
                      <List class="w-4 h-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>列表视图</TooltipContent>
                </Tooltip>
              </div>

              <div v-if="lastOperation && lastOperation.canUndo" class="flex items-center mr-2">
                <Tooltip>
                  <TooltipTrigger as-child>
                    <Button
                      variant="outline"
                      size="sm"
                      class="h-8 px-2 text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20"
                      @click="handleUndo"
                      :disabled="operationInProgress"
                    >
                      <Undo2 class="w-4 h-4 mr-1" />
                      撤销
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>撤销: {{ lastOperation.description }}</p>
                  </TooltipContent>
                </Tooltip>
              </div>

              <Tooltip>
                <TooltipTrigger as-child>
                  <Button variant="outline" size="icon" class="h-9 w-9" @click="refreshData" :disabled="isLoading">
                    <Loader2 class="w-4 h-4" :class="{ 'animate-spin': isLoading }" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>刷新数据</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger as-child>
                  <Button variant="outline" size="icon" class="h-9 w-9">
                    <HelpCircle class="w-4 h-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>查看帮助</TooltipContent>
              </Tooltip>

              <Button size="sm" @click="openCreateDialog()" class="relative">
                <Plus class="w-4 h-4 mr-1" />
                新建部门
                <span v-if="operationInProgress" class="absolute inset-0 flex items-center justify-center bg-background/80 rounded-md">
                  <Loader2 class="w-4 h-4 animate-spin" />
                </span>
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent class="space-y-4 px-0 pb-0">
          <Tabs :modelValue="activeTab" @update:modelValue="handleTabChange" class="w-full">
            <TabsContent value="tree" class="space-y-4 mt-0">
              <div class="flex gap-1 relative">
                <div 
                  class="h-[calc(100vh-16rem)] flex-shrink-0 border rounded-lg p-4 dark:bg-slate-900/50 max overflow-y-auto"
                  :style="{ width: `${treeWidth}px` }"
                >
                  <div class="flex items-center justify-between mb-4">
                    <div class="relative flex-1">
                      <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input
                        v-model="searchQuery"
                        placeholder="搜索部门名称、代码..."
                        class="pl-9"
                        @input="handleSearch"
                      />
                    </div>
                    <div v-if="searchQuery" class="ml-2 text-sm text-muted-foreground">
                      找到 {{ filteredDepartments.length }} 个结果
                    </div>
                  </div>

                  <div class="space-y-1">
                    <div
                      v-for="dept in filteredDepartments"
                      :key="dept.id"
                      :class="cn(
                        'flex items-center gap-2 p-2 rounded-md cursor-pointer transition-all duration-200',
                        'hover:bg-muted/50 dark:hover:bg-slate-800/50',
                        selectedDepartment?.id === dept.id && 'bg-muted dark:bg-slate-800 ring-2 ring-primary/50'
                      )"
                      :style="{ paddingLeft: `${(dept._level || 0) * 20 + 8}px` }"
                      @click="selectDepartment(dept)"
                    >
                      <Button
                        v-if="getChildrenCount(dept) > 0"
                        variant="ghost"
                        size="icon"
                        class="h-5 w-5 p-0 hover:bg-muted"
                        @click.stop="toggleExpand(dept.id)"
                      >
                        <ChevronDown v-if="expandedDepts.has(dept.id)" class="w-4 h-4 transition-transform" />
                        <ChevronRight v-else class="w-4 h-4 transition-transform" />
                      </Button>
                      <span v-else class="w-5"></span>

                      <Building2 class="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      <span class="flex-1 text-sm dark:text-slate-200 truncate">{{ dept.name }}</span>

                      <Badge variant="secondary" class="text-xs flex-shrink-0">{{ dept.code }}</Badge>

                      <Tooltip>
                        <TooltipTrigger as-child>
                          <span class="text-xs text-muted-foreground hover:text-primary cursor-help">
                            {{ dept.userCount }}人
                          </span>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>该部门有 {{ dept.userCount }} 名成员</p>
                        </TooltipContent>
                      </Tooltip>

                      <Tooltip>
                        <TooltipTrigger as-child>
                          <Button
                            variant="ghost"
                            size="icon"
                            class="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 hover:bg-primary/10"
                            @click.stop="openCreateDialog(dept)"
                          >
                            <Plus class="w-3 h-3" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>添加子部门</TooltipContent>
                      </Tooltip>
                    </div>

                    <div v-if="filteredDepartments.length === 0" class="text-center py-8 text-muted-foreground">
                      <Building2 class="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>未找到匹配的部门</p>
                      <p class="text-sm">请尝试其他搜索词</p>
                    </div>
                  </div>
                </div>

                <!-- 拖拽调整宽度的手柄 -->
                <div 
                  class="w-2 hover:bg-primary/30 cursor-col-resize rounded transition-colors flex-shrink-0 z-10 flex items-center justify-center group"
                  :class="isDragging ? 'bg-primary/30' : 'bg-transparent'"
                  @mousedown.prevent="startDrag"
                >
                  <div class="h-8 w-1 rounded-full bg-border group-hover:bg-primary/50" :class="isDragging && 'bg-primary/50'"></div>
                </div>

                <div v-if="selectedDepartment" class="flex-1 border rounded-lg p-3 dark:bg-slate-900/50 flex flex-col min-w-0">
                  <div class="flex items-center justify-between mb-2 pb-2 border-b dark:border-slate-700">
                    <div class="flex items-center gap-1.5">
                      <Button v-if="selectedDepartment.parent_id || currentBreadcrumb.length > 1" variant="ghost" size="icon" class="h-6 w-6" @click="goBackToParent">
                        <ArrowLeft class="w-3 h-3" />
                      </Button>
                      <h3 class="font-medium dark:text-slate-200 flex items-center gap-1.5 text-sm">
                        {{ selectedDepartment.name }}
                        <Badge v-if="!selectedDepartment.parent_id" variant="outline" class="text-[10px]">顶级</Badge>
                      </h3>
                    </div>
                    <div class="flex gap-0.5">
                      <Tooltip>
                        <TooltipTrigger as-child>
                          <Button variant="ghost" size="icon" class="h-7 w-7" @click="openCreateDialog(selectedDepartment)">
                            <Plus class="w-3 h-3" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>添加子部门</TooltipContent>
                      </Tooltip>
                      <Tooltip>
                        <TooltipTrigger as-child>
                          <Button variant="ghost" size="icon" class="h-7 w-7" @click="openEditDialog(selectedDepartment)">
                            <Pencil class="w-3 h-3" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>编辑部门</TooltipContent>
                      </Tooltip>
                      <Tooltip>
                        <TooltipTrigger as-child>
                          <Button variant="ghost" size="icon" class="h-7 w-7" @click="openTransferDialog(selectedDepartment)">
                            <ArrowRightLeft class="w-3 h-3" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>调整成员</TooltipContent>
                      </Tooltip>
                      <AlertDialog>
                        <Tooltip>
                          <TooltipTrigger as-child>
                            <AlertDialogTrigger as-child>
                              <Button variant="ghost" size="icon" class="h-7 w-7 text-red-500 hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20">
                                <Trash2 class="w-3 h-3" />
                              </Button>
                            </AlertDialogTrigger>
                          </TooltipTrigger>
                          <TooltipContent>删除部门</TooltipContent>
                        </Tooltip>
                      </AlertDialog>
                    </div>
                  </div>

                  <div class="flex items-center gap-1 text-[10px] text-muted-foreground mb-2">
                    <Button variant="ghost" size="sm" class="h-4 px-1" @click="goToRoot">
                      <Home class="w-2.5 h-2.5 mr-0.5" />
                      根目录
                    </Button>
                    <template v-for="(crumb, idx) in currentBreadcrumb" :key="idx">
                      <ChevronRight class="w-2.5 h-2.5" />
                      <Button
                        variant="ghost"
                        size="sm"
                        class="h-4 px-1"
                        :class="idx === currentBreadcrumb.length - 1 && 'text-primary font-medium'"
                        @click="idx < currentBreadcrumb.length - 1 && (selectedDepartment = departments.find(d => d.name === crumb) || selectedDepartment)"
                      >
                        {{ crumb }}
                      </Button>
                    </template>
                  </div>

                  <div class="flex-1 overflow-y-auto space-y-2 text-xs">
                    <div class="grid grid-cols-2 gap-2">
                      <div class="p-2 bg-muted/30 dark:bg-slate-800/50 rounded-lg">
                        <p class="text-[10px] text-muted-foreground mb-0.5">部门代码</p>
                        <p class="font-mono dark:text-slate-200 text-xs">{{ selectedDepartment.code }}</p>
                      </div>
                      <div class="p-2 bg-muted/30 dark:bg-slate-800/50 rounded-lg">
                        <p class="text-[10px] text-muted-foreground mb-0.5">部门负责人</p>
                        <p class="dark:text-slate-200 text-xs">{{ selectedDepartment.leader || '-' }}</p>
                      </div>
                      <div class="p-2 bg-muted/30 dark:bg-slate-800/50 rounded-lg">
                        <p class="text-[10px] text-muted-foreground mb-0.5">联系电话</p>
                        <p class="dark:text-slate-200 text-xs">{{ selectedDepartment.phone || '-' }}</p>
                      </div>
                      <div class="p-2 bg-muted/30 dark:bg-slate-800/50 rounded-lg">
                        <p class="text-[10px] text-muted-foreground mb-0.5">上级部门</p>
                        <p class="dark:text-slate-200 text-xs">{{ selectedDepartment.parent?.name || '无' }}</p>
                      </div>
                    </div>

                    <div class="p-2 bg-muted/30 dark:bg-slate-800/50 rounded-lg">
                      <div class="flex items-center justify-between mb-1">
                        <p class="text-[10px] text-muted-foreground">组织结构</p>
                        <div class="flex gap-1 text-[10px]">
                          <span class="text-primary">{{ getChildrenCount(selectedDepartment) }} 个子部门</span>
                          <span class="text-muted-foreground">|</span>
                          <span>{{ selectedDepartment.userCount }} 名成员</span>
                        </div>
                      </div>
                    </div>

                    <div class="p-2 bg-muted/30 dark:bg-slate-800/50 rounded-lg">
                      <p class="text-[10px] text-muted-foreground mb-0.5">部门描述</p>
                      <p class="dark:text-slate-200 text-xs">{{ selectedDepartment.description || '暂无描述' }}</p>
                    </div>

                    <div class="pt-2 border-t dark:border-slate-700">
                      <div class="flex items-center justify-between mb-2">
                        <p class="text-xs font-medium dark:text-slate-200 flex items-center gap-1.5">
                          <Users class="w-3 h-3" />
                          部门成员
                        </p>
                        <Button variant="ghost" size="sm" class="h-5 text-[10px] px-1" @click="openTransferDialog(selectedDepartment)">
                          <ArrowRightLeft class="w-2.5 h-2.5 mr-0.5" />
                          管理
                        </Button>
                      </div>

                      <div v-if="usersInDepartment.length > 0" class="space-y-1.5 max-h-[100px] overflow-y-auto">
                        <div
                          v-for="user in usersInDepartment"
                          :key="user.id"
                          class="flex items-center gap-2 p-1.5 rounded-md bg-muted/20 dark:bg-slate-800/30 hover:bg-muted/40 dark:hover:bg-slate-800/50 transition-colors"
                        >
                          <div class="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-[10px] font-medium text-primary">
                            {{ user.username.charAt(0).toUpperCase() }}
                          </div>
                          <div class="flex-1 min-w-0">
                            <p class="text-xs dark:text-slate-200 truncate">{{ user.username }}</p>
                            <p class="text-[10px] text-muted-foreground truncate">{{ user.email }}</p>
                          </div>
                          <CheckCircle class="w-3 h-3 text-green-500 flex-shrink-0" />
                        </div>
                      </div>
                      <p v-else class="text-xs text-muted-foreground text-center py-2">
                        暂无成员
                      </p>
                    </div>

                    <div class="pt-1.5 border-t dark:border-slate-700 text-[10px] text-muted-foreground">
                      <div class="flex justify-between mb-0.5">
                        <span>创建时间</span>
                        <span>{{ selectedDepartment.created_at }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span>更新时间</span>
                        <span>{{ selectedDepartment.updated_at }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-else class="flex-1 border rounded-lg p-8 dark:bg-slate-900/50 flex items-center justify-center min-w-0">
                  <div class="text-center text-muted-foreground">
                    <Building2 class="w-16 h-16 mx-auto mb-3 opacity-30" />
                    <p class="text-base font-medium mb-1">选择一个部门</p>
                    <p class="text-sm">点击左侧部门树查看详情</p>
                    <Button variant="outline" size="sm" class="mt-4" @click="openCreateDialog()">
                      <Plus class="w-4 h-4 mr-1" />
                      或新建部门
                    </Button>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="list" class="mt-0">
              <div class="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow class="dark:bg-slate-900 dark:border-slate-800">
                      <TableHead class="dark:text-slate-200 w-[300px]">部门信息</TableHead>
                      <TableHead class="dark:text-slate-200">负责人</TableHead>
                      <TableHead class="dark:text-slate-200">上级部门</TableHead>
                      <TableHead class="dark:text-slate-200">成员数</TableHead>
                      <TableHead class="dark:text-slate-200 w-[180px]">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <template v-for="dept in flattenedDepartments" :key="dept.id">
                      <TableRow class="dark:border-slate-800 cursor-pointer" @click="selectDepartment(dept)">
                        <TableCell class="font-medium dark:text-slate-200">
                          <div class="flex items-center gap-3">
                            <div :style="{ paddingLeft: `${(dept._level || 0) * 20}px` }" class="flex items-center gap-2">
                              <Building2 class="w-4 h-4 text-muted-foreground flex-shrink-0" />
                              <span>{{ dept.name }}</span>
                              <Badge variant="secondary" class="text-xs ml-2">{{ dept.code }}</Badge>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell class="dark:text-slate-300">{{ dept.leader || '-' }}</TableCell>
                        <TableCell class="dark:text-slate-300">
                          <div class="flex items-center gap-1">
                            <span v-if="dept.parent">{{ dept.parent.name }}</span>
                            <Badge v-else variant="outline" class="text-xs">顶级部门</Badge>
                          </div>
                        </TableCell>
                        <TableCell class="dark:text-slate-300">
                          <div class="flex items-center gap-1">
                            <Users class="w-3 h-3" />
                            {{ dept.userCount }}
                          </div>
                        </TableCell>
                        <TableCell @click.stop>
                          <div class="flex items-center gap-1">
                            <Tooltip>
                              <TooltipTrigger as-child>
                                <Button variant="ghost" size="icon" class="h-8 w-8" @click="openCreateDialog(dept)" title="添加子部门">
                                  <Plus class="w-4 h-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>添加子部门</TooltipContent>
                            </Tooltip>
                            <Tooltip>
                              <TooltipTrigger as-child>
                                <Button variant="ghost" size="icon" class="h-8 w-8" @click="openEditDialog(dept)" title="编辑">
                                  <Pencil class="w-4 h-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>编辑</TooltipContent>
                            </Tooltip>
                            <Tooltip>
                              <TooltipTrigger as-child>
                                <Button variant="ghost" size="icon" class="h-8 w-8" @click="openTransferDialog(dept)" title="调整成员">
                                  <ArrowRightLeft class="w-4 h-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>调整成员</TooltipContent>
                            </Tooltip>
                            <AlertDialog>
                              <Tooltip>
                                <TooltipTrigger as-child>
                                  <AlertDialogTrigger as-child>
                                    <Button variant="ghost" size="icon" class="h-8 w-8 text-red-500 hover:text-red-400" title="删除">
                                      <Trash2 class="w-4 h-4" />
                                    </Button>
                                  </AlertDialogTrigger>
                                </TooltipTrigger>
                                <TooltipContent>删除</TooltipContent>
                              </Tooltip>
                            </AlertDialog>
                          </div>
                        </TableCell>
                      </TableRow>
                    </template>

                    <TableRow v-if="flattenedDepartments.length === 0">
                      <TableCell colspan="5" class="text-center py-8 text-muted-foreground">
                        <Building2 class="w-12 h-12 mx-auto mb-2 opacity-50" />
                        暂无部门数据
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <Sheet v-model:open="isDialogOpen">
        <SheetContent side="right" class="w-[480px] sm:max-w-[480px] flex flex-col">
          <SheetHeader>
            <div class="flex items-center gap-2">
              <Building2 class="w-5 h-5 text-primary" />
              <SheetTitle>{{ deptForm.id ? '编辑部门' : '新建部门' }}</SheetTitle>
            </div>
            <SheetDescription>
              {{ deptForm.id ? '修改部门信息，所有变更将被记录' : '创建一个新的部门，可作为现有部门的子部门' }}
            </SheetDescription>
          </SheetHeader>

          <ScrollArea class="flex-1 mt-4">
            <div class="space-y-4 pr-4">
              <div class="grid gap-2">
                <Label for="deptName" class="flex items-center gap-1">
                  部门名称
                  <span class="text-destructive">*</span>
                  <Info class="w-3 h-3 text-muted-foreground" />
                </Label>
                <Input
                  id="deptName"
                  v-model="deptForm.name"
                  placeholder="请输入部门名称（至少2个字符）"
                  :class="cn(formErrors.name && 'border-destructive focus:ring-destructive')"
                  @input="formErrors.name && delete formErrors.name"
                />
                <p v-if="formErrors.name" class="text-xs text-destructive flex items-center gap-1">
                  <AlertCircle class="w-3 h-3" />
                  {{ formErrors.name }}
                </p>
              </div>
              <div class="grid gap-2">
                <Label for="deptCode" class="flex items-center gap-1">
                  部门代码
                  <span class="text-destructive">*</span>
                  <Badge variant="outline" class="text-xs ml-auto">如: TECH, HR</Badge>
                </Label>
                <Input
                  id="deptCode"
                  v-model="deptForm.code"
                  placeholder="大写字母或数字"
                  class="font-mono uppercase"
                  :class="cn(formErrors.code && 'border-destructive')"
                  @input="deptForm.code = deptForm.code.toUpperCase(); formErrors.code && delete formErrors.code"
                />
                <p v-if="formErrors.code" class="text-xs text-destructive flex items-center gap-1">
                  <AlertCircle class="w-3 h-3" />
                  {{ formErrors.code }}
                </p>
              </div>
              <div class="grid gap-2">
                <Label for="parentDept">上级部门</Label>
                <Select v-model="parentSelectValue" @update:modelValue="(v: string) => { deptForm.parent_id = v === 'none' ? undefined : Number(v); }">
                  <SelectTrigger id="parentDept" :class="cn(parentSelectValue === 'none' && 'text-muted-foreground')">
                    <SelectValue placeholder="选择上级部门（可选）" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectLabel>上级部门</SelectLabel>
                      <SelectItem value="none">无（作为顶级部门）</SelectItem>
                      <SelectItem v-for="dept in availableParents" :key="dept.id" :value="String(dept.id || 'unknown')">
                        {{ dept.name }}
                        <span class="text-xs text-muted-foreground ml-2">{{ dept.code }}</span>
                      </SelectItem>
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div class="grid gap-2">
                  <Label for="leader">负责人</Label>
                  <Input id="leader" v-model="deptForm.leader" placeholder="部门负责人姓名" />
                </div>
                <div class="grid gap-2">
                  <Label for="phone">联系电话</Label>
                  <Input
                    id="phone"
                    v-model="deptForm.phone"
                    placeholder="手机号码"
                    :class="cn(formErrors.phone && 'border-destructive')"
                    @input="formErrors.phone && delete formErrors.phone"
                  />
                </div>
              </div>
              <div class="grid gap-2">
                <Label for="desc">部门描述</Label>
                <Input id="desc" v-model="deptForm.description" placeholder="简要描述部门职能" />
              </div>
            </div>
          </ScrollArea>

          <SheetFooter class="gap-2 sm:gap-4 mt-4 pt-4 border-t">
            <Button variant="outline" @click="isDialogOpen = false">取消</Button>
            <Button @click="handleSaveDept" :disabled="operationInProgress">
              <Loader2 v-if="operationInProgress" class="w-4 h-4 mr-2 animate-spin" />
              {{ deptForm.id ? '保存修改' : '创建部门' }}
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>

      <AlertDialog v-model:open="isDeleteDialogOpen">
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle class="flex items-center gap-2 text-destructive">
              <AlertTriangle class="w-5 h-5" />
              确认删除部门
            </AlertDialogTitle>
            <AlertDialogDescription as-child>
              <div class="space-y-3">
                <p>
                  确定要删除部门 <strong class="text-foreground">"{{ currentDept?.name }}"</strong> 吗？
                </p>
                <div v-if="currentDept && (currentDeptChildrenCount > 0 || usersInDepartment.length > 0)" class="p-3 bg-destructive/10 rounded-lg border border-destructive/20">
                  <div class="flex items-start gap-2">
                    <AlertTriangle class="w-4 h-4 text-destructive mt-0.5 flex-shrink-0" />
                    <div class="text-sm">
                      <p class="font-medium text-destructive">无法删除此部门</p>
                      <ul class="mt-1 space-y-1 text-muted-foreground">
                        <li v-if="currentDeptChildrenCount > 0">
                          该部门有 {{ currentDeptChildrenCount }} 个子部门需先删除
                        </li>
                        <li v-if="usersInDepartment.length > 0">
                          该部门有 {{ usersInDepartment.length }} 名成员需先转移
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
                <p v-else class="text-sm text-muted-foreground">
                  此操作不可恢复，部门的所有信息将被永久删除。
                </p>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              @click="handleDeleteDept"
              class="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              :disabled="operationInProgress || (currentDept !== null && (currentDeptChildrenCount > 0 || usersInDepartment.length > 0))"
            >
              <Loader2 v-if="operationInProgress" class="w-4 h-4 mr-2 animate-spin" />
              确认删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Sheet v-model:open="isTransferDialogOpen">
        <SheetContent side="right" class="w-[480px] sm:max-w-[480px] flex flex-col" :onInteractOutside="(e: Event) => e.preventDefault()">
          <SheetHeader>
            <div class="flex items-center gap-2">
              <ArrowRightLeft class="w-5 h-5 text-primary" />
              <SheetTitle>调整部门成员</SheetTitle>
            </div>
            <SheetDescription>
              将用户转移至部门 <strong>"{{ selectedDepartment?.name }}"</strong>。
              选择用户后点击"确认转移"完成操作。
            </SheetDescription>
          </SheetHeader>
          <ScrollArea class="flex-1 mt-4">
            <div class="py-4 pr-4">
              <div class="mb-4">
              <div class="flex items-center justify-between mb-2">
                <Label class="text-sm font-medium">待转移用户</Label>
                <span class="text-xs text-muted-foreground">
                  已选择 {{ selectedUserIds.length }} 名
                </span>
              </div>
              <div class="mt-2 max-h-[300px] overflow-y-auto border rounded-lg p-2 space-y-2">
                <div
                  v-for="user in usersNotInDepartment"
                  :key="user.id"
                  :class="cn(
                    'flex items-center gap-3 p-3 rounded-md cursor-pointer transition-all duration-200',
                    'hover:bg-muted/50 dark:hover:bg-slate-800/50',
                    selectedUserIds.includes(user.id) && 'bg-primary/10 dark:bg-primary/20 ring-2 ring-primary/50'
                  )"
                  @click="selectedUserIds.includes(user.id) ? selectedUserIds = selectedUserIds.filter(id => id !== user.id) : selectedUserIds.push(user.id)"
                >
                  <input
                    type="checkbox"
                    :checked="selectedUserIds.includes(user.id)"
                    class="rounded border-input"
                    @click.stop
                  />
                  <div class="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-sm font-medium text-primary">
                    {{ user.username.charAt(0).toUpperCase() }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm dark:text-slate-200 truncate font-medium">{{ user.username }}</p>
                    <p class="text-xs text-muted-foreground truncate">{{ user.email }}</p>
                  </div>
                  <Badge v-if="user.department_id" variant="secondary" class="text-xs">
                    {{ user.department_name }}
                  </Badge>
                  <Badge v-else variant="outline" class="text-xs text-muted-foreground">未分配</Badge>
                </div>
                <p v-if="usersNotInDepartment.length === 0" class="text-sm text-muted-foreground text-center py-6">
                  <Users class="w-8 h-8 mx-auto mb-2 opacity-50" />
                  所有用户都已在该部门
                </p>
              </div>
            </div>

            <div v-if="selectedUserIds.length > 0" class="flex items-center justify-between p-4 bg-primary/5 dark:bg-primary/10 rounded-lg border border-primary/20">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                  <CheckCircle class="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p class="text-sm font-medium">已选择 {{ selectedUserIds.length }} 名用户</p>
                  <p class="text-xs text-muted-foreground">确认后将被转移至 "{{ selectedDepartment?.name }}"</p>
                </div>
              </div>
              <Button size="sm" @click="handleTransferUsers" :disabled="operationInProgress">
                <Loader2 v-if="operationInProgress" class="w-4 h-4 mr-2 animate-spin" />
                确认转移
              </Button>
            </div>
            </div>
          </ScrollArea>
          <SheetFooter class="gap-2 sm:gap-4 mt-4 pt-4 border-t">
            <Button variant="outline" @click="isTransferDialogOpen = false">关闭</Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </div>
  </TooltipProvider>
</template>
