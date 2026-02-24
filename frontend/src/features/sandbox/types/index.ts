export interface SandboxRequest {
    language: string;
    code?: string;
    template?: string;
    params?: Record<string, any>;
}

export interface SandboxFile {
    name: string;
    content: string; // Base64 encoded or text
    type?: 'image' | 'text' | 'pdf' | 'other';
}

export interface SandboxResult {
    type: string;
    content: string;
    files: SandboxFile[];
}

export interface SandboxResponse {
    session_id: string;
    status: 'success' | 'error';
    result: SandboxResult;
}

export interface SandboxError {
    code: string;
    message: string;
    details?: any;
}

export type ViewMode = 'list' | 'grid' | 'carousel' | 'gallery';
