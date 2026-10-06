// API响应基础类型
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  pagination?: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

// 任务类型
export interface Task {
  id: string;
  target: string;
  description: string;
  status: 'pending' | 'running' | 'finished';
  is_running: boolean;
  flag: string;
  task_path?: string;
  explorered_pages?: string[];
  pages_count?: number;
  vulns_count?: number;
  agent_id?: string;
  agent_name?: string;
  created_at: string;
  messages?: Message[];
}

// 漏洞类型
export interface Vuln {
  id: string;
  vuln_type: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  description: string;
  request: Record<string, any>;
  response: Record<string, any>;
  discovered_at: string;
  task_id?: string;
}

// Agent类型
export interface Agent {
  id: string;
  name: string;
  host: string;
  port: number;
  // agent 端实际上报的是业务状态（idle/running/exploring/detecting/error 等），
  // 只有显式 offline 才代表离线
  status: 'online' | 'offline' | 'idle' | 'running' | 'exploring' | 'detecting' | 'busy' | 'error';
  capabilities: Record<string, any>;
  last_heartbeat?: string;
  registered_at: string;
  last_seen?: string;
  start_time?: string;
  metadata: Record<string, any>;
  tasks_count?: number;
}

// Agent状态统计
export interface AgentStatus {
  agents: Agent[];
  statistics: {
    total_agents: number;
    online_agents: number;
    offline_agents: number;
  };
}

// 页面类型
export interface Page {
  id: string;
  name: string;
  request: Record<string, any>;
  response: Record<string, any>;
  description: string;
  key: string;
  discovered_at: string;
  task_id?: string;
}

// 消息类型
export interface Message {
  id: string;
  session_id: string;
  role: string;
  content: string;
  status: string;
  type: 'pure' | 'solution' | 'page' | 'summary' | 'vulnerability' | 'question';
  metadata?: Record<string, any>;
  created_at: string;
  timestamp?: string;
  messageType?: string; // 前端兼容字段
}

// 进程类型
export interface Process {
  id: string;
  status: 'run' | 'pause';
  addition?: string;
}

// 历史记录类型
export interface History {
  id: string;
  metadata: Record<string, any>;
  process_id: string;
}
