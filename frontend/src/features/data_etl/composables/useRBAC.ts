import { ref, computed, readonly } from 'vue';

export interface ActionDef {
  id: string;
  name: string;
  description?: string;
}

export interface ResourceDef {
  id: string;
  name: string;
  actions: ActionDef[];
}

export interface ModuleDef {
  id: string;
  name: string;
  resources: ResourceDef[];
}

export interface Role {
  id: string;
  name: string;
  code: string;
  description: string;
  isSystem: boolean;
  userCount: number;
  permissions: string[];
}

export const MODULES: ModuleDef[] = [
  {
    id: 'data_integration',
    name: '数据集成',
    resources: [
      { id: 'datasource', name: '数据源', actions: [{ id: 'read', name: '查看' }, { id: 'write', name: '编辑' }, { id: 'delete', name: '删除' }] },
      { id: 'dataset', name: '数据集', actions: [{ id: 'read', name: '查看' }, { id: 'write', name: '编辑' }, { id: 'delete', name: '删除' }, { id: 'export', name: '导出' }] },
    ]
  },
  {
    id: 'pipeline',
    name: '数据管道',
    resources: [
      { id: 'job', name: '作业任务', actions: [{ id: 'read', name: '查看' }, { id: 'write', name: '编辑' }, { id: 'execute', name: '执行' }, { id: 'delete', name: '删除' }] },
      { id: 'schedule', name: '调度配置', actions: [{ id: 'read', name: '查看' }, { id: 'write', name: '编辑' }] },
    ]
  },
  {
    id: 'system',
    name: '系统设置',
    resources: [
      { id: 'user', name: '用户管理', actions: [{ id: 'read', name: '查看' }, { id: 'write', name: '编辑' }, { id: 'delete', name: '删除' }] },
      { id: 'role', name: '角色权限', actions: [{ id: 'read', name: '查看' }, { id: 'write', name: '编辑' }] },
    ]
  }
];

export const MOCK_ROLES: Role[] = [
  { id: '1', name: '超级管理员', code: 'admin', description: '系统最高权限，不可删除', isSystem: true, userCount: 2, permissions: ['*'] },
  { id: '2', name: '数据工程师', code: 'data_eng', description: '负责数据集成与管道开发', isSystem: false, userCount: 15, permissions: ['datasource:read', 'datasource:write', 'dataset:read', 'dataset:write', 'job:read', 'job:write', 'job:execute', 'schedule:read', 'schedule:write'] },
  { id: '3', name: '数据分析师', code: 'data_analyst', description: '只读权限，可导出数据', isSystem: false, userCount: 25, permissions: ['datasource:read', 'dataset:read', 'dataset:export', 'job:read'] },
];

export function useRBAC() {
  const normalizePermissions = (codes: string[]) => Array.from(new Set(codes)).sort();

  // Snapshot for discarding changes
  const originalRoles = ref<Role[]>(JSON.parse(JSON.stringify(MOCK_ROLES)));
  const roles = ref<Role[]>(JSON.parse(JSON.stringify(MOCK_ROLES)));
  
  const activeRoleId = ref<string>(roles.value[0].id);
  const hasUnsavedChanges = ref(false);

  const activeRole = computed(() => roles.value.find(r => r.id === activeRoleId.value));

  const selectRole = (id: string) => {
    if (hasUnsavedChanges.value) {
      throw new Error('UNSAVED_CHANGES');
    }
    activeRoleId.value = id;
  };

  const hasPermission = (resourceId: string, actionId: string) => {
    if (!activeRole.value) return false;
    if (activeRole.value.permissions.includes('*')) return true;
    return activeRole.value.permissions.includes(`${resourceId}:${actionId}`);
  };

  const togglePermission = (resourceId: string, actionId: string, checked: boolean) => {
    if (!activeRole.value || activeRole.value.permissions.includes('*')) return;
    
    hasUnsavedChanges.value = true;
    const perm = `${resourceId}:${actionId}`;
    
    if (checked) {
      if (!activeRole.value.permissions.includes(perm)) {
        activeRole.value.permissions.push(perm);
      }
    } else {
      activeRole.value.permissions = activeRole.value.permissions.filter(p => p !== perm);
    }
  };

  const replaceActiveRolePermissions = (permissionCodes: string[]) => {
    if (!activeRole.value || activeRole.value.permissions.includes('*') || activeRole.value.isSystem) return;
    hasUnsavedChanges.value = true;
    activeRole.value.permissions = normalizePermissions(permissionCodes);
  };

  const bulkTogglePermissions = (permissionCodes: string[], checked: boolean) => {
    if (!activeRole.value || activeRole.value.permissions.includes('*') || activeRole.value.isSystem) return;

    if (permissionCodes.length === 0) return;
    hasUnsavedChanges.value = true;

    if (checked) {
      const set = new Set(activeRole.value.permissions);
      for (const code of permissionCodes) set.add(code);
      activeRole.value.permissions = normalizePermissions(Array.from(set));
      return;
    }

    const removeSet = new Set(permissionCodes);
    activeRole.value.permissions = activeRole.value.permissions.filter((p) => !removeSet.has(p));
  };

  const isRowFullySelected = (resource: ResourceDef) => {
    if (!activeRole.value) return false;
    if (activeRole.value.permissions.includes('*')) return true;
    return resource.actions.every((a) => activeRole.value!.permissions.includes(`${resource.id}:${a.id}`));
  };

  const toggleRowSelection = (resource: ResourceDef, checked: boolean) => {
    if (!activeRole.value || activeRole.value.permissions.includes('*')) return;
    hasUnsavedChanges.value = true;
    resource.actions.forEach((a) => {
      togglePermission(resource.id, a.id, checked);
    });
  };

  const saveConfig = async () => {
    // Simulate API call to save config
    return new Promise((resolve) => {
      setTimeout(() => {
        originalRoles.value = JSON.parse(JSON.stringify(roles.value));
        hasUnsavedChanges.value = false;
        resolve(true);
      }, 500);
    });
  };

  const discardChanges = () => {
    roles.value = JSON.parse(JSON.stringify(originalRoles.value));
    hasUnsavedChanges.value = false;
  };

  const addRole = (newRole: Omit<Role, 'id' | 'isSystem' | 'userCount' | 'permissions'>) => {
    const role: Role = {
      ...newRole,
      id: Date.now().toString(),
      isSystem: false,
      userCount: 0,
      permissions: []
    };
    roles.value.push(role);
    originalRoles.value.push(JSON.parse(JSON.stringify(role))); // Assume adding role saves it directly
    selectRole(role.id);
  };

  return {
    roles,
    activeRoleId,
    activeRole,
    hasUnsavedChanges: readonly(hasUnsavedChanges),
    selectRole,
    hasPermission,
    togglePermission,
    replaceActiveRolePermissions,
    bulkTogglePermissions,
    isRowFullySelected,
    toggleRowSelection,
    saveConfig,
    discardChanges,
    addRole,
    MODULES
  };
}
