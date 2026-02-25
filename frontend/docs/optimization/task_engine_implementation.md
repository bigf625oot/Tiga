# Task Engine Implementation Guide

## 1. TaskPanel.vue Upgrade

### Features
- **DAG Visualization**: Replace simple list with a node-based graph.
- **Task Control**: Pause/Resume/Retry buttons on each node.
- **Log Streaming**: Optimized rendering for large logs (virtual scrolling).

### Component Structure
- `TaskGraph.vue`: Uses `VueFlow` to render task dependencies.
- `TaskNode.vue`: Custom node component showing Status Icon, Name, Priority.
- `TaskDetailDrawer.vue`: Shows full logs, input/output data.

### Data Flow
1.  **Init**: `workflowStore.initWorkflow()` fetches initial DAG.
2.  **Stream**: `EventSource` receives `agent_task_update`.
3.  **Update**:
    - If `status` changes -> Update Node color/icon.
    - If `logs` append -> Update Store, show indicator on Node.
    - If `new_task` -> Add Node & Edge to Graph.

## 2. Code Runtime (ArtifactEditor) Upgrade

### Features
- **Monaco Editor**: Replace `ArtifactEditor` with full Monaco instance.
- **Diff View**: Show changes between `v1` and `v2` of generated code.
- **Run Button**: Execute code in Sandbox context directly.

### Integration
- **Props**:
    - `code`: string
    - `language`: string
    - `readOnly`: boolean
- **Events**:
    - `run`: Emitted when user clicks Run. Payload: `{ code, selection }`.
    - `save`: Emitted on Ctrl+S.

### Code Snippet (Monaco Setup)

```ts
import { loader } from "@guolao/vue-monaco-editor";

loader.config({
  paths: {
    vs: "https://cdn.jsdelivr.net/npm/monaco-editor@0.43.0/min/vs",
  },
});

// Diff Editor Configuration
const diffOptions = {
    renderSideBySide: false,
    readOnly: true
};
```

## 3. Store Updates (workflow.store.ts)

### New State
```ts
interface TaskGraph {
    nodes: Node[];
    edges: Edge[];
}

state: () => ({
    // ... existing
    graph: { nodes: [], edges: [] } as TaskGraph,
    selectedTaskId: null as string | null,
})
```

### New Actions
```ts
updateGraph(task: WorkflowTask) {
    // Logic to convert Task to Graph Node
    const node = {
        id: task.id,
        type: 'custom',
        data: { label: task.name, status: task.status },
        position: { x: 0, y: 0 } // Layout needed (dagre?)
    };
    // Add edges based on dependencies
}
```
