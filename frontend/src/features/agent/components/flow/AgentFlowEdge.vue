<script setup lang="ts">
import { computed, ref } from 'vue';
import { BaseEdge, EdgeLabelRenderer, getBezierPath, useVueFlow, type EdgeProps } from '@vue-flow/core';
import { Trash2 } from 'lucide-vue-next';

const props = defineProps<EdgeProps>();

const { removeEdges } = useVueFlow();
const path = computed(() => getBezierPath(props));
const isHovered = ref(false);

const onEdgeClick = (event: Event) => {
  // Optional: Add logic for edge click if needed
};

const onDelete = () => {
  removeEdges(props.id);
};
</script>

<template>
  <!-- Invisible interaction path for easier hovering -->
  <path
    :d="path[0]"
    class="vue-flow__edge-interaction"
    :stroke-width="20"
    stroke="transparent"
    fill="none"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
    @click="onEdgeClick"
    style="pointer-events: stroke; cursor: pointer;"
  />

  <BaseEdge 
    :path="path[0]" 
    :marker-end="markerEnd" 
    :style="{
        ...style,
        stroke: isHovered || selected ? 'hsl(var(--primary))' : '#94a3b8',
        strokeWidth: isHovered || selected ? 3 : 2,
        transition: 'all 0.2s ease'
    }" 
  />

  <EdgeLabelRenderer>
    <div
      v-if="isHovered || selected"
      :style="{
        pointerEvents: 'all',
        position: 'absolute',
        transform: `translate(-50%, -50%) translate(${path[1]}px,${path[2]}px)`,
        zIndex: 10,
      }"
      class="nodrag nopan"
      @mouseenter="isHovered = true"
      @mouseleave="isHovered = false"
    >
      <button 
        class="p-1.5 bg-background border rounded-full shadow-md hover:bg-red-50 hover:text-red-600 transition-colors text-muted-foreground flex items-center justify-center"
        title="删除连线"
        @click="onDelete"
      >
        <Trash2 class="w-3.5 h-3.5" />
      </button>
    </div>
  </EdgeLabelRenderer>
</template>
