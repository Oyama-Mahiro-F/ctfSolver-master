import { useState, useEffect } from 'react';
import { useApiList } from '@/hooks/useApi';
import { vulnApi, taskApi } from '@/services/api';
import type { Vuln, Task } from '@/types';
import { cn } from '@/lib/utils';
import { Link } from 'react-router-dom';
import { GlassCard } from '@/components/ui/liquid-glass';

export function VulnList() {
  const [taskFilter, setTaskFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [tasks, setTasks] = useState<Task[]>([]);

  const { items: vulns, loading, error, refresh } = useApiList<Vuln>(
    () => vulnApi.getVulns(taskFilter || undefined),
    { immediate: true }
  );

  useEffect(() => {
    taskApi.getTasks().then((response) => {
      if (response.success) {
        setTasks(response.data);
      }
    });
  }, []);

  const filteredVulns = severityFilter
    ? vulns.filter((v) => v.severity === severityFilter)
    : vulns;

  const severityColors = {
    HIGH: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    MEDIUM: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    LOW: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  };

  if (loading && vulns.length === 0) {
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
        <div className="flex-1">
          <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
            按严重程度筛选
          </label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-white"
          >
            <option value="">全部</option>
            <option value="HIGH">高危</option>
            <option value="MEDIUM">中危</option>
            <option value="LOW">低危</option>
          </select>
        </div>
      </div>

      {filteredVulns.length === 0 ? (
        <div className="text-center py-12 text-zinc-600 dark:text-zinc-400">
          暂无漏洞
        </div>
      ) : (
        <div className="space-y-4">
          {filteredVulns.map((vuln) => (
            <Link
              key={vuln.id}
              to={`/vulns/${vuln.id}`}
              className="block"
            >
              <GlassCard>
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-2">
                    {vuln.vuln_type}
                  </h3>
                  <p className="text-sm text-zinc-600 dark:text-zinc-400 line-clamp-2">
                    {vuln.description || '无描述'}
                  </p>
                </div>
                <span
                  className={cn(
                    'px-3 py-1 rounded-full text-xs font-medium',
                    severityColors[vuln.severity] || severityColors.MEDIUM
                  )}
                >
                  {vuln.severity}
                </span>
              </div>
              {vuln.discovered_at && (
                <div className="text-xs text-zinc-500 dark:text-zinc-500">
                  发现时间: {new Date(vuln.discovered_at).toLocaleString('zh-CN')}
                </div>
              )}
              </GlassCard>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
