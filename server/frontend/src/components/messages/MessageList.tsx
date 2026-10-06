import { useState, useEffect } from 'react';
import { useApiList } from '@/hooks/useApi';
import { messageApi, taskApi } from '@/services/api';
import type { Message, Task } from '@/types';
import { GlassCard } from '@/components/ui/liquid-glass';

export function MessageList() {
  const [taskFilter, setTaskFilter] = useState<string>('');
  const [tasks, setTasks] = useState<Task[]>([]);

  const { items: messages, loading, error } = useApiList<Message>(
    () => messageApi.getMessages(taskFilter ? { task_id: taskFilter } : undefined),
    { immediate: true }
  );

  useEffect(() => {
    taskApi.getTasks().then((response) => {
      if (response.success) {
        setTasks(response.data);
      }
    });
  }, []);

  if (loading && messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-zinc-600 dark:text-zinc-400">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-md">
        错误: {error.message}
      </div>
    );
  }

  const typeLabels: Record<string, string> = {
    pure: '纯文本',
    solution: '解决方案',
    page: '页面',
    summary: '摘要',
    vulnerability: '漏洞',
    question: '问题',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
            按任务筛选
          </label>
          <select
            value={taskFilter}
            onChange={(e) => setTaskFilter(e.target.value)}
            className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-white"
          >
            <option value="">全部任务</option>
            {tasks.map((task) => (
              <option key={task.id} value={task.id}>
                {task.target || task.id}
              </option>
            ))}
          </select>
        </div>
      </div>

      {messages.length === 0 ? (
        <div className="text-center py-12 text-zinc-600 dark:text-zinc-400">
          暂无消息
        </div>
      ) : (
        <div className="space-y-4">
          {messages.map((message) => (
            <GlassCard key={message.id}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 bg-zinc-100 dark:bg-zinc-700 rounded text-xs font-medium">
                    {message.role}
                  </span>
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 rounded text-xs">
                    {typeLabels[message.type] || message.type}
                  </span>
                </div>
                {message.created_at && (
                  <span className="text-xs text-zinc-500 dark:text-zinc-500">
                    {new Date(message.created_at).toLocaleString('zh-CN')}
                  </span>
                )}
              </div>
              <p className="text-zinc-900 dark:text-white whitespace-pre-wrap">
                {message.content}
              </p>
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
}
