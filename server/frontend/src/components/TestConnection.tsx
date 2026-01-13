import { useState } from 'react';
import { taskApi } from '@/services/api';
import { RippleButton } from '@/registry/magicui/ripple-button';

export function TestConnection() {
  const [status, setStatus] = useState<string>('');
  const [error, setError] = useState<string>('');

  const testConnection = async () => {
    setStatus('测试中...');
    setError('');
    try {
      const response = await taskApi.getTasks();
      setStatus(`成功！获取到 ${response.data.length} 个任务`);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '未知错误';
      setError(errorMsg);
      setStatus('失败');
      console.error('连接测试失败:', err);
    }
  };

  return (
    <div className="p-4 bg-white/80 dark:bg-zinc-800/80 rounded-lg border border-zinc-200 dark:border-zinc-700">
      <h3 className="text-lg font-semibold mb-2">连接测试</h3>
      <RippleButton
        onClick={testConnection}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 mb-2"
        rippleColor="rgba(255, 255, 255, 0.3)"
      >
        测试后端连接
      </RippleButton>
      {status && (
        <div className={`p-2 rounded ${error ? 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200' : 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'}`}>
          {status}
        </div>
      )}
      {error && (
        <div className="p-2 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded mt-2">
          错误详情: {error}
        </div>
      )}
      <div className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
        API地址: {import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}
      </div>
    </div>
  );
}
