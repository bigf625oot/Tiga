/**
 * @vitest-environment jsdom
 */
import { mount } from '@vue/test-utils';
import { describe, it, expect, beforeEach } from 'vitest';
import AgentStatusDashboard from '../AgentStatusDashboard.vue';
import { useI18n } from '../../../../locales';

describe('AgentStatusDashboard.vue', () => {
    const { setLocale } = useI18n();
    
    const defaultProps = {
        agentName: 'Test Agent',
        sessionId: '12345678',
        status: 'running',
        progress: 50,
        currentPhase: 'agentStatus.phases.executing',
        steps: [
            { label: 'agentStatus.phases.init', status: 'completed' },
            { label: 'agentStatus.phases.planning', status: 'running' }
        ],
        cpuUsage: 20,
        memoryUsage: 300,
        networkUsage: 10,
        errorCount: 0
    };

    beforeEach(() => {
        setLocale('zh-CN');
    });

    it('renders Chinese translations correctly', async () => {
        setLocale('zh-CN');
        const wrapper = mount(AgentStatusDashboard, {
            props: defaultProps
        });

        expect(wrapper.text()).toContain('Test Agent');
        expect(wrapper.text()).toContain('进度');
        expect(wrapper.text()).toContain('正在执行代码'); // agentStatus.phases.executing
        expect(wrapper.text()).toContain('初始化'); // agentStatus.phases.init
        expect(wrapper.text()).toContain('规划'); // agentStatus.phases.planning
        expect(wrapper.text()).toContain('CPU 使用率');
        expect(wrapper.text()).toContain('内存占用');
        expect(wrapper.text()).toContain('网络流量');
        expect(wrapper.text()).toContain('错误数');
    });

    it('renders English translations correctly', async () => {
        setLocale('en-US');
        const wrapper = mount(AgentStatusDashboard, {
            props: defaultProps
        });

        expect(wrapper.text()).toContain('Progress');
        expect(wrapper.text()).toContain('Executing Code');
        expect(wrapper.text()).toContain('Init');
        expect(wrapper.text()).toContain('Planning');
        expect(wrapper.text()).toContain('CPU Usage');
        expect(wrapper.text()).toContain('Memory');
        expect(wrapper.text()).toContain('Network');
        expect(wrapper.text()).toContain('Errors');
    });
});
