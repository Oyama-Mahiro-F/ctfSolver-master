import { useState, useEffect } from 'react';
import { taskApi } from '@/services/api';
import type { Task } from '@/types';
import { TaskCard } from './TaskCard';
import { TaskForm } from './TaskForm';
import { RippleButton } from '@/registry/magicui/ripple-button';
import { GlassCard } from '@/components/ui/liquid-glass';

export function TaskList() {
  const [showForm, setShowForm] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set());
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const fetchTasks = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await taskApi.getTasks({ status: statusFilter || undefined, page, per_page: 10 });
        if (response.success) {
          setTasks(response.data);
          if (response.pagination) {
            setTotalPages(response.pagination.pages || 1);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('获取任务失败'));
      } finally {
        setLoading(false);
      }
    };
    fetchTasks();
  }, [statusFilter, page]);

  const fetchTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await taskApi.getTasks({ status: statusFilter || undefined, page, per_page: 10 });
      if (response.success) {
        setTasks(response.data);
        if (response.pagination) {
          setTotalPages(response.pagination.pages || 1);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('获取任务失败'));
    } finally {
      setLoading(false);
    }
  };

  const handleToggleRunning = async (taskId: string) => {
    try {
      await taskApi.toggleTaskRunning(taskId);
      fetchTasks();
    } catch (err) {
      console.error('切换任务状态失败:', err);
    }
  };

  const refresh = () => {
    fetchTasks();
    setSelectedTasks(new Set());
  };

  const handleSelectTask = (taskId: string, checked: boolean) => {
    const newSelected = new Set(selectedTasks);
    if (checked) {
      newSelected.add(taskId);
    } else {
      newSelected.delete(taskId);
    }
    setSelectedTasks(newSelected);
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedTasks(new Set(tasks.map(t => t.id)));
    } else {
      setSelectedTasks(new Set());
    }
  };

  const handleBatchDelete = async () => {
    if (selectedTasks.size === 0) return;
    
    if (!confirm(`确定要删除选中的 ${selectedTasks.size} 个任务吗？此操作不可恢复。`)) {
      return;
    }

    setIsDeleting(true);
    try {
      const deletePromises = Array.from(selectedTasks).map(taskId => 
        taskApi.deleteTask(taskId).catch(err => {
          console.error(`删除任务 ${taskId} 失败:`, err);
          return { success: false };
        })
      );
      
      await Promise.all(deletePromises);
      setSelectedTasks(new Set());
      fetchTasks();
    } catch (err) {
      console.error('批量删除失败:', err);
      alert('批量删除失败，请重试');
    } finally {
      setIsDeleting(false);
    }
  };

  if (loading && tasks.length === 0) {
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
    <div className="space-y-6 relative z-0">
      <div className="flex items-center justify-end relative z-10">
        <RippleButton
          type="button"
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-md hover:bg-zinc-800 dark:hover:bg-zinc-100"
          rippleColor="rgba(255, 255, 255, 0.3)"
        >
          {showForm ? '取消' : '创建任务'}
        </RippleButton>
      </div>

      {showForm && (
        <GlassCard className="relative z-10">
          <TaskForm
            onSuccess={() => {
              setShowForm(false);
              refresh();
            }}
            onCancel={() => setShowForm(false)}
          />
        </GlassCard>
      )}

      <div className="flex gap-2 mb-4 relative z-10">
        <RippleButton
          type="button"
          onClick={() => {
            setStatusFilter('');
            setPage(1);
          }}
          className={`px-4 py-2 rounded-md transition-colors cursor-pointer relative z-10 ${
            statusFilter === ''
              ? 'bg-zinc-900 dark:bg-white text-white dark:text-zinc-900'
              : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700'
          }`}
          rippleColor={statusFilter === '' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.1)'}
        >
          全部
        </RippleButton>
        <RippleButton
          type="button"
          onClick={() => {
            setStatusFilter('pending');
            setPage(1);
          }}
          className={`px-4 py-2 rounded-md transition-colors cursor-pointer relative z-10 ${
            statusFilter === 'pending'
              ? 'bg-zinc-900 dark:bg-white text-white dark:text-zinc-900'
              : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700'
          }`}
          rippleColor={statusFilter === 'pending' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.1)'}
        >
          待处理
        </RippleButton>
        <RippleButton
          type="button"
          onClick={() => {
            setStatusFilter('running');
            setPage(1);
          }}
          className={`px-4 py-2 rounded-md transition-colors cursor-pointer relative z-10 ${
            statusFilter === 'running'
              ? 'bg-zinc-900 dark:bg-white text-white dark:text-zinc-900'
              : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700'
          }`}
          rippleColor={statusFilter === 'running' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.1)'}
        >
          运行中
        </RippleButton>
        <RippleButton
          type="button"
          onClick={() => {
            setStatusFilter('finished');
            setPage(1);
          }}
          className={`px-4 py-2 rounded-md transition-colors cursor-pointer relative z-10 ${
            statusFilter === 'finished'
              ? 'bg-zinc-900 dark:bg-white text-white dark:text-zinc-900'
              : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700'
          }`}
          rippleColor={statusFilter === 'finished' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.1)'}
        >
          已完成
        </RippleButton>
      </div>

      {tasks.length === 0 ? (
        <div className="text-center py-12 text-zinc-600 dark:text-zinc-400">
          暂无任务
        </div>
      ) : (
        <>
          <div className="flex items-center gap-2 mb-2 relative z-10">
            <input
              type="checkbox"
              checked={tasks.length > 0 && selectedTasks.size === tasks.length}
              onChange={(e) => handleSelectAll(e.target.checked)}
              className="w-4 h-4 text-zinc-900 bg-zinc-100 border-zinc-300 rounded focus:ring-zinc-500 dark:focus:ring-zinc-600 dark:ring-offset-zinc-800 focus:ring-2 dark:bg-zinc-700 dark:border-zinc-600"
            />
            <span className="text-sm text-zinc-600 dark:text-zinc-400">
              全选 ({selectedTasks.size}/{tasks.length})
            </span>
            {selectedTasks.size > 0 && (
              <>
                <RippleButton
                  type="button"
                  onClick={handleBatchDelete}
                  disabled={isDeleting}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed ml-4"
                  rippleColor="rgba(255, 255, 255, 0.3)"
                >
                  {isDeleting ? '删除中...' : `删除选中 (${selectedTasks.size})`}
                </RippleButton>
                <RippleButton
                  type="button"
                  onClick={() => setSelectedTasks(new Set())}
                  className="px-4 py-2 bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded-md hover:bg-zinc-300 dark:hover:bg-zinc-600 ml-2"
                  rippleColor="rgba(0, 0, 0, 0.1)"
                >
                  取消选择
                </RippleButton>
              </>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 auto-rows-fr">
            {tasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                isSelected={selectedTasks.has(task.id)}
                onSelect={(checked) => handleSelectTask(task.id, checked)}
              />
            ))}
          </div>
        </>
      )}

      <div className="flex justify-center gap-2 mt-6">
        <RippleButton
          onClick={() => setPage(Math.max(1, page - 1))}
          disabled={page === 1}
          className="px-4 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md disabled:opacity-50"
          rippleColor="rgba(0, 0, 0, 0.1)"
        >
          上一页
        </RippleButton>
        <span className="px-4 py-2">第 {page} 页 / 共 {totalPages} 页</span>
        <RippleButton
          onClick={() => setPage(page + 1)}
          disabled={page >= totalPages}
          className="px-4 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md disabled:opacity-50"
          rippleColor="rgba(0, 0, 0, 0.1)"
        >
          下一页
        </RippleButton>
      </div>
    </div>
  );
}
