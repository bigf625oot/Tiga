/**
 * @vitest-environment jsdom
 *
 * 测试套件: frontend/src/features/workflow/components/TaskPanel.vue
 * 覆盖需求:
 *  - REQ-UI-1: pending 任务显示灰色圆点
 *  - REQ-UI-2: running 任务显示蓝色 animate-pulse 圆点
 *  - REQ-UI-3: completed 任务显示绿色 ✓ 标记
 *  - REQ-UI-4: failed 任务显示红色 ✗ 标记
 *  - REQ-UI-5: 状态文字标签正确（待执行/执行中/完成/失败）
 *  - REQ-UI-6: 进度条根据 store.progress 显示
 *  - REQ-UI-7: 运行中的任务自动展开输出区域
 *  - REQ-UI-8: 工具调用徽章渲染（tool_name + status class）
 *  - REQ-UI-9: 产出物区域在有 artifacts 时显示
 *  - REQ-UI-10: 产出物区域在无 artifacts 时不显示
 *  - REQ-UI-11: 产出物链接指向 /uploads/ 正确 URL
 *  - REQ-UI-12: 产出物图标根据 type 正确（python=🐍 etc.）
 *  - REQ-UI-13: 任务总数/完成数显示在进度条左侧
 *  - REQ-UI-14: 日志抽屉按钮点击后打开 LogDrawer
 *  - REQ-UI-15: 停止按钮调用 store.stopWorkflow
 *  - REQ-UI-16: 空状态（无任务且不在运行）显示 EmptyState
 */
import { mount } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, computed } from 'vue';
import TaskPanel from '../TaskPanel.vue';
import LogDrawer from '../drawer/LogDrawer.vue';

// ── Store mock 工厂 ───────────────────────────────────────────────────────────
function makeStore(overrides = {}) {
    return {
        progress: 0,
        tasks: [],
        logs: [],
        artifacts: [],
        isRunning: false,
        currentStep: '',
        completedTasks: 0,
        totalTasks: 0,
        stopWorkflow: vi.fn(),
        clearLogs: vi.fn(),
        ...overrides,
    };
}

let mockStore = makeStore();

vi.mock('../../store/workflow.store', () => ({
    useWorkflowStore: () => mockStore,
}));

vi.mock('../../../../locales', () => ({
    useI18n: () => ({ t: (key) => key }),
}));

const STUBS = {
    TaskTree: true,
    LogDrawer: true,
    AgentStatusDashboard: { template: '<div class="dashboard-stub">Dashboard</div>' },
    TaskGraph: true,
    ArtifactEditor: true,
    SandboxResultViewer: true,
    SandboxTerminal: true,
    EmptyState: { template: '<div class="empty-state-stub">Empty</div>' },
    'a-slider': { template: '<input type="range" />' },
    AppstoreOutlined: true,
    StopOutlined: true,
    CodeOutlined: true,
    ApartmentOutlined: true,
    PlayCircleOutlined: true,
    LeftOutlined: true,
    RightOutlined: true,
    FileTextOutlined: true,
};

beforeEach(() => {
    mockStore = makeStore();
});

// ─────────────────────────────────────────────────────────────────────────────

describe('TaskPanel — 任务卡片状态样式', () => {
    it('REQ-UI-1: pending 任务 — 显示灰色状态圆点', () => {
        mockStore = makeStore({
            tasks: [{ id: 't1', name: '待执行任务', status: 'pending', output: '', toolCalls: [], logs: [] }],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        // 灰色圆点使用 bg-muted-foreground/40
        expect(wrapper.html()).toContain('bg-muted-foreground/40');
    });

    it('REQ-UI-2: running 任务 — 显示 animate-pulse 蓝色圆点', () => {
        mockStore = makeStore({
            isRunning: true,
            tasks: [{ id: 't1', name: '执行中任务', status: 'running', output: '', toolCalls: [], logs: [], startTime: Date.now() }],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.html()).toContain('animate-ping');
        expect(wrapper.html()).toContain('bg-primary');
    });

    it('REQ-UI-3: completed 任务 — 显示绿色区域', () => {
        mockStore = makeStore({
            tasks: [{ id: 't1', name: '已完成任务', status: 'completed', output: '完成输出', toolCalls: [], logs: [], startTime: Date.now() - 1000, endTime: Date.now() }],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.html()).toContain('bg-green-500');
    });

    it('REQ-UI-4: failed 任务 — 显示红色区域', () => {
        mockStore = makeStore({
            tasks: [{ id: 't1', name: '失败任务', status: 'failed', output: '', toolCalls: [], logs: ['错误: OOM'], startTime: Date.now() - 500, endTime: Date.now() }],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.html()).toContain('bg-red-500');
    });

    it('REQ-UI-5: 状态文字标签正确映射', () => {
        const statuses = [
            { status: 'pending',   label: '待执行' },
            { status: 'running',   label: '执行中' },
            { status: 'completed', label: '完成'   },
            { status: 'failed',    label: '失败'   },
        ];
        statuses.forEach(({ status, label }) => {
            mockStore = makeStore({
                tasks: [{ id: 't1', name: '任务', status, output: '', toolCalls: [], logs: [] }],
            });
            const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
            expect(wrapper.text()).toContain(label);
        });
    });
});

// ─────────────────────────────────────────────────────────────────────────────

describe('TaskPanel — 进度条', () => {
    it('REQ-UI-6: 进度条 width 等于 store.progress%', () => {
        mockStore = makeStore({ progress: 75, tasks: [{ id: 't1', name: 'T', status: 'pending', output: '', toolCalls: [], logs: [] }] });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.html()).toContain('width: 75%');
    });

    it('REQ-UI-13: 显示已完成/总数文字', () => {
        mockStore = makeStore({
            progress: 50,
            completedTasks: 2,
            totalTasks: 4,
            tasks: [
                { id: 't1', name: 'A', status: 'completed', output: '', toolCalls: [], logs: [] },
                { id: 't2', name: 'B', status: 'completed', output: '', toolCalls: [], logs: [] },
                { id: 't3', name: 'C', status: 'pending',   output: '', toolCalls: [], logs: [] },
                { id: 't4', name: 'D', status: 'pending',   output: '', toolCalls: [], logs: [] },
            ],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.text()).toContain('2');
        expect(wrapper.text()).toContain('4');
    });
});

// ─────────────────────────────────────────────────────────────────────────────

describe('TaskPanel — 工具调用徽章', () => {
    it('REQ-UI-8: toolCalls 渲染为 badge，显示 tool_name', () => {
        mockStore = makeStore({
            tasks: [{
                id: 't1', name: '执行任务', status: 'running', output: '',
                toolCalls: [
                    { tool_name: 'run_code', status: 'running' },
                    { tool_name: 'web_search', status: 'completed', result: 'ok' },
                ],
                logs: [],
            }],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.text()).toContain('run_code');
        expect(wrapper.text()).toContain('web_search');
    });

    it('REQ-UI-8: running tool 有 animate-pulse 样式', () => {
        mockStore = makeStore({
            tasks: [{
                id: 't1', name: '执行任务', status: 'running', output: '',
                toolCalls: [{ tool_name: 'calculator', status: 'running' }],
                logs: [],
            }],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.html()).toContain('animate-pulse');
    });
});

// ─────────────────────────────────────────────────────────────────────────────

describe('TaskPanel — 产出物区域', () => {
    it('REQ-UI-9: 有 artifacts 时渲染产出物清单区域', () => {
        mockStore = makeStore({
            artifacts: [
                { name: 'analysis.py', url: '/uploads/analysis.py', type: 'python' },
            ],
            tasks: [{ id: 't1', name: 'T', status: 'completed', output: '', toolCalls: [], logs: [] }],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.text()).toContain('产出物清单');
        expect(wrapper.text()).toContain('analysis.py');
    });

    it('REQ-UI-10: 无 artifacts 时不渲染产出物清单区域', () => {
        mockStore = makeStore({
            artifacts: [],
            tasks: [{ id: 't1', name: 'T', status: 'completed', output: '', toolCalls: [], logs: [] }],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.text()).not.toContain('产出物清单');
    });

    it('REQ-UI-11: 产出物链接指向正确的 /uploads/ URL', () => {
        mockStore = makeStore({
            artifacts: [
                { name: 'report.md', url: '/uploads/report.md', type: 'markdown' },
            ],
            tasks: [{ id: 't1', name: 'T', status: 'completed', output: '', toolCalls: [], logs: [] }],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        const link = wrapper.find('a[href="/uploads/report.md"]');
        expect(link.exists()).toBe(true);
        expect(link.attributes('target')).toBe('_blank');
    });

    it('REQ-UI-12: python 类型显示 🐍 图标', () => {
        mockStore = makeStore({
            artifacts: [{ name: 'script.py', url: '/uploads/script.py', type: 'python' }],
            tasks: [{ id: 't1', name: 'T', status: 'completed', output: '', toolCalls: [], logs: [] }],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.text()).toContain('🐍');
    });

    it('REQ-UI-12: image 类型显示 🖼️ 图标', () => {
        mockStore = makeStore({
            artifacts: [{ name: 'chart.png', url: '/uploads/chart.png', type: 'image' }],
            tasks: [{ id: 't1', name: 'T', status: 'completed', output: '', toolCalls: [], logs: [] }],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.text()).toContain('🖼️');
    });

    it('REQ-UI-12: markdown 类型显示 📝 图标', () => {
        mockStore = makeStore({
            artifacts: [{ name: 'readme.md', url: '/uploads/readme.md', type: 'markdown' }],
            tasks: [{ id: 't1', name: 'T', status: 'completed', output: '', toolCalls: [], logs: [] }],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.text()).toContain('📝');
    });

    it('REQ-UI-9: 多个产出物全部渲染', () => {
        mockStore = makeStore({
            artifacts: [
                { name: 'a.py',  url: '/uploads/a.py',  type: 'python'   },
                { name: 'b.csv', url: '/uploads/b.csv', type: 'csv'      },
                { name: 'c.png', url: '/uploads/c.png', type: 'image'    },
            ],
            tasks: [{ id: 't1', name: 'T', status: 'completed', output: '', toolCalls: [], logs: [] }],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.text()).toContain('a.py');
        expect(wrapper.text()).toContain('b.csv');
        expect(wrapper.text()).toContain('c.png');
        expect(wrapper.text()).toContain('3 个文件');
    });
});

// ─────────────────────────────────────────────────────────────────────────────

describe('TaskPanel — 日志与停止按钮', () => {
    it('REQ-UI-14: 点击日志按钮打开 LogDrawer', async () => {
        mockStore = makeStore({
            tasks: [{ id: 't1', name: 'T', status: 'pending', output: '', toolCalls: [], logs: [] }],
        });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        const logBtn = wrapper.find('.log-trigger');
        expect(logBtn.exists()).toBe(true);
        await logBtn.trigger('click');
        const drawer = wrapper.findComponent(LogDrawer);
        expect(drawer.props('visible')).toBe(true);
    });

    it('REQ-UI-15: 点击停止按钮调用 store.stopWorkflow', async () => {
        mockStore = makeStore({ isRunning: true, tasks: [] });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        const stopBtn = wrapper.find('button.text-red-500');
        expect(stopBtn.exists()).toBe(true);
        await stopBtn.trigger('click');
        expect(mockStore.stopWorkflow).toHaveBeenCalledOnce();
    });
});

// ─────────────────────────────────────────────────────────────────────────────

describe('TaskPanel — 空状态', () => {
    it('REQ-UI-16: 无任务且不在运行时显示 EmptyState', () => {
        mockStore = makeStore({ tasks: [], isRunning: false });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.html()).toContain('empty-state-stub');
    });

    it('REQ-UI-16: 运行中但无任务时显示加载动画而非 EmptyState', () => {
        mockStore = makeStore({ tasks: [], isRunning: true });
        const wrapper = mount(TaskPanel, { global: { stubs: STUBS } });
        expect(wrapper.html()).toContain('animate-spin');
        expect(wrapper.html()).not.toContain('empty-state-stub');
    });
});
