import { useState, useEffect } from 'react';
import type { Task, Agent } from '@/types';
import { taskApi, agentApi } from '@/services/api';
import { RippleButton } from '@/registry/magicui/ripple-button';

interface TaskFormProps {
  task?: Task;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function TaskForm({ task, onSuccess, onCancel }: TaskFormProps) {
  const [target, setTarget] = useState(task?.target || '');
  const [description, setDescription] = useState(task?.description || '');
  const [agentId, setAgentId] = useState(task?.agent_id || '');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    agentApi.getAgents().then((response) => {
      if (response.success) {
        setAgents(response.data);
      }
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (task) {
        await taskApi.updateTask(task.id, {
          target,
          description,
          agent_id: agentId || undefined,
        });
      } else {
        await taskApi.createTask({
          target,
          description,
          agent_id: agentId || undefined,
        });
      }
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-md">
          {error}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
          目标URL *
        </label>
        <input
          type="text"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          required
          className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-white"
          placeholder="https://example.com"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
          描述
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-white"
          placeholder="任务描述..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
          Agent
        </label>
        <select
          value={agentId}
          onChange={(e) => setAgentId(e.target.value)}
          className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-white"
        >
          <option value="">无</option>
          {agents.map((agent) => (
            <option key={agent.id} value={agent.id}>
              {agent.name} ({agent.status})
            </option>
          ))}
        </select>
      </div>

      <div className="flex gap-2 justify-end">
        {onCancel && (
          <RippleButton
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700"
            rippleColor="rgba(0, 0, 0, 0.1)"
          >
            取消
          </RippleButton>
        )}
        <RippleButton
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-md hover:bg-zinc-800 dark:hover:bg-zinc-100 disabled:opacity-50"
          rippleColor="rgba(255, 255, 255, 0.3)"
        >
          {loading ? '处理中...' : task ? '更新' : '创建'}
        </RippleButton>
      </div>
    </form>
  );
}
