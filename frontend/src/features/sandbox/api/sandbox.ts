import { api } from '@/core/api/client';
import type { SandboxRequest, SandboxResponse } from '../types';
import axios, { type CancelTokenSource } from 'axios';

const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

export class SandboxService {
    private static async wait(ms: number) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    static async runCode(
        request: SandboxRequest, 
        options: { 
            signal?: AbortSignal,
            retries?: number 
        } = {}
    ): Promise<SandboxResponse> {
        let lastError: any;
        const retries = options.retries ?? MAX_RETRIES;

        for (let i = 0; i <= retries; i++) {
            try {
                const response = await api.post<SandboxResponse>('/sandbox/run', request, {
                    signal: options.signal
                });
                return response.data;
            } catch (error) {
                lastError = error;
                
                if (axios.isCancel(error)) {
                    throw error;
                }

                if (i < retries) {
                    const delay = RETRY_DELAY * Math.pow(2, i);
                    await this.wait(delay);
                    continue;
                }
            }
        }
        
        throw lastError;
    }
}
