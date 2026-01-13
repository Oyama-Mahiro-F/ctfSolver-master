import { useApi } from '@/hooks/useApi';
import { agentApi } from '@/services/api';
import type { AgentStatus as AgentStatusType } from '@/types';
import { RippleButton } from '@/registry/magicui/ripple-button';
import { GlassCard } from '@/components/ui/liquid-glass';

export function AgentStatus() {
  const { data: statusData, loading, error, execute: refresh } = useApi<AgentStatusType>(
    () => agentApi.getAgentStatus(),
    { immediate: true }
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-zinc-600 dark:text-zinc-400">加载中...</div>
      </div>
    );
  }

  if (error || !statusData) {
    return (
      <div className="p-4 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-md">
        错误: {error?.message || '获取状态失败'}
      </div>
    );
  }

  const { statistics } = statusData;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-zinc-900 dark:text-white">Agent状态概览</h1>
        <RippleButton
          onClick={refresh}
          className="px-4 py-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-md hover:bg-zinc-800 dark:hover:bg-zinc-100"
          rippleColor="rgba(255, 255, 255, 0.3)"
        >
          刷新
        </RippleButton>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <GlassCard>
          <div className="text-sm text-zinc-600 dark:text-zinc-400 mb-1">总Agent数</div>
          <div className="text-3xl font-bold text-zinc-900 dark:text-white">
            {statistics.total_agents}
          </div>
        </GlassCard>
        <GlassCard>
          <div className="text-sm text-zinc-600 dark:text-zinc-400 mb-1">在线Agent</div>
          <div className="text-3xl font-bold text-green-600 dark:text-green-400">
            {statistics.online_agents}
          </div>
        </GlassCard>
        <GlassCard>
          <div className="text-sm text-zinc-600 dark:text-zinc-400 mb-1">离线Agent</div>
          <div className="text-3xl font-bold text-red-600 dark:text-red-400">
            {statistics.offline_agents}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
