import { useWorkflowStore } from '@/features/llm-chat/store/workflow/workflow.store';
import type { Message } from '@/features/llm-chat/shared/types';

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
            let thoughtText = data;
            if (typeof thoughtText !== 'string') {
                const rawContent = thoughtText.content;
                thoughtText = typeof rawContent === 'object' && rawContent !== null 
                    ? JSON.stringify(rawContent, null, 2) 
                    : (rawContent || normalizeThink(thoughtText));
            }
            assistantMsg.reasoning = (assistantMsg.reasoning || '') + thoughtText;
        },
        error: (data: any) => {
            let errorText = data;
            if (typeof errorText !== 'string') {
                const rawContent = errorText.content || errorText.message || errorText.detail;
                errorText = typeof rawContent === 'object' && rawContent !== null 
                    ? JSON.stringify(rawContent, null, 2) 
                    : (rawContent || normalizeThink(errorText));
            }
            assistantMsg.content = (assistantMsg.content || '') + `\n**错误**: ${errorText}`;
        },
    };
}
