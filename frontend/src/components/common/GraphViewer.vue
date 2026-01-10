<template>
  <div class="graph-container">
    <v-network-graph
      v-if="nodes && Object.keys(nodes).length > 0"
      class="graph"
      :nodes="nodes"
      :edges="edges"
      :configs="configs"
    >
      <template #edge-label="{ edge, ...slotProps }">
        <v-edge-label :text="edge.label" align="center" vertical-align="above" v-bind="slotProps" />
      </template>
    </v-network-graph>
    <div v-else class="flex items-center justify-center h-full text-gray-400">
      暂无图谱数据
    </div>
  </div>
</template>

<script setup>
import { defineProps, reactive } from "vue"
import * as vNG from "v-network-graph"

const props = defineProps({
  nodes: Object,
  edges: Object
})

const configs = reactive(
  vNG.defineConfigs({
    node: {
      normal: {
        type: "circle",
        radius: 24,
        color: "#4466cc",
      },
      label: {
        visible: true,
        direction: "south",
        color: "#000000",
        fontSize: 12,
      },
    },
    edge: {
        normal: {
            color: "#aaaaaa",
            width: 2,
        },
        marker: {
            target: {
                type: "arrow",
                width: 4,
                height: 4,
            }
        },
        label: {
            fontSize: 11,
            color: "#666666"
        }
    }
  })
)
</script>

<style scoped>
.graph-container {
  width: 100%;
  height: 600px;
  background-color: #f9f9fa;
  border-radius: 8px;
  border: 1px solid #e5e6eb;
}
.graph {
  width: 100%;
  height: 100%;
}
</style>
