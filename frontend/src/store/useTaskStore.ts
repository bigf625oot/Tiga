import { defineStore } from 'pinia';

export interface Task {
  id: string;
  name: string;
  progress: number; // 0 - 100
  status: 'pending' | 'processing' | 'success' | 'error';
  createdAt: number;
}

export const useTaskStore = defineStore('taskStore', {
  state: () => ({
    tasks: [] as Task[],
  }),
  actions: {
    addTask(task: Omit<Task, 'id' | 'createdAt'>) {
      const newTask: Task = {
        ...task,
        id: crypto.randomUUID(),
        createdAt: Date.now(),
      };
      // 添加到列表开头
      this.tasks.unshift(newTask);
      return newTask.id;
    },
    updateTaskProgress(id: string, progress: number) {
      const task = this.tasks.find(t => t.id === id);
      if (task) {
        task.progress = Math.min(Math.max(progress, 0), 100);
      }
    },
    updateTaskStatus(id: string, status: Task['status']) {
      const task = this.tasks.find(t => t.id === id);
      if (task) {
        task.status = status;
        if (status === 'success') {
          task.progress = 100;
        }
      }
    },
    removeTask(id: string) {
      const index = this.tasks.findIndex(t => t.id === id);
      if (index !== -1) {
        this.tasks.splice(index, 1);
      }
    },
    clearCompletedTasks() {
      this.tasks = this.tasks.filter(t => t.status === 'processing' || t.status === 'pending');
    }
  },
  getters: {
    processingCount: (state) => state.tasks.filter(t => t.status === 'processing').length,
    hasProcessingTasks: (state) => state.tasks.some(t => t.status === 'processing'),
  }
});
