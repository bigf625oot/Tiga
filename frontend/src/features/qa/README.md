# QA Feature Module

This module handles the Smart QA (Question Answering) features, including Chat, Workflow (Team) mode, and Auto Task (Openclaw) mode.

## Architecture

The module is organized following a feature-based architecture with clear separation of concerns:

```
src/features/qa/
├── components/           # UI Components
│   ├── SmartQA.vue       # Main Entry Component (Orchestrator)
│   ├── SmartQA/          # Subcomponents for SmartQA
│   │   ├── SmartQAHeader.vue
│   │   ├── SmartQAChatArea.vue
│   │   ├── SmartQATaskPanel.vue
│   │   ├── SmartQAInput.vue
│   │   └── AttachmentDialog.vue
│   ├── MessageList.vue   # Message list display
│   └── ...
├── composables/          # Business Logic & State Management
│   ├── useAgentSelection.ts
│   ├── useAttachments.ts
│   ├── useChatSession.ts
│   └── useSmartQALayout.ts
├── services/             # API Interaction Layer
│   ├── agentService.ts
│   ├── chatService.ts
│   └── knowledgeService.ts
├── types/                # TypeScript Definitions
│   └── index.ts
└── constants/            # Constants & Configuration
    └── index.ts
```

## Key Components

- **SmartQA.vue**: The container component that initializes composables and manages the overall layout state. It orchestrates communication between the Chat Area and the Task Panel.
- **SmartQAChatArea**: Handles the left pane (or full screen) chat interface, including the welcome screen, message list, and input area.
- **SmartQATaskPanel**: Handles the right pane for complex tasks (Workflow visualization, AutoTask logs).

## State Management

State is managed primarily through Vue Composables (`use...`) for component-local but complex logic, and Pinia (`workflowStore`) for global application state related to workflows.

## Services

API calls are encapsulated in `services/` to keep components clean and allow for easier testing and mocking.
