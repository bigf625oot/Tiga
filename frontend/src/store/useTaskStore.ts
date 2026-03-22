import { defineStore } from 'pinia';

export interface Task {
  id: string;
  name: string;
  task_type?: string;
  progress: number;
  status: 'pending' | 'processing' | 'success' | 'error' | 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED';
  createdAt: number;
  msg?: string;
  step?: string;
}

const API_BASE = '/api/v1/async/tasks';
const WS_BASE = `ws://${window.location.host}/api/v1/async/tasks/ws`;

export const useTaskStore = defineStore('taskStore', {
  state: () => ({
    tasks: [] as Task[],
    ws: null as WebSocket | null,
    wsUserId: '',
    pollingInterval: null as number | null,
    reconnectTimer: null as number | null,
    isConnecting: false,
  }),
  actions: {
    async fetchTasks(userId?: string) {
      try {
        const params = new URLSearchParams();
        if (userId) params.append('user_id', userId);
        params.append('page', '1');
        params.append('page_size', '50');

        const response = await fetch(`${API_BASE}/?${params}`);
        if (!response.ok) throw new Error('Failed to fetch tasks');

        const data = await response.json();
        this.tasks = (data.items || []).map((t: any) => this.mapTask(t));
      } catch (error) {
        console.error('Failed to fetch tasks:', error);
      }
    },

    async createTask(payload: { name: string; task_type?: string; priority?: number }) {
      try {
        const response = await fetch(API_BASE, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!response.ok) throw new Error('Failed to create task');

        const data = await response.json();
        const newTask: Task = {
          id: data.task_id,
          name: payload.name,
          progress: 0,
          status: 'pending',
          createdAt: Date.now(),
        };
        this.tasks.unshift(newTask);
        return data.task_id;
      } catch (error) {
        console.error('Failed to create task:', error);
        throw error;
      }
    },

    async removeTask(id: string) {
      try {
        const response = await fetch(`${API_BASE}/${id}`, {
          method: 'DELETE',
        });

        if (!response.ok && response.status !== 404) {
          throw new Error('Failed to delete task');
        }

        const index = this.tasks.findIndex(t => t.id === id);
        if (index !== -1) {
          this.tasks.splice(index, 1);
        }
      } catch (error) {
        console.error('Failed to remove task:', error);
        this.tasks = this.tasks.filter(t => t.id !== id);
      }
    },

    async clearCompletedTasks() {
      const completedTasks = this.tasks.filter(
        t => t.status === 'success' || t.status === 'SUCCESS'
      );

      for (const task of completedTasks) {
        await this.removeTask(task.id);
      }
    },

    connectWebSocket(userId: string) {
      if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
        return;
      }
      if (this.isConnecting) return;

      this.isConnecting = true;
      this.wsUserId = userId;
      const wsUrl = `${WS_BASE}?user_id=${encodeURIComponent(userId)}`;

      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnecting = false;
          if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
          }
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleWebSocketMessage(message);
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
          }
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected, reconnecting in 5s...');
          this.isConnecting = false;
          this.ws = null;
          if (!this.reconnectTimer && this.wsUserId) {
             this.reconnectTimer = window.setTimeout(() => {
               this.reconnectTimer = null;
               if (this.wsUserId) {
                 this.connectWebSocket(this.wsUserId);
               }
             }, 5000);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          // The onclose event will typically fire after onerror, triggering the reconnect logic there.
        };
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        this.isConnecting = false;
        this.startPolling(userId);
      }
    },

    handleWebSocketMessage(message: any) {
      if (!message || !message.task_id) return;

      const taskId = message.task_id;
      let task = this.tasks.find(t => t.id === taskId);

      if (!task && message.type === 'progress') {
        task = {
          id: taskId,
          name: message.data?.name || 'Unknown Task',
          progress: message.data?.percent || 0,
          status: this.mapStatus(message.data?.status),
          createdAt: Date.now(),
        };
        this.tasks.unshift(task);
      }

      if (task) {
        if (message.type === 'progress' || message.data) {
          task.progress = message.data?.percent ?? task.progress;
          task.status = this.mapStatus(message.data?.status);
          task.msg = message.data?.msg;
          task.step = message.data?.step;
        }
      }
    },

    startPolling(userId: string) {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval);
      }

      this.fetchTasks(userId);
      this.pollingInterval = window.setInterval(() => {
        this.fetchTasks(userId);
      }, 5000);
    },

    disconnect() {
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval);
        this.pollingInterval = null;
      }
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
      this.isConnecting = false;
      this.wsUserId = '';
    },

    mapTask(apiTask: any): Task {
      return {
        id: apiTask.id,
        name: apiTask.name,
        task_type: apiTask.task_type,
        progress: apiTask.progress || 0,
        status: this.mapStatus(apiTask.status),
        createdAt: new Date(apiTask.created_at).getTime(),
        msg: apiTask.msg,
        step: apiTask.step,
      };
    },

    mapStatus(status: string): Task['status'] {
      const statusMap: Record<string, Task['status']> = {
        'PENDING': 'pending',
        'RUNNING': 'processing',
        'SUCCESS': 'success',
        'FAILED': 'error',
        'CANCELLED': 'error',
      };
      return statusMap[status?.toUpperCase()] || 'pending';
    },
  },
  getters: {
    processingCount: (state) => state.tasks.filter(
      t => t.status === 'processing' || t.status === 'RUNNING'
    ).length,
    hasProcessingTasks: (state) => state.tasks.some(
      t => t.status === 'processing' || t.status === 'RUNNING'
    ),
  },
});