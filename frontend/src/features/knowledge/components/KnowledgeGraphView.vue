<template>
    <div class="flex h-full overflow-hidden bg-white">
        <!-- Left: Graph -->
        <div class="flex-1 relative">
            <KnowledgeGraphViewer
                ref="viewerRef"
                :doc-id="docId"
                :initial-scope="initialScope"
                :show-chat="showChat"
                @toggle-chat="showChat = !showChat"
                @nodes-updated="handleNodesUpdated"
                @scope-changed="handleScopeChanged"
            />
        </div>

        <!-- Right: Chat -->
        <KnowledgeQAPanel
            :visible="showChat"
            :doc-id="docId"
            :scope="currentScope"
            :nodes="graphNodes"
            @close="showChat = false"
            @locate-node="handleLocateNode"
        />
    </div>
</template>

<script setup lang="ts">
import { ref, defineAsyncComponent, shallowRef } from 'vue';
import { message } from 'ant-design-vue';

// Async Components
const KnowledgeGraphViewer = defineAsyncComponent(() => 
    import('./KnowledgeGraphViewer.vue')
);
const KnowledgeQAPanel = defineAsyncComponent(() => 
    import('./KnowledgeQAPanel.vue')
);

const props = defineProps<{
    docId?: number | string | null;
    initialScope?: string;
}>();

// State
const showChat = ref(false);
const graphNodes = shallowRef({});
const currentScope = ref(props.initialScope || 'doc');
const viewerRef = ref<any>(null);

// Handlers
const handleNodesUpdated = (nodes: any) => {
    graphNodes.value = nodes;
};

const handleScopeChanged = (scope: string) => {
    currentScope.value = scope;
};

const handleLocateNode = (nodeId: string) => {
    if (viewerRef.value) {
        viewerRef.value.focusNode(nodeId);
        
        // Find node name for feedback
        const node = (graphNodes.value as any)[nodeId];
        const nodeName = node?.name || nodeId;
        message.success(`已定位: ${nodeName}`);
    } else {
        message.warning('图谱组件未就绪');
    }
};
</script>
