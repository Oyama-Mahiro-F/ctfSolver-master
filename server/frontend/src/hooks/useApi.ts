import { useState, useEffect, useCallback, useRef } from 'react';

interface UseApiOptions {
  immediate?: boolean;
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
}

/**
 * 把最新值放进 ref，使依赖它的回调保持稳定引用。
 *
 * 调用方（各个列表页）普遍传入内联箭头函数作为 apiCall，
 * 若把 apiCall 放进 useCallback 的依赖数组，每次 render 都会产生新的
 * execute/fetch，进而触发 useEffect 反复重新请求，形成
 * “请求 → setState → render → 再请求” 的无限循环。
 */
function useLatest<T>(value: T) {
  const ref = useRef(value);
  ref.current = value;
  return ref;
}

export function useApi<T>(
  apiCall: () => Promise<{ success: boolean; data: T; message: string }>,
  options: UseApiOptions = {}
) {
  const { immediate = false } = options;
  const apiCallRef = useLatest(apiCall);
  const onSuccessRef = useLatest(options.onSuccess);
  const onErrorRef = useLatest(options.onError);

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiCallRef.current();
      if (response.success) {
        setData(response.data);
        onSuccessRef.current?.(response.data);
      } else {
        throw new Error(response.message);
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      onErrorRef.current?.(error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate, execute]);

  return { data, loading, error, execute, setData };
}

// 用于列表数据的Hook
export function useApiList<T>(
  apiCall: () => Promise<{ success: boolean; data: T[]; message: string }>,
  options: UseApiOptions = {}
) {
  const { immediate = true } = options;
  const apiCallRef = useLatest(apiCall);
  const onSuccessRef = useLatest(options.onSuccess);
  const onErrorRef = useLatest(options.onError);

  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiCallRef.current();
      if (response.success) {
        setItems(response.data);
        onSuccessRef.current?.(response.data);
      } else {
        throw new Error(response.message);
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      onErrorRef.current?.(error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (immediate) {
      fetch();
    }
  }, [immediate, fetch]);

  const refresh = useCallback(() => {
    fetch();
  }, [fetch]);

  return { items, loading, error, refresh, setItems };
}
