import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useWorkflowStore } from '../workflow.store';

describe('Workflow Store Graph Logic', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('should add a new node to the graph when updateGraph is called', () => {
    const store = useWorkflowStore();
    
    const task = {
      id: 'task-1',
      name: 'Test Task',
      status: 'pending',
      logs: [],
      dependencies: []
    };

    store.updateGraph(task);

    expect(store.graph.nodes).toHaveLength(1);
    expect(store.graph.nodes[0].id).toBe('task-1');
    expect(store.graph.nodes[0].data.label).toBe('Test Task');
  });

  it('should update an existing node in the graph', () => {
    const store = useWorkflowStore();
    
    const task = {
      id: 'task-1',
      name: 'Test Task',
      status: 'pending',
      logs: [],
      dependencies: []
    };

    store.updateGraph(task);
    
    // Update status
    const updatedTask = { ...task, status: 'running', progress: 50 };
    store.updateGraph(updatedTask);

    expect(store.graph.nodes).toHaveLength(1);
    expect(store.graph.nodes[0].data.status).toBe('running');
    expect(store.graph.nodes[0].data.progress).toBe(50);
  });

  it('should create edges for dependencies', () => {
    const store = useWorkflowStore();
    
    // Create parent task
    store.updateGraph({
      id: 'task-1',
      name: 'Parent',
      status: 'completed',
      logs: [],
      dependencies: []
    });

    // Create child task
    store.updateGraph({
      id: 'task-2',
      name: 'Child',
      status: 'pending',
      logs: [],
      dependencies: ['task-1']
    });

    expect(store.graph.nodes).toHaveLength(2);
    expect(store.graph.edges).toHaveLength(1);
    expect(store.graph.edges[0].source).toBe('task-1');
    expect(store.graph.edges[0].target).toBe('task-2');
  });
});
