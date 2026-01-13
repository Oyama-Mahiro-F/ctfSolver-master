import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Welcome } from './components/Welcome';
import { TaskList } from './components/tasks/TaskList';
import { TaskDetail } from './components/tasks/TaskDetail';
import { VulnList } from './components/vulns/VulnList';
import { VulnDetail } from './components/vulns/VulnDetail';
import { AgentList } from './components/agents/AgentList';
import { AgentStatus } from './components/agents/AgentStatus';
import { PageList } from './components/pages/PageList';
import { MessageList } from './components/messages/MessageList';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/welcome" element={<Welcome />} />
        <Route path="/home" element={<Layout><TaskList /></Layout>} />
        <Route path="/" element={<Navigate to="/welcome" replace />} />
        <Route path="/tasks/:id" element={<Layout><TaskDetail /></Layout>} />
        <Route path="/vulns" element={<Layout><VulnList /></Layout>} />
        <Route path="/vulns/:id" element={<Layout><VulnDetail /></Layout>} />
        <Route path="/agents" element={<Layout><AgentList /></Layout>} />
        <Route path="/agents/status" element={<Layout><AgentStatus /></Layout>} />
        <Route path="/pages" element={<Layout><PageList /></Layout>} />
        <Route path="/messages" element={<Layout><MessageList /></Layout>} />
        <Route path="*" element={<Navigate to="/welcome" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
