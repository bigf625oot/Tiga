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
            if (typeof textChunk !== 'string') {
                const rawContent = textChunk.content;
                textChunk = typeof rawContent === 'object' && rawContent !== null 
                    ? JSON.stringify(rawContent, null, 2) 
                    : (rawContent || normalizeThink(textChunk));
            }
            assistantMsg.content = (assistantMsg.content || '') + textChunk;
            workflowStore.appendOutput(textChunk);
        },
        think: (data: any) => {
            let thinking = data;
            if (typeof thinking !== 'string') {
                const rawContent = thinking.content;
                thinking = typeof rawContent === 'object' && rawContent !== null 
                    ? JSON.stringify(rawContent, null, 2) 
                    : (rawContent || normalizeThink(thinking));
            }
            assistantMsg.reasoning = (assistantMsg.reasoning || '') + thinking;
        },
        sources: (data: any) => { assistantMsg.sources = data; },
        file: (data: any) => { 
            let fileData = data;
            if (typeof fileData !== 'string') {
                const rawContent = fileData.content || fileData.data || fileData;
                fileData = typeof rawContent === 'object' && rawContent !== null 
                    ? JSON.stringify(rawContent) 
                    : String(rawContent);
            }
            assistantMsg.content = (assistantMsg.content || '') + `\n::: file\n${fileData}\n:::\n`; 
        },
        image: (data: any) => { 
            const url = data?.url || data?.content?.url;
            if (url) assistantMsg.content = (assistantMsg.content || '') + `\n![生成图片](${url})\n`; 
        },
        chart: (data: any) => { assistantMsg.chart_config = data; },
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
