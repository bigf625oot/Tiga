import { describe, expect, it } from 'vitest';
import { getSmartQADefaults } from './smartqaDefaults';
import type { Message } from '@/features/llm-chat/shared/types';

describe('getSmartQADefaults', () => {
  it('defaults to auto when no sessionId', () => {
    expect(getSmartQADefaults(null)).toEqual({ mode: 'auto', currentModeId: null });
    expect(getSmartQADefaults(undefined)).toEqual({ mode: 'auto', currentModeId: null });
  });

  it('defaults to auto when sessionId exists but no messages', () => {
    expect(getSmartQADefaults('abc', [])).toEqual({ mode: 'auto', currentModeId: null });
  });

  it('defaults to auto when only system messages exist', () => {
    const msgs: Message[] = [{ role: 'system', content: 'hello', isSystem: true }];
    expect(getSmartQADefaults('abc', msgs)).toEqual({ mode: 'auto', currentModeId: null });
  });

  it('defaults to auto when sessionId exists and has user/assistant messages', () => {
    const msgs: Message[] = [{ role: 'user', content: 'hello' }];
    expect(getSmartQADefaults('abc', msgs)).toEqual({ mode: 'auto', currentModeId: null });
  });
});

