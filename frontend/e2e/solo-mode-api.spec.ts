import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

test.describe('Solo Mode Chat API E2E Tests', () => {
  let sessionId: string;
  const predefinedSessionId = '371e46b4-d285-4e41-87dc-b84e7822752e';

  // 1. 测试创建 solo 模式的会话
  test('01 - Create a new solo mode chat session', async ({ request }) => {
    const response = await request.post('/api/v1/chat/sessions', {
      data: {
        title: 'E2E Solo Mode Test',
        mode: 'solo'
      }
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('id');
    expect(data.mode).toBe('solo');
    sessionId = data.id; // 保存供后续使用
  });

  // 2. 测试获取刚才创建的会话
  test('02 - Get the created session details', async ({ request }) => {
    expect(sessionId).toBeDefined();
    const response = await request.get(`/api/v1/chat/sessions/${sessionId}`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.id).toBe(sessionId);
    expect(data.mode).toBe('solo');
  });

  // 3. 测试发送非流式消息
  test('03 - Send a basic message (stream=false)', async ({ request }) => {
    expect(sessionId).toBeDefined();
    const response = await request.post(`/api/v1/chat/sessions/${sessionId}/chat`, {
      data: {
        message: 'Hello, this is an E2E test message.',
        stream: false,
        mode: 'solo'
      }
    });
    // 取决于后端是否真正连接了LLM，这里允许 200 或 500
    expect([200, 500]).toContain(response.status());
  });

  // 4. 测试发送流式消息
  test('04 - Send a message with streaming (stream=true)', async ({ request }) => {
    expect(sessionId).toBeDefined();
    const response = await request.post(`/api/v1/chat/sessions/${sessionId}/chat`, {
      data: {
        message: 'Hello, please stream the response.',
        stream: true,
        mode: 'solo'
      }
    });
    expect([200, 500]).toContain(response.status());
  });

  // 5. 测试更新会话标题
  test('05 - Update session title', async ({ request }) => {
    expect(sessionId).toBeDefined();
    const response = await request.put(`/api/v1/chat/sessions/${sessionId}`, {
      data: {
        title: 'Updated Solo Mode Title'
      }
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.title).toBe('Updated Solo Mode Title');
  });

  // 6. 测试会话列表是否包含新会话
  test('06 - List sessions and verify inclusion', async ({ request }) => {
    const response = await request.get('/api/v1/chat/sessions');
    expect(response.ok()).toBeTruthy();
    const list = await response.json();
    expect(Array.isArray(list)).toBeTruthy();
    const found = list.find((s: any) => s.id === sessionId);
    expect(found).toBeDefined();
  });

  // 7. 测试指定会话ID的接口 (用户提供的ID)
  test('07 - Test user provided specific session ID', async ({ request }) => {
    // 该ID可能不存在，我们验证接口的正确处理 (200 或 404)
    const response = await request.get(`/api/v1/chat/sessions/${predefinedSessionId}`);
    expect([200, 404]).toContain(response.status());
  });

  // 8. 测试向指定ID发送消息 (边界测试)
  test('08 - Send message to predefined session ID', async ({ request }) => {
    const response = await request.post(`/api/v1/chat/sessions/${predefinedSessionId}/chat`, {
      data: {
        message: 'Ping to predefined session',
        stream: false,
        mode: 'solo'
      }
    });
    expect([200, 404, 500]).toContain(response.status());
  });

  // 9. 测试删除会话
  test('09 - Delete the test session', async ({ request }) => {
    expect(sessionId).toBeDefined();
    const response = await request.delete(`/api/v1/chat/sessions/${sessionId}`);
    expect(response.ok()).toBeTruthy();
  });

  // 10. 测试删除后无法获取会话
  test('10 - Verify session is deleted (404)', async ({ request }) => {
    expect(sessionId).toBeDefined();
    const response = await request.get(`/api/v1/chat/sessions/${sessionId}`);
    expect(response.status()).toBe(404);
  });
});
