import { useWorkflowStore } from '@/features/workflow/store/workflow.store';
import type { Message, AgentEvent } from '../../types';
import type { StreamEventHandlers } from './baseHandlers';

export function createChatHandlers(
    assistantMsg: Message,
    workflowStore: ReturnType<typeof useWorkflowStore>,
    normalizeThink: (data: any) => string,
    agentRunIdRef?: { value: string | null }
): Partial<StreamEventHandlers> {
    return {
        text: (data: any) => {
            let textChunk = data;
            if (typeof textChunk !== 'string') textChunk = textChunk.content || normalizeThink(textChunk);
            assistantMsg.content = (assistantMsg.content || '') + textChunk;
            workflowStore.appendOutput(textChunk);
        },
        think: (data: any) => {
            let thinking = data;
            if (typeof thinking !== 'string') thinking = thinking.content || normalizeThink(thinking);
            assistantMsg.reasoning = (assistantMsg.reasoning || '') + thinking;
        },
        sources: (data: any) => { assistantMsg.sources = data; },
        file: (data: any) => { assistantMsg.content = (assistantMsg.content || '') + `\n::: file\n${JSON.stringify(data)}\n:::\n`; },
        image: (data: any) => { if (data?.url) assistantMsg.content = (assistantMsg.content || '') + `\n![生成图片](${data.url})\n`; },
        chart: (data: any) => { assistantMsg.chart_config = data; },
        error: (data: any) => {
            let errorText = data;
            if (typeof errorText !== 'string') errorText = errorText.content || errorText.message || errorText.detail || normalizeThink(errorText);
            assistantMsg.content = (assistantMsg.content || '') + `\n**错误**: ${errorText}`;
        },
    };
}
