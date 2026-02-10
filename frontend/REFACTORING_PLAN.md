# Frontend Refactoring Plan & Documentation

## Overview
This document outlines the architectural refactoring of the Tiga Frontend application (`d:\tiga\frontend`). The goal is to transition from a monolithic component structure to a **Feature-Sliced Design (FSD)** architecture to improve scalability, maintainability, and team collaboration.

## Architecture Structure

The codebase is organized into the following layers:

```
src/
├── app/                # App-wide settings, providers, and global styles
├── core/               # Core business logic, constants, and utilities (Framework agnostic)
├── shared/             # Reusable UI components, hooks, and types (Domain agnostic)
│   ├── components/     # Atomic UI components (Buttons, Inputs, etc.)
│   ├── hooks/          # Shared Vue composables
│   └── utils/          # Shared utility functions
├── features/           # Business domains (Feature Slices)
│   ├── agent/          # Agent management and scripting
│   ├── analytics/      # Data analytics, metrics, and indicators
│   ├── knowledge/      # Knowledge base and graph visualization
│   ├── qa/             # Smart QA and chat interface
│   ├── recording/      # Audio recording and processing
│   ├── search/         # Search agent and crawler
│   ├── system/         # System configuration (Models, Database)
│   └── workflow/       # Workflow automation integration
└── App.vue             # Main application entry point (Wiring)
```

## Module Responsibilities

### 1. Shared Layer (`src/shared`)
- **Purpose**: Low-level, domain-agnostic building blocks.
- **Rules**: Can only import from other `shared` segments or external libraries. Cannot import from `features`.
- **Content**:
  - `components/atoms`: Basic UI elements (Loading, Icon).
  - `components/molecules`: Simple composite components.
  - `components/organisms`: Complex UI widgets (GraphViewer).

### 2. Features Layer (`src/features`)
- **Purpose**: Encapsulates specific business domains.
- **Rules**: 
  - Self-contained.
  - Should not import from other features (ideally). 
  - Exposes public API via `index.ts` (future improvement).
- **Modules**:
  - **Recording**: Handles audio capture (`Recorder`), file listing (`RecordingList`), and details (`RecordingDetail`).
  - **Knowledge**: Manages documents (`KnowledgeBase`) and visualization (`KnowledgeGraphView`).
  - **QA**: Chat interface (`SmartQA`) and reference display.
  - **Analytics**: Metrics extraction and data queries.
  - **Agent**: Agent creation and script editing.

## Key Changes

1.  **Component Migration**: All components moved from `src/components/*` to their respective `src/features/<domain>/components/*`.
2.  **Shared Extraction**: Common graph components moved to `src/shared/components`.
3.  **App.vue Refactoring**:
    -   Removed inline logic for "File List".
    -   Replaced monolithic imports with `defineAsyncComponent` for lazy loading (Performance).
    -   Updated imports to use aliases (`@/features/...`, `@/shared/...`).

## Performance Improvements
-   **Lazy Loading**: Top-level views are now loaded asynchronously, reducing the initial bundle size.
-   **Code Splitting**: Feature-based organization allows for better tree-shaking and chunking by build tools (Vite).

## Future Work
-   **Strict Boundaries**: Enforce dependency rules using ESLint (e.g., `eslint-plugin-boundaries`).
-   **Testing**: Add unit tests for each feature module.
-   **Documentation**: Detailed README for each feature folder.
