import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { taskApi, vulnApi, pageApi, messageApi } from '@/services/api';
import type { Task, Vuln, Page, Message } from '@/types';
import { cn } from '@/lib/utils';
import { RippleButton } from '@/registry/magicui/ripple-button';
import { GlassCard } from '@/components/ui/liquid-glass';

export function TaskDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'info' | 'vulns' | 'pages' | 'messages'>('info');
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const refreshTask = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const response = await taskApi.getTask(id, true);
      if (response.success) {
        setTask(response.data);
      } else {
        throw new Error(response.message || '获取任务失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('获取任务失败'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshTask();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const [vulns, setVulns] = useState<Vuln[]>([]);
  const [pages, setPages] = useState<Page[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingVulns, setLoadingVulns] = useState(false);
  const [loadingPages, setLoadingPages] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);

  useEffect(() => {
    if (id) {
      // 加载漏洞
      setLoadingVulns(true);
      vulnApi.getVulnsByTask(id).then((response) => {
        if (response.success) {
          setVulns(response.data);
        }
        setLoadingVulns(false);
      });

      // 加载页面
      setLoadingPages(true);
      pageApi.getPagesByTask(id).then((response) => {
        if (response.success) {
          setPages(response.data);
        }
        setLoadingPages(false);
      });

      // 加载消息
      setLoadingMessages(true);
      messageApi.getTaskMessages(id).then((response) => {
        if (response.success) {
          setMessages(response.data);
        }
        setLoadingMessages(false);
      });
    }
  }, [id]);

  const handleToggleRunning = async () => {
    if (!id) return;
    try {
      await taskApi.toggleTaskRunning(id);
      refreshTask();
    } catch (err) {
      console.error('切换任务状态失败:', err);
    }
  };

  const handleDelete = async () => {
    if (!id || !confirm('确定要删除这个任务吗？')) return;
    try {
      await taskApi.deleteTask(id);
      navigate('/home');
    } catch (err) {
      console.error('删除任务失败:', err);
    }
  };

  if (loading) {
    return <div className="text-center py-12">加载中...</div>;
  }

  if (error || !task) {
    return (
      <div className="p-4 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-md">
        错误: {error?.message || '任务不存在'}
      </div>
    );
  }

  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    running: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    finished: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <RippleButton
          onClick={() => navigate('/home')}
          className="text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white"
          rippleColor="rgba(0, 0, 0, 0.1)"
        >
          ← 返回
        </RippleButton>
        <div className="flex gap-2">
          <RippleButton
            onClick={handleToggleRunning}
            className="px-4 py-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-md hover:bg-zinc-800 dark:hover:bg-zinc-100"
            rippleColor="rgba(255, 255, 255, 0.3)"
          >
            {task.is_running ? '停止' : '启动'}
          </RippleButton>
          <RippleButton
            onClick={handleDelete}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            rippleColor="rgba(255, 255, 255, 0.3)"
          >
            删除
          </RippleButton>
        </div>
      </div>

      <GlassCard>
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-2">
              {task.target || '未命名任务'}
            </h1>
            <span
              className={cn(
                'inline-block px-3 py-1 rounded-full text-xs font-medium',
                statusColors[task.status] || statusColors.pending
              )}
            >
              {task.status === 'pending' ? '待处理' : task.status === 'running' ? '运行中' : '已完成'}
            </span>
          </div>
        </div>

        <div className="space-y-4 mb-6">
          <div>
            <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">描述</label>
            <p className="text-zinc-900 dark:text-white">{task.description || '无描述'}</p>
          </div>
          {task.flag && (
            <div>
              <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Flag</label>
              <p className="font-mono text-zinc-900 dark:text-white">{task.flag}</p>
            </div>
          )}
          {task.agent_name && (
            <div>
              <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Agent</label>
              <p className="text-zinc-900 dark:text-white">{task.agent_name}</p>
            </div>
          )}
          {task.created_at && (
            <div>
              <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">创建时间</label>
              <p className="text-zinc-900 dark:text-white">
                {new Date(task.created_at).toLocaleString('zh-CN')}
              </p>
            </div>
          )}
        </div>

        <div className="border-t border-zinc-200 dark:border-zinc-700 pt-4">
          <div className="flex gap-2 mb-4">
            {(['info', 'vulns', 'pages', 'messages'] as const).map((tab) => (
              <RippleButton
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  'px-4 py-2 rounded-md text-sm font-medium',
                  activeTab === tab
                    ? 'bg-zinc-900 dark:bg-white text-white dark:text-zinc-900'
                    : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300'
                )}
                rippleColor={activeTab === tab ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.1)'}
              >
                {tab === 'info' ? '信息' : tab === 'vulns' ? `漏洞 (${vulns.length})` : tab === 'pages' ? `页面 (${pages.length})` : `消息 (${messages.length})`}
              </RippleButton>
            ))}
          </div>

          {activeTab === 'info' && (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">任务ID</label>
                <p className="text-zinc-900 dark:text-white font-mono text-sm">{task.id}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">目标</label>
                <p className="text-zinc-900 dark:text-white">{task.target || '未设置'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">描述</label>
                <p className="text-zinc-900 dark:text-white whitespace-pre-wrap">{task.description || '无描述'}</p>
              </div>
              {task.flag && (
                <div>
                  <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Flag</label>
                  <p className="font-mono text-zinc-900 dark:text-white bg-zinc-100 dark:bg-zinc-700 p-2 rounded">{task.flag}</p>
                </div>
              )}
              {task.agent_name && (
                <div>
                  <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Agent</label>
                  <p className="text-zinc-900 dark:text-white">{task.agent_name}</p>
                </div>
              )}
              {task.agent_id && (
                <div>
                  <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Agent ID</label>
                  <p className="text-zinc-900 dark:text-white font-mono text-sm">{task.agent_id}</p>
                </div>
              )}
              {task.task_path && (
                <div>
                  <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">任务路径</label>
                  <p className="text-zinc-900 dark:text-white font-mono text-sm break-all">{task.task_path}</p>
                </div>
              )}
              <div>
                <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">状态</label>
                <p className="text-zinc-900 dark:text-white">
                  {task.status === 'pending' ? '待处理' : task.status === 'running' ? '运行中' : '已完成'}
                  {task.is_running && <span className="ml-2 text-blue-600 dark:text-blue-400">(运行中)</span>}
                </p>
              </div>
              {task.created_at && (
                <div>
                  <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">创建时间</label>
                  <p className="text-zinc-900 dark:text-white">
                    {new Date(task.created_at).toLocaleString('zh-CN')}
                  </p>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-zinc-200 dark:border-zinc-700">
                <div>
                  <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">页面数量</label>
                  <p className="text-2xl font-bold text-zinc-900 dark:text-white">{task.pages_count || 0}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400">漏洞数量</label>
                  <p className="text-2xl font-bold text-zinc-900 dark:text-white">{task.vulns_count || 0}</p>
                </div>
              </div>
              {task.explorered_pages && task.explorered_pages.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400 mb-2 block">已探索页面</label>
                  <div className="space-y-1">
                    {task.explorered_pages.map((page, index) => (
                      <div key={index} className="text-sm text-zinc-900 dark:text-white font-mono bg-zinc-100 dark:bg-zinc-700 p-2 rounded">
                        {page}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'vulns' && (
            <div>
              {loadingVulns ? (
                <div>加载中...</div>
              ) : vulns.length === 0 ? (
                <div className="text-zinc-600 dark:text-zinc-400">暂无漏洞</div>
              ) : (
                <div className="space-y-2">
                  {vulns.map((vuln) => (
                    <GlassCard key={vuln.id} className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-zinc-900 dark:text-white">
                          {vuln.vuln_type}
                        </span>
                        <span
                          className={cn(
                            'px-2 py-1 rounded text-xs',
                            vuln.severity === 'HIGH'
                              ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                              : vuln.severity === 'MEDIUM'
                              ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                              : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          )}
                        >
                          {vuln.severity}
                        </span>
                      </div>
                      <p className="text-sm text-zinc-600 dark:text-zinc-400">{vuln.description}</p>
                    </GlassCard>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'pages' && (
            <div>
              {loadingPages ? (
                <div>加载中...</div>
              ) : pages.length === 0 ? (
                <div className="text-zinc-600 dark:text-zinc-400">暂无页面</div>
              ) : (
                <div className="space-y-2">
                  {pages.map((page) => (
                    <GlassCard key={page.id} className="p-4">
                      <div className="font-semibold text-zinc-900 dark:text-white mb-1">
                        {page.name}
                      </div>
                      <p className="text-sm text-zinc-600 dark:text-zinc-400">{page.description}</p>
                      {page.discovered_at && (
                        <div className="text-xs text-zinc-500 mt-2">
                          {new Date(page.discovered_at).toLocaleString('zh-CN')}
                        </div>
                      )}
                    </GlassCard>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'messages' && (
            <div>
              {loadingMessages ? (
                <div>加载中...</div>
              ) : messages.length === 0 ? (
                <div className="text-zinc-600 dark:text-zinc-400">暂无消息</div>
              ) : (
                <div className="space-y-2">
                  {messages.map((message) => (
                    <GlassCard key={message.id} className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
                          {message.role} - {message.type}
                        </span>
                        {message.created_at && (
                          <span className="text-xs text-zinc-500">
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
          )}
        </div>
      </GlassCard>
    </div>
  );
}
