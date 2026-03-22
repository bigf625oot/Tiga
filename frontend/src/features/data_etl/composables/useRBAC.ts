import { ref, computed, readonly } from 'vue';
import { roleApi, type Role as RoleType } from '../api';

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
    id: 'knowledge_base',
    name: '公共知识库管理',
    resources: []
  },
  {
    id: 'agent',
    name: '公共智能体管理',
    resources: []
  }
];

export function useRBAC() {
  const normalizePermissions = (codes: string[]) => Array.from(new Set(codes)).sort();

  const roles = ref<Role[]>([]);
  const originalRoles = ref<Role[]>([]);
  const activeRoleId = ref<string | null>(null);
  const hasUnsavedChanges = ref(false);
  const isLoading = ref(false);

  const activeRole = computed(() => roles.value.find(r => r.id === activeRoleId.value));

  const fetchRoles = async () => {
    isLoading.value = true;
    try {
      const data = await roleApi.list();
      roles.value = data.map(r => ({
        id: r.id,
        name: r.name,
        code: r.code,
        description: r.description ?? '',
        isSystem: r.is_system ?? false,
        userCount: r.userCount,
        permissions: r.permissions ?? []
      }));
      originalRoles.value = JSON.parse(JSON.stringify(roles.value));
      if (roles.value.length > 0 && !activeRoleId.value) {
        activeRoleId.value = roles.value[0].id;
      }
    } finally {
      isLoading.value = false;
    }
  };

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
    if (!activeRole.value) return;
    await roleApi.update(activeRole.value.id, {
      permissions: activeRole.value.permissions
    });
    const idx = originalRoles.value.findIndex(r => r.id === activeRole.value!.id);
    if (idx !== -1) {
      originalRoles.value[idx] = JSON.parse(JSON.stringify(activeRole.value));
    }
    hasUnsavedChanges.value = false;
  };

  const discardChanges = () => {
    const idx = roles.value.findIndex(r => r.id === activeRoleId.value);
    if (idx !== -1) {
      roles.value[idx] = JSON.parse(JSON.stringify(originalRoles.value[idx]));
    }
    hasUnsavedChanges.value = false;
  };

  const addRole = async (newRole: Omit<Role, 'id' | 'isSystem' | 'userCount' | 'permissions'>) => {
    const created = await roleApi.create({
      name: newRole.name,
      code: newRole.code,
      description: newRole.description,
      permissions: []
    });
    const role: Role = {
      id: created.id,
      name: created.name,
      code: created.code,
      description: created.description ?? '',
      isSystem: created.is_system ?? false,
      userCount: created.userCount,
      permissions: created.permissions ?? []
    };
    roles.value.push(role);
    originalRoles.value.push(JSON.parse(JSON.stringify(role)));
    selectRole(role.id);
    return role;
  };

  const deleteRole = async (id: string) => {
    await roleApi.delete(id);
    roles.value = roles.value.filter(r => r.id !== id);
    originalRoles.value = originalRoles.value.filter(r => r.id !== id);
    if (activeRoleId.value === id && roles.value.length > 0) {
      activeRoleId.value = roles.value[0].id;
    }
  };

  fetchRoles();

  return {
    roles,
    activeRoleId,
    activeRole,
    hasUnsavedChanges: readonly(hasUnsavedChanges),
    isLoading: readonly(isLoading),
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
    deleteRole,
    MODULES
  };
}
