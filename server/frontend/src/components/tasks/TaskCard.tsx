import { Link } from 'react-router-dom';
import type { Task } from '@/types';
import { cn } from '@/lib/utils';
import { GlassCard } from '@/components/ui/liquid-glass';

interface TaskCardProps {
  task: Task;
  isSelected?: boolean;
  onSelect?: (checked: boolean) => void;
}

const statusColors = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  running: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  finished: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
};

export function TaskCard({ task, isSelected = false, onSelect }: TaskCardProps) {
  const handleCardClick = (e: React.MouseEvent) => {
    // 如果点击的是复选框区域，不跳转
    const target = e.target as HTMLElement;
    if (target.closest('input[type="checkbox"]') || target.closest('label')) {
      e.preventDefault();
      e.stopPropagation();
      return;
    }
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation();
    onSelect?.(e.target.checked);
  };

  return (
    <div className="relative group h-full">
      <label 
        className="absolute top-4 left-4 z-[100] cursor-pointer" 
        style={{ pointerEvents: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        <input
          type="checkbox"
          checked={isSelected}
          onChange={handleCheckboxChange}
          onClick={(e) => e.stopPropagation()}
          className="w-5 h-5 text-blue-600 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-zinc-800 focus:ring-2 cursor-pointer shadow-md checked:bg-blue-600 checked:border-blue-600"
        />
      </label>
      <Link
        to={`/tasks/${task.id}`}
        onClick={handleCardClick}
        className="block h-full"
      >
        <GlassCard selected={isSelected} className="h-full relative min-h-[280px] flex flex-col">
          <div className="flex items-start justify-between mb-4 pl-6 flex-shrink-0">
            <div className="flex-1 min-w-0 pr-2">
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-2 truncate" title={task.target || '未命名任务'}>
                {task.target || '未命名任务'}
              </h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400 line-clamp-2">
                {task.description || '无描述'}
              </p>
            </div>
            <span
              className={cn(
                'px-3 py-1 rounded-full text-xs font-medium flex-shrink-0',
                statusColors[task.status] || statusColors.pending
              )}
            >
              {task.status === 'pending' ? '待处理' : task.status === 'running' ? '运行中' : '已完成'}
            </span>
          </div>
        
          <div className="flex items-center gap-4 text-sm text-zinc-600 dark:text-zinc-400 flex-wrap flex-shrink-0">
            {task.flag && (
              <div className="flex items-center gap-1 min-w-0 flex-shrink">
                <span className="font-medium">Flag:</span>
                <span className="font-mono text-xs truncate max-w-[150px]" title={task.flag}>{task.flag}</span>
              </div>
            )}
            {task.agent_name && (
              <div className="flex items-center gap-1 min-w-0 flex-shrink">
                <span>Agent:</span>
                <span className="truncate max-w-[100px]" title={task.agent_name}>{task.agent_name}</span>
              </div>
            )}
            <div className="flex items-center gap-4 ml-auto flex-shrink-0">
              <span>页面: {task.pages_count || 0}</span>
              <span>漏洞: {task.vulns_count || 0}</span>
            </div>
          </div>
          
          {task.created_at && (
            <div className="mt-auto pt-4 text-xs text-zinc-500 dark:text-zinc-500 flex-shrink-0">
              创建时间: {new Date(task.created_at).toLocaleString('zh-CN')}
            </div>
          )}
        </GlassCard>
      </Link>
    </div>
  );
}
