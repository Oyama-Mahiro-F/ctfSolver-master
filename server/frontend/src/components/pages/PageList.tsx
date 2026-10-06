import { useState, useEffect } from 'react';
import { useApiList } from '@/hooks/useApi';
import { pageApi, taskApi } from '@/services/api';
import type { Page, Task } from '@/types';
import { Link } from 'react-router-dom';
import { GlassCard } from '@/components/ui/liquid-glass';

export function PageList() {
  const [taskFilter, setTaskFilter] = useState<string>('');
  const [tasks, setTasks] = useState<Task[]>([]);

  const { items: pages, loading, error } = useApiList<Page>(
    () => pageApi.getPages(taskFilter || undefined),
    { immediate: true }
  );

  useEffect(() => {
    taskApi.getTasks().then((response) => {
      if (response.success) {
        setTasks(response.data);
      }
    });
  }, []);

  if (loading && pages.length === 0) {
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

      {pages.length === 0 ? (
        <div className="text-center py-12 text-zinc-600 dark:text-zinc-400">
          暂无页面
        </div>
      ) : (
        <div className="space-y-4">
          {pages.map((page) => (
            <GlassCard key={page.id}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-2">
                    {page.name}
                  </h3>
                  <p className="text-sm text-zinc-600 dark:text-zinc-400 line-clamp-2">
                    {page.description || '无描述'}
                  </p>
                </div>
              </div>

              {page.key && (
                <div className="mb-2">
                  <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Key: </span>
                  <span className="font-mono text-sm text-zinc-900 dark:text-white">{page.key}</span>
                </div>
              )}

              {page.discovered_at && (
                <div className="text-xs text-zinc-500 dark:text-zinc-500">
                  发现时间: {new Date(page.discovered_at).toLocaleString('zh-CN')}
                </div>
              )}

              {page.task_id && (
                <div className="mt-4">
                  <Link
                    to={`/tasks/${page.task_id}`}
                    className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    查看任务 →
                  </Link>
                </div>
              )}
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
}
