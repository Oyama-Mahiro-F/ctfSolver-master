import { useParams, useNavigate } from 'react-router-dom';
import { useApi } from '@/hooks/useApi';
import { vulnApi } from '@/services/api';
import type { Vuln } from '@/types';
import { cn } from '@/lib/utils';
import { RippleButton } from '@/registry/magicui/ripple-button';
import { GlassCard } from '@/components/ui/liquid-glass';

export function VulnDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: vuln, loading, error } = useApi<Vuln>(
    () => vulnApi.getVuln(id!),
    { immediate: !!id }
  );

  const handleDelete = async () => {
    if (!id || !confirm('确定要删除这个漏洞吗？')) return;
    try {
      await vulnApi.deleteVuln(id);
      navigate('/vulns');
    } catch (err) {
      console.error('删除漏洞失败:', err);
    }
  };

  if (loading) {
    return <div className="text-center py-12">加载中...</div>;
  }

  if (error || !vuln) {
    return (
      <div className="p-4 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-md">
        错误: {error?.message || '漏洞不存在'}
      </div>
    );
  }

  const severityColors = {
    HIGH: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    MEDIUM: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    LOW: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <RippleButton
          onClick={() => navigate('/vulns')}
          className="text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white"
          rippleColor="rgba(0, 0, 0, 0.1)"
        >
          ← 返回
        </RippleButton>
        <RippleButton
          onClick={handleDelete}
          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          rippleColor="rgba(255, 255, 255, 0.3)"
        >
          删除
        </RippleButton>
      </div>

      <GlassCard>
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-2">
              {vuln.vuln_type}
            </h1>
            <span
              className={cn(
                'inline-block px-3 py-1 rounded-full text-xs font-medium',
                severityColors[vuln.severity] || severityColors.MEDIUM
              )}
            >
              {vuln.severity}
            </span>
          </div>
        </div>

        <div className="space-y-4 mb-6">
          <div>
            <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">描述</label>
            <p className="text-zinc-900 dark:text-white mt-1">{vuln.description || '无描述'}</p>
          </div>

          {vuln.discovered_at && (
            <div>
              <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">发现时间</label>
              <p className="text-zinc-900 dark:text-white mt-1">
                {new Date(vuln.discovered_at).toLocaleString('zh-CN')}
              </p>
            </div>
          )}

          {Object.keys(vuln.request || {}).length > 0 && (
            <div>
              <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">请求数据</label>
              <pre className="mt-1 p-4 bg-zinc-100 dark:bg-zinc-900 rounded-md overflow-auto text-sm">
                {JSON.stringify(vuln.request, null, 2)}
              </pre>
            </div>
          )}

          {Object.keys(vuln.response || {}).length > 0 && (
            <div>
              <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">响应数据</label>
              <pre className="mt-1 p-4 bg-zinc-100 dark:bg-zinc-900 rounded-md overflow-auto text-sm">
                {JSON.stringify(vuln.response, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </GlassCard>
    </div>
  );
}
