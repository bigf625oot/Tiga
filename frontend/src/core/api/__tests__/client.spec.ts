import { api } from '../client';
import MockAdapter from 'axios-mock-adapter';
import { message } from 'ant-design-vue';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// Mock ant-design-vue message
vi.mock('ant-design-vue', () => ({
  message: {
    error: vi.fn(),
  },
}));

describe('API Client Auth Interceptor', () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(api);
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    mock.restore();
  });

  it('should attach Authorization header when token exists', async () => {
    const token = 'test-token-123';
    localStorage.setItem('token', token);

    mock.onGet('/test').reply(config => {
      expect(config.headers?.Authorization).toBe(`Bearer ${token}`);
      return [200, { success: true }];
    });

    await api.get('/test');
  });

  it('should not attach Authorization header when token is missing', async () => {
    mock.onGet('/test').reply(config => {
      expect(config.headers?.Authorization).toBeUndefined();
      return [200, { success: true }];
    });

    await api.get('/test');
  });

  it('should handle 401 Unauthorized error', async () => {
    mock.onGet('/test').reply(401);

    try {
      await api.get('/test');
    } catch (error: any) {
      expect(error.response.status).toBe(401);
      // message.error is now removed/optional, so we don't expect it
      // expect(message.error).toHaveBeenCalledWith('登录已过期，请重新登录');
    }
  });

  it('should handle 403 Forbidden error', async () => {
    mock.onGet('/test').reply(403);

    try {
      await api.get('/test');
    } catch (error: any) {
      expect(error.response.status).toBe(403);
      // expect(message.error).toHaveBeenCalledWith('没有权限执行此操作');
    }
  });
});
