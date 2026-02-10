# Features Directory

This directory contains the business logic and UI components for specific domains of the application, following the **Feature-Sliced Design (FSD)** principles.

## Structure

Each feature folder (e.g., `recording`, `knowledge`) should ideally follow this structure:

```
features/<feature-name>/
├── components/     # Vue components specific to this feature
├── composables/    # Feature-specific hooks (optional)
├── types/          # Feature-specific TypeScript types (optional)
├── api/            # API calls specific to this feature (optional)
└── index.ts        # Public API export (optional)
```

## List of Features

-   **agent**: Management of AI Agents and user scripts.
-   **analytics**: Business intelligence, metrics extraction, and data querying.
-   **knowledge**: Knowledge base management and Knowledge Graph visualization.
-   **qa**: Smart Q&A chat interface.
-   **recording**: Audio recording, transcription, and file management.
-   **search**: Intelligent search and crawling capabilities.
-   **system**: System-level configurations (LLM models, Database connections).
-   **workflow**: Integration with automation workflows (e.g., n8n).

## Rules

1.  **Cohesion**: Keep related logic together.
2.  **Encapsulation**: Components here should not be used by other features if possible. If a component is needed by multiple features, consider moving it to `src/shared`.
3.  **Lazy Loading**: Export components meant for `App.vue` or routing as Async Components where appropriate.
