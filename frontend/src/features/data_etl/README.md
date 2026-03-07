# Data ETL Dashboard

## Features
- **Visual Canvas**: 1920x920px infinite canvas with zoom (50%-200%) and drag support.
- **Real-time Monitoring**: Visualizing data sources, storage endpoints, and data flow pipelines.
- **Mock Data**: Built-in mock data generator with different states.

## Mock Data Modes
You can toggle between different mock data states by pressing the **`m`** key on your keyboard while viewing the dashboard.

The modes cycle through:
1. **Normal**: Healthy system state.
2. **Abnormal**: System with errors and warnings.
3. **Empty**: No data state.

## Canvas Controls
- **Drag**: Click and drag anywhere on the canvas background to pan.
- **Zoom**: Use mouse wheel to zoom in/out.
- **Reset**: Click the "Fit" icon in the toolbar to reset view.

## Development
- **Tech Stack**: Vue 3, TypeScript, Tailwind CSS.
- **Components**: Located in `components/`.
- **Logic**: Mock data logic in `composables/useDashboardMock.ts`.
