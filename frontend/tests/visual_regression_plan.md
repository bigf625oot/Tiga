# Visual Regression Test Plan - Log Empty State

## Overview
Verify the visual correctness of the "Empty Log State" component across different themes and resolutions.

## Test Cases

### Case 1: Light Mode Display
**Preconditions:**
- Application is in Light Mode.
- No logs are present in the system.
**Steps:**
1. Open the "System Log" drawer.
**Expected Result:**
- "Empty Log" illustration is visible in center.
- Illustration matches `empty-log.svg` (Light background #E4E7ED accents).
- Text "暂无日志" is displayed below icon.
- Text color is #909399.
- Vertical spacing between icon and text is 16px.

### Case 2: Dark Mode Display
**Preconditions:**
- Application is in Dark Mode (or toggle switch used).
- No logs are present.
**Steps:**
1. Open the "System Log" drawer.
2. Ensure Dark Mode is active.
**Expected Result:**
- "Empty Log" illustration switches to Dark version.
- Illustration matches `empty-log-dark.svg` (Dark slate colors).
- Text "暂无日志" is displayed.
- Text color is #C0C4CC.
- Background of drawer is dark (#0f172a).

### Case 3: LogPanel (Always Dark)
**Preconditions:**
- View `LogPanel` component (e.g., in Task Dashboard).
- No logs are present.
**Steps:**
1. Observe the Log Panel area.
**Expected Result:**
- Displays the Dark Mode version of the empty state illustration.
- Text color is #C0C4CC.

### Case 4: Responsiveness
**Steps:**
1. Resize browser window to 1024px, 768px, and mobile widths.
**Expected Result:**
- Empty state remains vertically and horizontally centered.
- Illustration does not overflow or distort.

### Case 5: State Transitions
**Steps:**
1. Start a task that generates logs (Empty State -> List).
2. Clear logs (List -> Empty State).
**Expected Result:**
- Smooth transition (no flickering).
- Empty state reappears immediately after clearing.
