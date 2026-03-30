import { useWorkflowStore } from '@/features/llm-chat/store/workflow/workflow.store';
import type { Message, AgentEvent } from '@/features/llm-chat/shared/types';
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
            if (typeof fileData === 'string') {
                try {
                    fileData = JSON.parse(fileData);
                } catch {
                    fileData = { name: fileData, url: fileData };
                }
            } else {
                const rawContent = fileData.content || fileData.data || fileData;
                fileData = typeof rawContent === 'object' && rawContent !== null 
                    ? rawContent 
                    : { name: String(rawContent), url: String(rawContent) };
            }
            if (!assistantMsg.artifacts) {
                assistantMsg.artifacts = [];
            }
            assistantMsg.artifacts.push(fileData);
        },
        image: (data: any) => { 
            const url = data?.url || data?.content?.url;
            if (url) assistantMsg.content = (assistantMsg.content || '') + `\n![生成图片](${url})\n`; 
        },
        chart: (data: any, meta?: any) => { 
            assistantMsg.chart_config = typeof data === 'string' ? JSON.parse(data) : data;
            
            // Check sub_type for d3/antv, passed via meta if available or guess from data structure
            let chartType = 'echarts';
            if (meta?.sub_type) {
                chartType = meta.sub_type;
            } else if (assistantMsg.chart_config?._type) {
                chartType = assistantMsg.chart_config._type;
            }

            // Record to artifacts for consistency
            if (!assistantMsg.artifacts) assistantMsg.artifacts = [];
            assistantMsg.artifacts.push({
                type: chartType === 'echarts' ? 'chart' : chartType,
                name: 'Generated Chart',
                data: assistantMsg.chart_config
            });
        },
        media: (data: any) => {
            let mediaData = data;
            if (typeof mediaData === 'string') {
                try { mediaData = JSON.parse(mediaData); } catch { mediaData = { url: mediaData, media_type: 'video' }; }
            }
            if (!assistantMsg.media) assistantMsg.media = [];
            assistantMsg.media.push(mediaData);
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
