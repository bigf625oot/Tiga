# Frontend Common Components Architecture

## Directory Structure

```
src/components/common/
├── atoms/                # Basic building blocks (e.g., Loading, Button, Icon)
│   └── Loading/          # Component folder
│       ├── Loading.vue   # Implementation
│       ├── index.ts      # Public API
│       └── types.ts      # Type definitions
├── molecules/            # Combinations of atoms (e.g., GraphToolbar, SearchBar)
│   ├── GraphToolbar/
│   ├── GraphNodeDetails/
│   └── GraphLayoutSwitch/
├── organisms/            # Complex standalone components (e.g., GraphViewer)
│   └── GraphViewer/
├── hooks/                # Composable logic (e.g., useGraphLayout)
├── utils/                # Pure helper functions
└── types/                # Shared type definitions
```

## Rules & Conventions

1.  **Component Structure**: Each component must reside in its own directory with `index.ts`, `types.ts`, and the `.vue` file.
2.  **Naming**: PascalCase for directories and components.
3.  **Exports**: Use `index.ts` for barreling exports.
4.  **Types**: No `any`. Define interfaces in `types.ts`.
5.  **Styles**: Use `<style scoped>` or CSS Modules.
6.  **Dependencies**: Common components should not depend on feature-specific code (pages, business logic).
7.  **Testing**: Include `.spec.ts` for logic-heavy components.

## Code Review Checklist

1.  [ ] Is the component placed in the correct atomic level (Atom/Molecule/Organism)?
2.  [ ] Are props strictly typed in `types.ts`?
3.  [ ] Is `index.ts` present and exporting the component correctly?
4.  [ ] Are there any circular dependencies?
5.  [ ] Is the component free of business logic (pure UI/functional)?
6.  [ ] Are styles scoped?
7.  [ ] Are hardcoded strings extracted to props or constants?
8.  [ ] Is the component responsive?
9.  [ ] Are accessibility attributes (aria-label, etc.) present?
10. [ ] Are complex logic parts extracted to `hooks/`?
