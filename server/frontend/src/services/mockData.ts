import type { Task, Vuln, Agent, Page, Message, AgentStatus } from '@/types';

// Mock数据
export const mockTasks: Task[] = [
  {
    id: '1',
    target: 'https://example.com',
    description: '测试任务1 - 这是一个示例任务',
    status: 'running',
    is_running: true,
    flag: 'flag{test_flag_123}',
    pages_count: 5,
    vulns_count: 2,
    agent_id: 'agent-1',
    agent_name: 'Agent-1',
    created_at: new Date().toISOString(),
  },
  {
    id: '2',
    target: 'https://test.com',
    description: '测试任务2 - 已完成的任务',
    status: 'finished',
    is_running: false,
    flag: 'flag{completed_flag}',
    pages_count: 10,
    vulns_count: 5,
    agent_id: 'agent-2',
    agent_name: 'Agent-2',
    created_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: '3',
    target: 'https://demo.com',
    description: '测试任务3 - 待处理的任务',
    status: 'pending',
    is_running: false,
    flag: '',
    pages_count: 0,
    vulns_count: 0,
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
];

export const mockVulns: Vuln[] = [
  {
    id: 'vuln-1',
    vuln_type: 'SQL Injection',
    severity: 'HIGH',
    description: '在登录页面发现SQL注入漏洞',
    request: {
      method: 'POST',
      url: '/login',
      data: { username: "admin' OR '1'='1", password: 'test' },
    },
    response: {
      status: 200,
      data: { token: 'fake_token' },
    },
    discovered_at: new Date().toISOString(),
    task_id: '1',
  },
  {
    id: 'vuln-2',
    vuln_type: 'XSS',
    severity: 'MEDIUM',
    description: '在搜索功能中发现跨站脚本漏洞',
    request: {
      method: 'GET',
      url: '/search',
      params: { q: '<script>alert(1)</script>' },
    },
    response: {
      status: 200,
      html: '<div>搜索结果包含未转义的脚本</div>',
    },
    discovered_at: new Date(Date.now() - 3600000).toISOString(),
    task_id: '1',
  },
  {
    id: 'vuln-3',
    vuln_type: 'IDOR',
    severity: 'LOW',
    description: '发现不安全的直接对象引用',
    request: {
      method: 'GET',
      url: '/api/user/123',
    },
    response: {
      status: 200,
      data: { id: 123, email: 'user@example.com' },
    },
    discovered_at: new Date(Date.now() - 7200000).toISOString(),
    task_id: '2',
  },
];

export const mockAgents: Agent[] = [
  {
    id: 'agent-1',
    name: 'Agent-1',
    host: 'localhost',
    port: 8001,
    status: 'online',
    capabilities: {
      scanning: true,
      exploitation: true,
      reporting: true,
    },
    last_heartbeat: new Date().toISOString(),
    registered_at: new Date(Date.now() - 86400000).toISOString(),
    last_seen: new Date().toISOString(),
    start_time: new Date(Date.now() - 86400000).toISOString(),
    metadata: { version: '1.0.0' },
    tasks_count: 1,
  },
  {
    id: 'agent-2',
    name: 'Agent-2',
    host: 'localhost',
    port: 8002,
    status: 'online',
    capabilities: {
      scanning: true,
      exploitation: false,
      reporting: true,
    },
    last_heartbeat: new Date(Date.now() - 60000).toISOString(),
    registered_at: new Date(Date.now() - 172800000).toISOString(),
    last_seen: new Date(Date.now() - 60000).toISOString(),
    start_time: new Date(Date.now() - 172800000).toISOString(),
    metadata: { version: '1.1.0' },
    tasks_count: 1,
  },
  {
    id: 'agent-3',
    name: 'Agent-3',
    host: 'localhost',
    port: 8003,
    status: 'offline',
    capabilities: {
      scanning: true,
      exploitation: true,
      reporting: false,
    },
    last_heartbeat: new Date(Date.now() - 3600000).toISOString(),
    registered_at: new Date(Date.now() - 259200000).toISOString(),
    last_seen: new Date(Date.now() - 3600000).toISOString(),
    start_time: new Date(Date.now() - 259200000).toISOString(),
    metadata: { version: '0.9.0' },
    tasks_count: 0,
  },
];

export const mockPages: Page[] = [
  {
    id: 'page-1',
    name: '登录页面',
    description: '用户登录页面',
    key: '/login',
    request: {
      method: 'GET',
      url: '/login',
    },
    response: {
      status: 200,
      title: 'Login Page',
    },
    discovered_at: new Date().toISOString(),
    task_id: '1',
  },
  {
    id: 'page-2',
    name: '首页',
    description: '网站首页',
    key: '/',
    request: {
      method: 'GET',
      url: '/',
    },
    response: {
      status: 200,
      title: 'Home Page',
    },
    discovered_at: new Date(Date.now() - 1800000).toISOString(),
    task_id: '1',
  },
  {
    id: 'page-3',
    name: '用户资料页',
    description: '用户个人资料页面',
    key: '/profile',
    request: {
      method: 'GET',
      url: '/profile',
    },
    response: {
      status: 200,
      title: 'User Profile',
    },
    discovered_at: new Date(Date.now() - 3600000).toISOString(),
    task_id: '2',
  },
];

export const mockMessages: Message[] = [
  {
    id: 'msg-1',
    session_id: '1',
    role: 'system',
    content: '任务已启动，开始扫描目标...',
    status: 'success',
    type: 'pure',
    created_at: new Date(Date.now() - 3600000).toISOString(),
    timestamp: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: 'msg-2',
    session_id: '1',
    role: 'agent',
    content: '发现潜在漏洞：SQL注入',
    status: 'success',
    type: 'vulnerability',
    metadata: { vuln_id: 'vuln-1' },
    created_at: new Date(Date.now() - 1800000).toISOString(),
    timestamp: new Date(Date.now() - 1800000).toISOString(),
  },
  {
    id: 'msg-3',
    session_id: '1',
    role: 'system',
    content: '扫描完成，共发现2个漏洞',
    status: 'success',
    type: 'summary',
    created_at: new Date().toISOString(),
    timestamp: new Date().toISOString(),
  },
];

// Mock API响应函数
export const mockApi = {
  tasks: {
    getTasks: (params?: { status?: string; page?: number; per_page?: number }) => {
      return new Promise<{ success: boolean; data: Task[]; pagination?: any }>((resolve) => {
        setTimeout(() => {
          let filteredTasks = [...mockTasks];
          
          if (params?.status) {
            filteredTasks = filteredTasks.filter(t => t.status === params.status);
          }
          
          const page = params?.page || 1;
          const perPage = params?.per_page || 10;
          const start = (page - 1) * perPage;
          const end = start + perPage;
          const paginatedTasks = filteredTasks.slice(start, end);
          
          resolve({
            success: true,
            data: paginatedTasks,
            pagination: {
              page,
              per_page: perPage,
              total: filteredTasks.length,
              pages: Math.ceil(filteredTasks.length / perPage),
            },
          });
        }, 300); // 模拟网络延迟
      });
    },
    
    getTask: (taskId: string, includeMessages = false) => {
      return new Promise<{ success: boolean; data: Task }>((resolve) => {
        setTimeout(() => {
          const task = mockTasks.find(t => t.id === taskId);
          if (task) {
            const taskData = { ...task };
            if (includeMessages) {
              taskData.messages = mockMessages.filter(m => m.session_id === taskId);
            }
            resolve({ success: true, data: taskData });
          } else {
            resolve({ success: false, data: {} as Task });
          }
        }, 200);
      });
    },
    
    createTask: (data: any) => {
      return new Promise<{ success: boolean; data: Task }>((resolve) => {
        setTimeout(() => {
          const newTask: Task = {
            id: `task-${Date.now()}`,
            target: data.target,
            description: data.description || '',
            status: 'pending',
            is_running: false,
            flag: '',
            pages_count: 0,
            vulns_count: 0,
            agent_id: data.agent_id,
            agent_name: data.agent_id ? mockAgents.find(a => a.id === data.agent_id)?.name : undefined,
            created_at: new Date().toISOString(),
          };
          mockTasks.unshift(newTask);
          resolve({ success: true, data: newTask });
        }, 300);
      });
    },
    
    updateTask: (taskId: string, data: any) => {
      return new Promise<{ success: boolean; data: Task }>((resolve) => {
        setTimeout(() => {
          const task = mockTasks.find(t => t.id === taskId);
          if (task) {
            Object.assign(task, data);
            resolve({ success: true, data: task });
          } else {
            resolve({ success: false, data: {} as Task });
          }
        }, 200);
      });
    },
    
    deleteTask: (taskId: string) => {
      return new Promise<{ success: boolean }>((resolve) => {
        setTimeout(() => {
          const index = mockTasks.findIndex(t => t.id === taskId);
          if (index !== -1) {
            mockTasks.splice(index, 1);
            resolve({ success: true });
          } else {
            resolve({ success: false });
          }
        }, 200);
      });
    },
    
    toggleTaskRunning: (taskId: string) => {
      return new Promise<{ success: boolean; data: Task }>((resolve) => {
        setTimeout(() => {
          const task = mockTasks.find(t => t.id === taskId);
          if (task) {
            task.is_running = !task.is_running;
            task.status = task.is_running ? 'running' : 'pending';
            resolve({ success: true, data: task });
          } else {
            resolve({ success: false, data: {} as Task });
          }
        }, 200);
      });
    },
  },
  
  vulns: {
    getVulns: (taskId?: string) => {
      return new Promise<{ success: boolean; data: Vuln[] }>((resolve) => {
        setTimeout(() => {
          let filteredVulns = taskId 
            ? mockVulns.filter(v => v.task_id === taskId)
            : [...mockVulns];
          resolve({ success: true, data: filteredVulns });
        }, 200);
      });
    },
    
    getVuln: (vulnId: string) => {
      return new Promise<{ success: boolean; data: Vuln }>((resolve) => {
        setTimeout(() => {
          const vuln = mockVulns.find(v => v.id === vulnId);
          resolve({ 
            success: !!vuln, 
            data: vuln || {} as Vuln 
          });
        }, 200);
      });
    },
    
    deleteVuln: (vulnId: string) => {
      return new Promise<{ success: boolean }>((resolve) => {
        setTimeout(() => {
          const index = mockVulns.findIndex(v => v.id === vulnId);
          if (index !== -1) {
            mockVulns.splice(index, 1);
            resolve({ success: true });
          } else {
            resolve({ success: false });
          }
        }, 200);
      });
    },
  },
  
  agents: {
    getAgents: () => {
      return new Promise<{ success: boolean; data: Agent[] }>((resolve) => {
        setTimeout(() => {
          resolve({ success: true, data: [...mockAgents] });
        }, 200);
      });
    },
    
    getAgentStatus: () => {
      return new Promise<{ success: boolean; data: AgentStatus }>((resolve) => {
        setTimeout(() => {
          const onlineAgents = mockAgents.filter(a => a.status === 'online').length;
          const offlineAgents = mockAgents.filter(a => a.status === 'offline').length;
          resolve({
            success: true,
            data: {
              agents: [...mockAgents],
              statistics: {
                total_agents: mockAgents.length,
                online_agents: onlineAgents,
                offline_agents: offlineAgents,
              },
            },
          });
        }, 200);
      });
    },
  },
  
  pages: {
    getPages: (taskId?: string) => {
      return new Promise<{ success: boolean; data: Page[] }>((resolve) => {
        setTimeout(() => {
          let filteredPages = taskId
            ? mockPages.filter(p => p.task_id === taskId)
            : [...mockPages];
          resolve({ success: true, data: filteredPages });
        }, 200);
      });
    },
  },
  
  messages: {
    getMessages: (params?: { task_id?: string }) => {
      return new Promise<{ success: boolean; data: Message[] }>((resolve) => {
        setTimeout(() => {
          let filteredMessages = params?.task_id
            ? mockMessages.filter(m => m.session_id === params.task_id)
            : [...mockMessages];
          resolve({ success: true, data: filteredMessages });
        }, 200);
      });
    },
  },
};
