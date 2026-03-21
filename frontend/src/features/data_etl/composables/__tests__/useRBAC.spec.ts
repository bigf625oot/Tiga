import { describe, it, expect, beforeEach } from 'vitest';
import { useRBAC, MOCK_ROLES } from '../useRBAC';

describe('useRBAC', () => {
  it('should initialize with mock roles and select the first role', () => {
    const { roles, activeRole, activeRoleId } = useRBAC();
    expect(roles.value.length).toBe(MOCK_ROLES.length);
    expect(activeRoleId.value).toBe(MOCK_ROLES[0].id);
    expect(activeRole.value?.id).toBe(MOCK_ROLES[0].id);
  });

  it('admin role should have all permissions by default', () => {
    const { hasPermission, isRowFullySelected, MODULES } = useRBAC();
    // Admin is the first role, and it has '*' permission
    expect(hasPermission('datasource', 'read')).toBe(true);
    expect(hasPermission('dataset', 'delete')).toBe(true);
    expect(isRowFullySelected(MODULES[0].resources[0])).toBe(true);
  });

  it('should not allow modifying admin permissions', () => {
    const { togglePermission, replaceActiveRolePermissions, bulkTogglePermissions, hasPermission, hasUnsavedChanges } = useRBAC();
    togglePermission('datasource', 'read', false);
    // Because it's admin ('*'), it should not be modifiable
    expect(hasPermission('datasource', 'read')).toBe(true);
    expect(hasUnsavedChanges.value).toBe(false);

    replaceActiveRolePermissions(['dataset:read']);
    expect(hasPermission('dataset', 'read')).toBe(true);
    expect(hasUnsavedChanges.value).toBe(false);

    bulkTogglePermissions(['dataset:delete'], true);
    expect(hasPermission('dataset', 'delete')).toBe(true);
    expect(hasUnsavedChanges.value).toBe(false);
  });

  it('should allow modifying normal role permissions', () => {
    const { selectRole, activeRoleId, hasPermission, togglePermission, hasUnsavedChanges } = useRBAC();
    // Select data engineer role
    selectRole('2');
    expect(activeRoleId.value).toBe('2');
    
    // Initially has datasource:read
    expect(hasPermission('datasource', 'read')).toBe(true);
    // Initially does not have dataset:delete
    expect(hasPermission('dataset', 'delete')).toBe(false);

    // Toggle permission
    togglePermission('dataset', 'delete', true);
    expect(hasPermission('dataset', 'delete')).toBe(true);
    expect(hasUnsavedChanges.value).toBe(true);
    
    // Toggle off
    togglePermission('datasource', 'read', false);
    expect(hasPermission('datasource', 'read')).toBe(false);
  });

  it('should support replacing active role permissions', () => {
    const { selectRole, hasPermission, replaceActiveRolePermissions, hasUnsavedChanges } = useRBAC();
    selectRole('2');
    replaceActiveRolePermissions(['dataset:read', 'dataset:export']);
    expect(hasPermission('dataset', 'read')).toBe(true);
    expect(hasPermission('dataset', 'export')).toBe(true);
    expect(hasPermission('datasource', 'read')).toBe(false);
    expect(hasUnsavedChanges.value).toBe(true);
  });

  it('should support bulk toggling permissions', () => {
    const { selectRole, hasPermission, bulkTogglePermissions } = useRBAC();
    selectRole('3');

    bulkTogglePermissions(['dataset:write', 'dataset:delete'], true);
    expect(hasPermission('dataset', 'write')).toBe(true);
    expect(hasPermission('dataset', 'delete')).toBe(true);

    bulkTogglePermissions(['dataset:read', 'dataset:export'], false);
    expect(hasPermission('dataset', 'read')).toBe(false);
    expect(hasPermission('dataset', 'export')).toBe(false);
  });

  it('should prevent selecting another role when there are unsaved changes', () => {
    const { selectRole, togglePermission } = useRBAC();
    selectRole('2');
    togglePermission('dataset', 'delete', true); // Modify state
    
    // Attempting to select another role should throw error
    expect(() => selectRole('3')).toThrow('UNSAVED_CHANGES');
  });

  it('should support discarding changes', () => {
    const { selectRole, togglePermission, hasPermission, discardChanges, hasUnsavedChanges } = useRBAC();
    selectRole('2');
    togglePermission('dataset', 'delete', true);
    expect(hasPermission('dataset', 'delete')).toBe(true);
    
    discardChanges();
    expect(hasUnsavedChanges.value).toBe(false);
    expect(hasPermission('dataset', 'delete')).toBe(false);
  });

  it('should support saving changes', async () => {
    const { selectRole, togglePermission, saveConfig, hasUnsavedChanges, discardChanges, hasPermission } = useRBAC();
    selectRole('2');
    togglePermission('dataset', 'delete', true);
    
    await saveConfig();
    expect(hasUnsavedChanges.value).toBe(false);
    
    // Even if we discard after saving, the new state should persist
    discardChanges();
    expect(hasPermission('dataset', 'delete')).toBe(true);
  });

  it('should support row full selection', () => {
    const { selectRole, toggleRowSelection, isRowFullySelected, hasPermission, MODULES } = useRBAC();
    selectRole('3'); // Data Analyst
    const datasetResource = MODULES[0].resources[1]; // dataset
    
    expect(isRowFullySelected(datasetResource)).toBe(false);
    
    toggleRowSelection(datasetResource, true);
    
    expect(isRowFullySelected(datasetResource)).toBe(true);
    expect(hasPermission('dataset', 'read')).toBe(true);
    expect(hasPermission('dataset', 'write')).toBe(true);
    expect(hasPermission('dataset', 'delete')).toBe(true);
    expect(hasPermission('dataset', 'export')).toBe(true);
  });
});
