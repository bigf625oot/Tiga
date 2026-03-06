/**
 * @场景    验证自动任务面板的标签切换、模板填充与数据拉取行为
 * @功能    覆盖面板基础渲染、活动分组、任务触发与统计加载
 * @依赖    vitest、@vue/test-utils、AutoTaskPanel、api client mock
 * @备注    依赖较多图标与接口 mock，属于偏集成层组件测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import AutoTaskPanel from '../AutoTaskPanel.vue';

// Mock icons
vi.mock('@ant-design/icons-vue', async () => {
  return {
    SearchOutlined: { template: '<span class="icon-search"></span>' },
    LineChartOutlined: { template: '<span class="icon-linechart"></span>' },
    CameraOutlined: { template: '<span class="icon-camera"></span>' },
    CloseOutlined: { template: '<span class="icon-close"></span>' },
    ThunderboltFilled: { template: '<span class="icon-thunderbolt"></span>' },
    ReloadOutlined: { template: '<span class="icon-reload"></span>' },
    InboxOutlined: { template: '<span class="icon-inbox"></span>' },
    DisconnectOutlined: { template: '<span class="icon-disconnect"></span>' },
    CheckCircleOutlined: { template: '<span class="icon-check"></span>' },
    PlusCircleOutlined: { template: '<span class="icon-plus"></span>' },
    MonitorOutlined: { template: '<span class="icon-monitor"></span>' },
    UnorderedListOutlined: { template: '<span class="icon-list"></span>' },
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

// Mock axios api client
const { apiGet } = vi.hoisted(() => ({
  apiGet: vi.fn()
}));
vi.mock('@/core/api/client', () => {
  return { api: { get: apiGet } };
});

describe('AutoTaskPanel', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => []
    });
    apiGet.mockReset();
    apiGet.mockResolvedValue({ data: [] });
  });

  it('renders correctly', async () => {
    const wrapper = mount(AutoTaskPanel);
    expect(wrapper.text()).toContain('自动任务工作台');
    (wrapper.vm as any).activeTab = 'task';
    await flushPromises();
    expect(wrapper.text()).toContain('今日任务');
  });
  
  it('displays templates', async () => {
    const wrapper = mount(AutoTaskPanel);
    (wrapper.vm as any).activeTab = 'task';
    await flushPromises();
    expect(wrapper.text()).toContain('竞品监控');
    expect(wrapper.text()).toContain('价格追踪');
  });

  it('toggles time groups', async () => {
    const wrapper = mount(AutoTaskPanel);
    (wrapper.vm as any).activeTab = 'task';
    await flushPromises();
    // Inject a recent activity to create "1小时内"分组
    (wrapper.vm as any).activities = [{ id: 1, last_run: new Date().toISOString(), type: 'crawl' }];
    await flushPromises();
    expect(wrapper.text()).toMatch(/(1小时内|今天)/);
    const header = wrapper.findAll('h3').find(h => /^(1小时内|今天)$/.test(h.text()));
    header && (await header.trigger('click'));
  });

  it('fills input when template is clicked', async () => {
    const wrapper = mount(AutoTaskPanel, {
      attachTo: document.body 
    });
    Element.prototype.scrollIntoView = vi.fn();

    (wrapper.vm as any).activeTab = 'task';
    await flushPromises();
    const templateCard = wrapper.findAll('button').filter(b => b.text().includes('竞品监控'))[0];
    await templateCard.trigger('click');

    const textarea = wrapper.find('#task-input textarea');
    const ta = textarea.element as HTMLTextAreaElement;
    expect(ta.value).toContain('每天9点抓取');
  });

  it('fetches stats on mount', async () => {
    const mockStats = [
        { label: '抓取', count: 5, trend: '+10%', trendUp: true, accentColor: 'blue' }
    ];
    apiGet.mockImplementation((url: string) => {
      if (url.includes('/openclaw/stats')) {
        return Promise.resolve({ data: mockStats });
      }
      return Promise.resolve({ data: [] });
    });

    const wrapper = mount(AutoTaskPanel);
    (wrapper.vm as any).activeTab = 'task';
    await flushPromises();

    expect(wrapper.text()).toContain('5');
    expect(wrapper.text()).toContain('抓取');
  });

  it('calls create_task API when button is clicked', async () => {
    const wrapper = mount(AutoTaskPanel, { attachTo: document.body });
    (wrapper.vm as any).activeTab = 'task';
    await flushPromises();
    const textarea = wrapper.find('#task-input textarea');
    await textarea.setValue('Crawl google.com');
    
    const createButton = wrapper.findAll('button').filter(b => b.text().includes('创建任务'))[0];
    await createButton.trigger('click');
    
    await flushPromises();
    expect(wrapper.emitted('run-task')).toBeTruthy();
  });
});
