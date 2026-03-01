import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import AutoTaskPanel from '../AutoTaskPanel.vue';

// Mock icons
vi.mock('@ant-design/icons-vue', async () => {
  return {
    CloseOutlined: { template: '<span class="icon-close"></span>' },
    ThunderboltFilled: { template: '<span class="icon-thunderbolt"></span>' },
    ReloadOutlined: { template: '<span class="icon-reload"></span>' },
    InboxOutlined: { template: '<span class="icon-inbox"></span>' },
    DisconnectOutlined: { template: '<span class="icon-disconnect"></span>' },
    CheckCircleOutlined: { template: '<span class="icon-check"></span>' },
    CameraOutlined: { template: '<span class="icon-camera"></span>' },
    PlusCircleOutlined: { template: '<span class="icon-plus"></span>' },
    MonitorOutlined: { template: '<span class="icon-monitor"></span>' },
    UnorderedListOutlined: { template: '<span class="icon-list"></span>' },
    LineChartOutlined: { template: '<span class="icon-line-chart"></span>' },
    DollarOutlined: { template: '<span class="icon-dollar"></span>' },
    FileTextOutlined: { template: '<span class="icon-file-text"></span>' },
    ReadOutlined: { template: '<span class="icon-read"></span>' },
    BarChartOutlined: { template: '<span class="icon-bar-chart"></span>' },
    BellOutlined: { template: '<span class="icon-bell"></span>' },
    AimOutlined: { template: '<span class="icon-aim"></span>' },
    MailOutlined: { template: '<span class="icon-mail"></span>' },
    CloudOutlined: { template: '<span class="icon-cloud"></span>' },
    RiseOutlined: { template: '<span class="icon-rise"></span>' },
    FallOutlined: { template: '<span class="icon-fall"></span>' },
    ClockCircleOutlined: { template: '<span class="icon-clock"></span>' },
    DownOutlined: { template: '<span class="icon-down"></span>' },
    ArrowRightOutlined: { template: '<span class="icon-arrow-right"></span>' },
  };
});

// Mock global fetch
global.fetch = vi.fn();

describe('AutoTaskPanel', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => []
    });
  });

  it('renders correctly', () => {
    const wrapper = mount(AutoTaskPanel);
    expect(wrapper.text()).toContain('自动任务工作台');
    expect(wrapper.text()).toContain('今日任务');
  });

  it('displays templates', () => {
    const wrapper = mount(AutoTaskPanel);
    expect(wrapper.text()).toContain('竞品监控');
    expect(wrapper.text()).toContain('价格追踪');
  });

  it('toggles time groups', async () => {
    const wrapper = mount(AutoTaskPanel);
    expect(wrapper.text()).toContain('10分钟前');
    const timeGroup = wrapper.findAll('.group').filter(w => w.text().includes('10分钟前'))[0];
    if (timeGroup) {
        await timeGroup.trigger('click');
    }
  });

  it('fills input when template is clicked', async () => {
    const wrapper = mount(AutoTaskPanel, {
      attachTo: document.body 
    });
    Element.prototype.scrollIntoView = vi.fn();

    const templateCard = wrapper.findAll('button').filter(b => b.text().includes('竞品监控'))[0];
    await templateCard.trigger('click');

    const textarea = wrapper.find('textarea');
    expect(textarea.element.value).toContain('每天9点抓取');
  });

  it('fetches stats on mount', async () => {
    const mockStats = [
        { label: '抓取', count: 5, trend: '+10%', trendUp: true, accentColor: 'blue' }
    ];
    (global.fetch as any).mockImplementation((url: string) => {
        if (url.includes('/stats')) {
            return Promise.resolve({
                ok: true,
                json: async () => mockStats
            });
        }
        return Promise.resolve({ ok: true, json: async () => [] });
    });

    const wrapper = mount(AutoTaskPanel);
    await flushPromises();

    expect(global.fetch).toHaveBeenCalledWith('/api/v1/openclaw/stats');
    expect(wrapper.text()).toContain('5');
    expect(wrapper.text()).toContain('抓取');
  });

  it('calls create_task API when button is clicked', async () => {
    const wrapper = mount(AutoTaskPanel, { attachTo: document.body });
    const textarea = wrapper.find('textarea');
    await textarea.setValue('Crawl google.com');
    
    // Mock create API
    (global.fetch as any).mockImplementation((url: string) => {
        if (url.includes('/create_task')) {
            return Promise.resolve({
                ok: true,
                json: async () => ({ status: 'success' })
            });
        }
        return Promise.resolve({ ok: true, json: async () => [] });
    });

    const createButton = wrapper.findAll('button').filter(b => b.text().includes('创建任务'))[0];
    await createButton.trigger('click');
    
    expect(global.fetch).toHaveBeenCalledWith('/api/v1/openclaw/create_task', expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ prompt: 'Crawl google.com' })
    }));
    
    await flushPromises();
    expect(wrapper.emitted('run-task')).toBeTruthy();
  });
});
