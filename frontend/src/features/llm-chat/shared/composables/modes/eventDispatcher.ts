import { useWorkflowStore } from '@/features/llm-chat/store/workflow/workflow.store';
import type { Message, ModeType } from '@/features/llm-chat/shared/types';
import { createBaseHandlers, type StreamEventHandlers } from './baseHandlers';
import { createChatHandlers } from './chatMode';
import { createWorkflowHandlers } from './workflowMode';
// Future imports for other modes
// import { createTeamHandlers } from './teamMode';
// import { createSoloHandlers } from './soloMode';

/**
 * Registry to dynamically resolve event handlers based on the active mode.
 */
export function createEventDispatcher(
    mode: ModeType | null | undefined,
    assistantMsg: Message,
    workflowStore: ReturnType<typeof useWorkflowStore>,
    normalizeThink: (data: any) => string,
    agentRunIdRef?: { value: string | null }
): StreamEventHandlers {
    
    // 1. Always load base handlers (meta, thought, error, etc.)
    const baseHandlers = createBaseHandlers(assistantMsg, normalizeThink, agentRunIdRef);
    
    let specificHandlers: Partial<StreamEventHandlers> = {};

    // 2. Load mode-specific handlers
    // In the future, this can be refactored into true lazy loading using dynamic imports `await import(...)`
    // if the handler payload becomes too large.
    switch (mode) {
        case 'chat':
        case 'quick':
        case 'auto':
        case 'auto_task':
            specificHandlers = {
                ...createChatHandlers(assistantMsg, workflowStore, normalizeThink),
                ...createWorkflowHandlers(assistantMsg, workflowStore) // Some chat modes (like auto_task) might trigger workflows
            };
            break;
            
        case 'workflow':
        case 'solo':
        case 'team':
            specificHandlers = {
                ...createWorkflowHandlers(assistantMsg, workflowStore),
                ...createChatHandlers(assistantMsg, workflowStore, normalizeThink) // Fallback for standard text outputs
            };
            break;
            
        default:
            // Fallback to load everything if mode is undefined
            specificHandlers = {
                ...createChatHandlers(assistantMsg, workflowStore, normalizeThink),
                ...createWorkflowHandlers(assistantMsg, workflowStore)
            };
            break;
    }

    // 3. Merge and return
    return {
        ...baseHandlers,
        ...specificHandlers
    } as StreamEventHandlers;
}
