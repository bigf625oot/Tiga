import { defineAsyncComponent } from 'vue';

// Using defineAsyncComponent for lazy loading blocks to improve initial render performance
export const BlockRendererRegistry: Record<string, any> = {
  thought: defineAsyncComponent(() => import('./ThoughtAccordion.vue')),
  plan: defineAsyncComponent(() => import('./PlanBlock.vue')),
  tool_call: defineAsyncComponent(() => import('./blocks/ToolBlockRenderer.vue')),
  action: defineAsyncComponent(() => import('./blocks/ActionBlockRenderer.vue')),
  terminal: defineAsyncComponent(() => import('./TerminalBlock.vue')),
  text: defineAsyncComponent(() => import('./blocks/TextBlockRenderer.vue')),
  search: defineAsyncComponent(() => import('./blocks/SearchBlockRenderer.vue')),
  visualization: defineAsyncComponent(() => import('./blocks/VisualizationBlockRenderer.vue')),
  resource: defineAsyncComponent(() => import('./blocks/ResourceBlockRenderer.vue')),
  references: defineAsyncComponent(() => import('./blocks/ReferencesBlockRenderer.vue')),
  error: defineAsyncComponent(() => import('./blocks/ErrorBlockRenderer.vue')),
  solo_layout: defineAsyncComponent(() => import('./blocks/SoloLayoutBlockRenderer.vue')),
  sandbox: defineAsyncComponent(() => import('./blocks/SandboxBlockRenderer.vue')),
  kb_retrieval: defineAsyncComponent(() => import('./blocks/KbRetrievalBlockRenderer.vue'))
};
