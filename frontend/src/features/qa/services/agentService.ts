import type { Agent, Team, UserScript } from '../types';

export const agentService = {
  async getAgents(): Promise<Agent[]> {
    const res = await fetch(`/api/v1/agents/?_t=${Date.now()}`);
    if (!res.ok) throw new Error('Failed to fetch agents');
    return res.json();
  },

  async getTeams(): Promise<Team[]> {
    const res = await fetch(`/api/v1/teams/?_t=${Date.now()}`);
    if (!res.ok) throw new Error('Failed to fetch teams');
    return res.json();
  },

  async getUserScripts(agentId: string): Promise<UserScript[]> {
    if (!agentId) return [];
    const res = await fetch(`/api/v1/user_scripts?agent_id=${agentId}`);
    if (!res.ok) throw new Error('Failed to fetch user scripts');
    return res.json();
  }
};
