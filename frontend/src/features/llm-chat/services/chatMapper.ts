import type { Session, Message, StreamEventItem } from '@/features/llm-chat/shared/types';

export interface MessageDTO {
    role: string;
    content: string;
    timestamp?: string | number;
    type?: string;
    status?: string;
    reasoning_content?: string;
    reasoning?: string;
    meta_data?: {
        stream_events?: any[];
        [key: string]: any;
    };
    stream_events?: any[];
    [key: string]: any;
}

export interface SessionDTO {
    id: string;
    title: string;
    agent_id?: string;
    mode?: string;
    messages?: MessageDTO[];
    workflow_state?: any;
    created_at?: string;
    updated_at?: string;
}

/**
 * Pure function to map MessageDTO from backend to frontend Domain Message model.
 */
export const mapMessageDTOToDomain = (dto: MessageDTO): Message => {
    const metaData = dto.meta_data || {};
    let artifacts = dto.artifacts || [];
    if (metaData.files && Array.isArray(metaData.files)) {
        artifacts = [...artifacts, ...metaData.files.map((f: any) => ({
            name: f.name || f.title,
            url: f.oss_url || f.url || f.id,
            type: f.media_kind || 'file',
            size: f.size
        }))];
    }

    return {
        ...dto,
        role: dto.role as 'user' | 'assistant' | 'system',
        reasoning: dto.reasoning_content || dto.reasoning || undefined,
        stream_events: metaData.stream_events || dto.stream_events || undefined,
        artifacts: artifacts.length > 0 ? artifacts : undefined,
    } as Message;
};

/**
 * Pure function to map SessionDTO from backend to frontend Domain Session model.
 */
export const mapSessionDTOToDomain = (dto: SessionDTO): Session => {
    return {
        ...dto,
        messages: (dto.messages || []).map(mapMessageDTOToDomain),
        mode: dto.mode as any,
    };
};
