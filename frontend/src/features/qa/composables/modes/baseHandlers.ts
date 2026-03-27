import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import type { Message } from '../../types';

export interface StreamEventHandlers {
    meta: (data: any) => void;
    thought: (data: any) => void;
    error: (data: any) => void;
    [key: string]: (data: any) => void;
}

export function createBaseHandlers(
    assistantMsg: Message, 
    normalizeThink: (data: any) => string,
    agentRunIdRef?: { value: string | null }
): StreamEventHandlers {
    return {
        meta: (data) => {
            if (data?.agent_run_id && agentRunIdRef) agentRunIdRef.value = data.agent_run_id;
            if (data?.msg_type) assistantMsg.type = data.msg_type;
        },
        thought: (data) => {
            const thoughtText = typeof data.content === 'string' ? data.content : '';
            assistantMsg.reasoning = (assistantMsg.reasoning || '') + thoughtText;
        },
        error: (data) => {
            let errorText = data;
            if (typeof errorText !== 'string') errorText = errorText.content || errorText.message || errorText.detail || normalizeThink(errorText);
            assistantMsg.content = (assistantMsg.content || '') + `\n**错误**: ${errorText}`;
        },
    };
}