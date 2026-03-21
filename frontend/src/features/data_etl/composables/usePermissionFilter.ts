import { computed, ref, type Ref } from 'vue';
import type { ModuleDef, ResourceDef, ActionDef } from './useRBAC';

export function usePermissionFilter(
  MODULES: ModuleDef[],
  hasPermission: (resourceId: string, actionId: string) => boolean
) {
  const query = ref('');
  const showGrantedOnly = ref(false);
  const actionFilter = ref<string[]>([]);

  const q = computed(() => query.value.trim().toLowerCase());
  const match = (text: string) => text.toLowerCase().includes(q.value);

  // Available actions for filter buttons
  const availableActions = computed(() => {
    const map = new Map<string, string>();
    for (const m of MODULES) {
      for (const r of m.resources) {
        for (const a of r.actions) {
          if (!map.has(a.id)) map.set(a.id, a.name);
        }
      }
    }
    return Array.from(map.entries()).map(([id, name]) => ({ id, name }));
  });

  const toggleAction = (id: string) => {
    const set = new Set(actionFilter.value);
    if (set.has(id)) set.delete(id);
    else set.add(id);
    actionFilter.value = Array.from(set);
  };

  const clearActionFilter = () => {
    actionFilter.value = [];
  };

  const actionsToShow = (moduleId: string, resourceId: string, resourceName: string, actions: ActionDef[]) => {
    let next = actions;
    if (actionFilter.value.length > 0) {
      const set = new Set(actionFilter.value);
      next = next.filter((a) => set.has(a.id));
    }

    if (q.value) {
      const resourceHit = match(moduleId) || match(resourceName) || match(resourceId);
      if (!resourceHit) next = next.filter((a) => match(a.id) || match(a.name));
    }

    if (showGrantedOnly.value) {
      next = next.filter((a) => hasPermission(resourceId, a.id));
    }

    return next;
  };

  const resourcesForModule = (moduleId: string) => {
    const module = MODULES.find((m) => m.id === moduleId);
    if (!module) return [];

    return module.resources
      .map((r) => {
        const visibleActions = actionsToShow(module.id, r.id, r.name, r.actions);
        return { resource: r, actions: visibleActions };
      })
      .filter(({ resource, actions }) => {
        if (actions.length === 0) return false;
        if (!q.value) return true;
        return (
          match(module.id) ||
          match(module.name) ||
          match(resource.id) ||
          match(resource.name) ||
          resource.actions.some((a) => match(a.id) || match(a.name))
        );
      });
  };

  const getVisiblePermissionCodesInModule = (moduleId: string) => {
    const items = resourcesForModule(moduleId);
    const codes: string[] = [];
    for (const { resource, actions } of items) {
      for (const a of actions) codes.push(`${resource.id}:${a.id}`);
    }
    return codes;
  };

  return {
    query,
    showGrantedOnly,
    actionFilter,
    availableActions,
    toggleAction,
    clearActionFilter,
    resourcesForModule,
    getVisiblePermissionCodesInModule,
  };
}
