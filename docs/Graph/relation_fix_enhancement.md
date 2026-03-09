# Relation Fix Enhancement Plan

## 1. Assessment
The current "Relation Fix" feature allows detecting missing relations, creating/deleting relations, and visualizing the graph. To meet the new requirements, we need to enhance the system in three dimensions:

1.  **Entity Type**: Allow users to modify the type/category of an entity.
2.  **Relation**: Strengthen the connection capabilities (create/edit relations).
3.  **Node Attributes**: Allow adding, deleting, and modifying node attributes.

## 2. Plan

### Backend (`backend/app/services/relation_fix_service.py` & `backend/app/api/endpoints/relation_fix.py`)
-   **Fetch Node Details**: Update `get_node_relations` to return full node attributes, not just ID and Label.
-   **Update Node**: Add an endpoint `/relation-fix/node/update` to update node attributes (including "type").
-   **Update Relation**: Add an endpoint `/relation-fix/relation/update` to update edge attributes.

### Frontend (`frontend/src/features/relation_fix`)
-   **API**: Update `api.ts` to include `updateNode` and `updateRelation` methods.
-   **UI Components**:
    -   **Node Details Panel**: A new section (likely in the right sidebar or a drawer) that appears when a node is clicked.
        -   Display Node ID (Name).
        -   Display Node Type (Editable).
        -   Display Attributes (Key-Value pairs, Editable).
        -   "Save" button to commit changes.
    -   **Relation Editing**:
        -   Allow clicking on an edge to edit its attributes (similar to node details).
        -   Enhance "Create Relation" to allow adding attributes during creation.

## 3. Todo List

### Backend
- [ ] Modify `RelationFixService.get_node_relations` to return node attributes.
- [ ] Add `RelationFixService.update_node` method.
- [ ] Add `RelationFixService.update_relation` method.
- [ ] Add `update_node` endpoint in `relation_fix.py`.
- [ ] Add `update_relation` endpoint in `relation_fix.py`.

### Frontend
- [ ] Update `relationFixApi` in `api.ts`.
- [ ] Create `NodeDetails.vue` component for viewing/editing node information.
- [ ] Integrate `NodeDetails.vue` into `RelationFix.vue` (or `RelationEditor.vue`).
- [ ] Update `RelationEditor.vue` to support "Strengthened" relation creation (more attributes).
- [ ] Add support for clicking edges to view/edit relation details (optional, but good for "Relation" dimension).

## 4. Implementation Details

-   **Entity Type**: We will treat "Type" as a special attribute `type` or `entity_type`.
-   **Attributes**: We will provide a dynamic list of key-value pairs for editing.

