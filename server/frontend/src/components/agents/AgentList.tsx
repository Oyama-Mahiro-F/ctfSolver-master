import { useApiList } from '@/hooks/useApi';
import { agentApi } from '@/services/api';
import type { Agent } from '@/types';
import { cn } from '@/lib/utils';
import { RippleButton } from '@/registry/magicui/ripple-button';
import { GlassCard } from '@/components/ui/liquid-glass';

/**
 * agent 端上报的 capabilities 是字符串数组，而类型声明为对象。
 * 直接 Object.keys 数组会渲染出 "0"/"1"/"2"，这里统一成字符串列表。
 */
function toCapabilityList(caps: unknown): string[] {
  if (Array.isArray(caps)) {
    return caps.map((item) => String(item));
  }
  if (caps && typeof caps === 'object') {
    return Object.keys(caps as Record<string, unknown>);
  }
  return [];
}

export function AgentList() {
  const { items: agents, loading, error, refresh } = useApiList<Agent>(
    () => agentApi.getAgents(),
    { immediate: true }
  );

  if (loading && agents.length === 0) {
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
      <div className="flex items-center justify-end">
        <RippleButton
          onClick={refresh}
          className="px-4 py-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-md hover:bg-zinc-800 dark:hover:bg-zinc-100"
          rippleColor="rgba(255, 255, 255, 0.3)"
        >
          刷新
        </RippleButton>
      </div>

      {agents.length === 0 ? (
        <div className="text-center py-12 text-zinc-600 dark:text-zinc-400">
          暂无Agent
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <GlassCard key={agent.id}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-2">
                    {agent.name}
                  </h3>
                  <p className="text-sm text-zinc-600 dark:text-zinc-400">
                    {agent.host}:{agent.port}
                  </p>
                </div>
                <span
                  className={cn(
                    'px-3 py-1 rounded-full text-xs font-medium',
                    agent.status !== 'offline'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                  )}
                >
                  {agent.status !== 'offline' ? `在线 (${agent.status})` : '离线'}
                </span>
              </div>

              <div className="space-y-2 text-sm text-zinc-600 dark:text-zinc-400">
                {agent.last_heartbeat && (
                  <div>
                    最后心跳: {new Date(agent.last_heartbeat).toLocaleString('zh-CN')}
                  </div>
                )}
                {agent.registered_at && (
                  <div>
                    注册时间: {new Date(agent.registered_at).toLocaleString('zh-CN')}
                  </div>
                )}
                <div>任务数: {agent.tasks_count || 0}</div>
              </div>

              {toCapabilityList(agent.capabilities).length > 0 && (
                <div className="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-700">
                  <div className="text-xs font-medium text-zinc-600 dark:text-zinc-400 mb-2">
                    能力:
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {toCapabilityList(agent.capabilities).map((key) => (
                      <span
                        key={key}
                        className="px-2 py-1 bg-zinc-100 dark:bg-zinc-700 rounded text-xs"
                      >
                        {key}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
}
