import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAgentSelection } from '../useAgentSelection';
import { agentService } from '../../services/agentService';
import { ref } from 'vue';

// Mock dependencies
vi.mock('../../services/agentService', () => ({
  agentService: {
    getAgents: vi.fn(),
    getTeams: vi.fn(),
    getUserScripts: vi.fn()
  }
}));

describe('useAgentSelection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches agents on mount', async () => {
    const mockAgents = [{ id: '1', name: 'Agent 1' }];
    (agentService.getAgents as any).mockResolvedValue(mockAgents);

    const { agents, fetchAgents } = useAgentSelection(ref(null));
    await fetchAgents();

    expect(agents.value).toEqual(mockAgents);
    expect(agentService.getAgents).toHaveBeenCalled();
  });

  it('fetches teams', async () => {
    const mockTeams = [{ id: 't1', name: 'Team 1' }];
    (agentService.getTeams as any).mockResolvedValue(mockTeams);

    const { teams, fetchTeams } = useAgentSelection(ref('team'));
    await fetchTeams();

    expect(teams.value).toEqual(mockTeams);
    expect(agentService.getTeams).toHaveBeenCalled();
  });

  it('selects default agent if needed', async () => {
    const mockAgents = [
      { id: '1', name: 'Other' },
      { id: '2', name: '通用' }
    ];
    (agentService.getAgents as any).mockResolvedValue(mockAgents);

    const { agents, selectedAgentId, fetchAgents } = useAgentSelection(ref(null));
    await fetchAgents();

    // Should prefer '通用' agent
    expect(selectedAgentId.value).toBe('2');
  });

  it('fetches user scripts when agent changes', async () => {
    const mockScripts = [{ id: 's1', content: 'script 1' }];
    (agentService.getUserScripts as any).mockResolvedValue(mockScripts);

    const { selectedAgentId, userScripts } = useAgentSelection(ref(null));
    selectedAgentId.value = 'agent-1';

    // Wait for watcher to trigger
    await new Promise(resolve => setTimeout(resolve, 10));

    expect(agentService.getUserScripts).toHaveBeenCalledWith('agent-1');
    expect(userScripts.value).toEqual(mockScripts);
  });
});
