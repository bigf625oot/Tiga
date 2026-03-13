import {
    User,
    Users,
    LayoutGrid,
    Bot,
    Zap,
    Workflow
} from 'lucide-vue-next';
import type { ModeConfig } from '../types';

export const MODES: ModeConfig[] = [
    { id: 'quick', name: 'Quick模式', icon: Zap, value: 'chat', description: '快问快答', themeColor: 'blue' },
    { id: 'solo', name: 'Solo模式', icon: User, value: 'chat', description: '自规划任务', themeColor: 'green' },
    { id: 'team', name: '团队模式', icon: Users, value: 'workflow', description: '多智能协作', themeColor: 'purple' },
    { id: 'workflow', name: '工作流模式', icon: Workflow, value: 'workflow', description: '自定义工作流', themeColor: 'orange' },
    { id: 'openclaw', name: 'Openclaw', icon: Bot, value: 'auto_task', description: '自动化任务', themeColor: 'rose' }
];

export const STORAGE_KEYS = {
    SPLIT_RATIO: 'smartqa-split-ratio',
    IS_NETWORK_SEARCH_ENABLED: 'isNetworkSearchEnabled',
    DEFAULT_AGENT_ID: 'defaultAgentId'
};

export const DEFAULT_SPLIT_RATIO = 0.6;
export const MAX_FILE_SIZE_MB = 50;
export const ACCEPTED_FILE_TYPES = ['.pdf', '.docx', '.pptx', '.xlsx', '.txt'];
