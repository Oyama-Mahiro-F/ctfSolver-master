import type { 
  ApiResponse, 
  Task, 
  Vuln, 
  Agent, 
  AgentStatus, 
  Page, 
  Message,
  Process,
  History
} from '@/types';
import { mockApi } from './mockData';

// 是否使用Mock数据（可以通过环境变量控制）
// 默认使用真实后端；仅在显式设置 VITE_USE_MOCK=true 时才使用 mock 数据
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

// 默认使用同源相对路径：开发时由 vite 的 /api 代理转发，
// 生产时由 nginx（或 proxy_server.py）转发，避免跨域与硬编码端口。
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

// 通用请求函数
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    
    // 检查响应是否成功
    if (!response.ok) {
      // 尝试解析错误响应
      let errorMessage = `HTTP error! status: ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.message || errorMessage;
      } catch {
        // 如果不是JSON响应，使用状态文本
        errorMessage = response.statusText || errorMessage;
      }
      throw new Error(errorMessage);
    }
    
    // 检查响应内容类型
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      return data;
    } else {
      // 如果不是JSON，返回文本响应
      const text = await response.text();
      throw new Error(`Unexpected response format: ${text}`);
    }
  } catch (error) {
    // 网络错误或其他错误
    if (error instanceof TypeError && error.message.includes('fetch')) {
      console.error('Network error - 无法连接到后端服务器:', error);
      throw new Error('无法连接到后端服务器，请确保后端服务正在运行在 http://localhost:5000');
    }
    console.error('API request failed:', error);
    throw error;
  }
}

// 任务API
export const taskApi = {
  // 获取任务列表
  getTasks: (params?: {
    agent_id?: string;
    status?: string;
    page?: number;
    per_page?: number;
  }) => {
    if (USE_MOCK) {
      return mockApi.tasks.getTasks(params) as Promise<ApiResponse<Task[]>>;
    }
    const queryParams = new URLSearchParams();
    if (params?.agent_id) queryParams.append('agent_id', params.agent_id);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.per_page) queryParams.append('per_page', params.per_page.toString());
    
    const query = queryParams.toString();
    return request<Task[]>(`/api/tasks${query ? `?${query}` : ''}`);
  },

  // 获取单个任务
  getTask: (taskId: string, includeMessages = false) => {
    if (USE_MOCK) {
      return mockApi.tasks.getTask(taskId, includeMessages) as Promise<ApiResponse<Task>>;
    }
    return request<Task>(`/api/tasks/${taskId}?include_messages=${includeMessages}`);
  },

  // 创建任务
  createTask: (data: {
    target: string;
    description?: string;
    agent_id?: string;
    flag?: string;
    task_path?: string;
  }) => {
    if (USE_MOCK) {
      return mockApi.tasks.createTask(data) as Promise<ApiResponse<Task>>;
    }
    return request<Task>('/api/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // 更新任务
  updateTask: (taskId: string, data: Partial<Task>) => {
    if (USE_MOCK) {
      return mockApi.tasks.updateTask(taskId, data) as Promise<ApiResponse<Task>>;
    }
    return request<Task>(`/api/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // 删除任务
  deleteTask: (taskId: string) => {
    if (USE_MOCK) {
      return mockApi.tasks.deleteTask(taskId) as Promise<ApiResponse<void>>;
    }
    return request<void>(`/api/tasks/${taskId}`, {
      method: 'DELETE',
    });
  },

  // 切换任务运行状态
  toggleTaskRunning: (taskId: string) => {
    if (USE_MOCK) {
      return mockApi.tasks.toggleTaskRunning(taskId) as Promise<ApiResponse<Task>>;
    }
    return request<Task>(`/api/tasks/${taskId}/toggle-running`, {
      method: 'PATCH',
    });
  },
};

// 漏洞API
export const vulnApi = {
  // 获取漏洞列表
  getVulns: (taskId?: string) => {
    if (USE_MOCK) {
      return mockApi.vulns.getVulns(taskId) as Promise<ApiResponse<Vuln[]>>;
    }
    const query = taskId ? `?task_id=${taskId}` : '';
    return request<Vuln[]>(`/api/vulns${query}`);
  },

  // 获取单个漏洞
  getVuln: (vulnId: string) => {
    if (USE_MOCK) {
      return mockApi.vulns.getVuln(vulnId) as Promise<ApiResponse<Vuln>>;
    }
    return request<Vuln>(`/api/vulns/${vulnId}`);
  },

  // 创建漏洞
  createVuln: (data: {
    vuln_type: string;
    severity?: 'HIGH' | 'MEDIUM' | 'LOW';
    description?: string;
    task_id?: string;
    request?: Record<string, any>;
    response?: Record<string, any>;
  }) => {
    return request<Vuln>('/api/vulns', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // 更新漏洞
  updateVuln: (vulnId: string, data: Partial<Vuln>) => {
    return request<Vuln>(`/api/vulns/${vulnId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // 删除漏洞
  deleteVuln: (vulnId: string) => {
    if (USE_MOCK) {
      return mockApi.vulns.deleteVuln(vulnId) as Promise<ApiResponse<void>>;
    }
    return request<void>(`/api/vulns/${vulnId}`, {
      method: 'DELETE',
    });
  },

  // 获取任务相关的漏洞
  getVulnsByTask: (taskId: string) => {
    if (USE_MOCK) {
      return mockApi.vulns.getVulns(taskId) as Promise<ApiResponse<Vuln[]>>;
    }
    return request<Vuln[]>(`/api/vulns/task/${taskId}`);
  },
};

// Agent API
export const agentApi = {
  // 获取Agent列表
  getAgents: () => {
    if (USE_MOCK) {
      return mockApi.agents.getAgents() as Promise<ApiResponse<Agent[]>>;
    }
    return request<Agent[]>('/api/agents');
  },

  // 获取单个Agent
  getAgent: (agentId: string) => {
    return request<Agent>(`/api/agents/${agentId}`);
  },

  // 注册Agent
  registerAgent: (data: {
    name: string;
    host: string;
    port: number;
    status?: string;
    capabilities?: Record<string, any>;
    metadata?: Record<string, any>;
  }) => {
    return request<Agent>('/api/agents/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // 更新Agent
  updateAgent: (agentId: string, data: Partial<Agent>) => {
    return request<Agent>(`/api/agents/${agentId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // 删除Agent
  deleteAgent: (agentId: string) => {
    return request<void>(`/api/agents/${agentId}`, {
      method: 'DELETE',
    });
  },

  // Agent心跳
  heartbeat: (agentId: string, data?: {
    status?: string;
    metadata?: Record<string, any>;
  }) => {
    return request<Agent>(`/api/agents/${agentId}/heartbeat`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    });
  },

  // 获取Agent状态
  getAgentStatus: () => {
    if (USE_MOCK) {
      return mockApi.agents.getAgentStatus() as Promise<ApiResponse<AgentStatus>>;
    }
    return request<AgentStatus>('/api/agents/status');
  },
};

// 页面API
export const pageApi = {
  // 获取页面列表
  getPages: (taskId?: string) => {
    if (USE_MOCK) {
      return mockApi.pages.getPages(taskId) as Promise<ApiResponse<Page[]>>;
    }
    const query = taskId ? `?task_id=${taskId}` : '';
    return request<Page[]>(`/api/pages${query}`);
  },

  // 获取单个页面
  getPage: (pageId: string) => {
    return request<Page>(`/api/pages/${pageId}`);
  },

  // 创建页面
  createPage: (data: {
    name: string;
    description?: string;
    key?: string;
    task_id?: string;
    request?: Record<string, any>;
    response?: Record<string, any>;
  }) => {
    return request<Page>('/api/pages', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // 更新页面
  updatePage: (pageId: string, data: Partial<Page>) => {
    return request<Page>(`/api/pages/${pageId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // 删除页面
  deletePage: (pageId: string) => {
    return request<void>(`/api/pages/${pageId}`, {
      method: 'DELETE',
    });
  },

  // 获取任务相关的页面
  getPagesByTask: (taskId: string) => {
    if (USE_MOCK) {
      return mockApi.pages.getPages(taskId) as Promise<ApiResponse<Page[]>>;
    }
    return request<Page[]>(`/api/pages/task/${taskId}`);
  },
};

// 消息API
export const messageApi = {
  // 获取消息列表
  getMessages: (params?: {
    session_id?: string;
    task_id?: string;
  }) => {
    if (USE_MOCK) {
      return mockApi.messages.getMessages(params) as Promise<ApiResponse<Message[]>>;
    }
    const queryParams = new URLSearchParams();
    if (params?.session_id) queryParams.append('session_id', params.session_id);
    if (params?.task_id) queryParams.append('task_id', params.task_id);
    
    const query = queryParams.toString();
    return request<Message[]>(`/api/messages${query ? `?${query}` : ''}`);
  },

  // 获取单个消息
  getMessage: (messageId: string) => {
    return request<Message>(`/api/messages/${messageId}`);
  },

  // 创建消息
  createMessage: (data: {
    session_id: string;
    role: string;
    content: string;
    status?: string;
    type?: string;
    metadata?: Record<string, any>;
  }) => {
    return request<Message>('/api/messages', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // 更新消息
  updateMessage: (messageId: string, data: Partial<Message>) => {
    return request<Message>(`/api/messages/${messageId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // 删除消息
  deleteMessage: (messageId: string) => {
    return request<void>(`/api/messages/${messageId}`, {
      method: 'DELETE',
    });
  },

  // 获取任务相关的消息
  getTaskMessages: (taskId: string) => {
    if (USE_MOCK) {
      return mockApi.messages.getMessages({ task_id: taskId }) as Promise<ApiResponse<Message[]>>;
    }
    return request<Message[]>(`/api/messages/task/${taskId}`);
  },
};

// 进程API
export const processApi = {
  // 创建进程
  createProcess: (processId: string, data?: { addition?: string }) => {
    return request<Process>(`/api/process/${processId}`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    });
  },

  // 获取进程消息
  getProcessMessages: (processId: string) => {
    return request<History[]>(`/api/process/${processId}`);
  },

  // 添加进程消息
  addProcessMessage: (processId: string, data: { metadata: Record<string, any> }) => {
    return request<History>(`/api/process/${processId}/message`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // 获取进程状态
  getProcessStatus: (processId: string) => {
    return request<{ status: string }>(`/api/process/${processId}/status`);
  },

  // 更新进程状态
  updateProcessStatus: (processId: string, data: { status: 'run' | 'pause'; addition?: string }) => {
    return request<{ status: string; addition?: string }>(`/api/process/${processId}/status`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};
