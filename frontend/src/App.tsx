import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import { MainLayout } from './components/MainLayout';
import { ViewProvider } from './contexts/ViewContext';
import { ProjectProvider } from './contexts/ProjectContext';
import { ChatView } from './components/ChatView';
import { JSONPlanView } from './components/JSONPlanView';
import { CodeChangesView } from './components/CodeChangesView';
import { TestResultsView } from './components/TestResultsView';
import { useWebSocket } from './hooks/useWebSocket';
import { AIService } from './services/aiService';
import { JsonRpcService } from './services/jsonRpcService';
import { useAISession } from './hooks/useAISession';
import { useChat } from './hooks/useChat';
import { SessionStatus } from './types/ai';
import { Agent } from './types/agent';
import { ProjectIntegration } from './components/ProjectIntegration';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
const USER_ID = 'demo-user';

// This will be loaded from backend
let AGENTS: Agent[] = [];

function App() {
  // Theme state
  const [theme, setTheme] = useState<'light' | 'dark'>(
    (localStorage.getItem('app.theme') as 'light' | 'dark') || 'light'
  );

  // WebSocket connection
  const { status: wsStatus, ws } = useWebSocket(WS_URL);

  // AIService instance
  const [aiService, setAIService] = useState<AIService | undefined>(undefined);

  // Current agent and plan state
  const [agents, setAgents] = useState<Agent[]>([]);
  const [currentAgent, setCurrentAgent] = useState<Agent | null>(null);
  const [currentPlan, setCurrentPlan] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  // JSON-RPC service for reuse
  const [jsonRpcService, setJsonRpcService] = useState<JsonRpcService | undefined>(undefined);

  // Initialize services when WebSocket is connected
  useEffect(() => {
    if (ws && wsStatus === 'connected') {
      console.log('[App] WebSocket is connected, initializing services');
      const jsonRpc = new JsonRpcService(ws);
      setJsonRpcService(jsonRpc);
      setAIService(new AIService(jsonRpc));
    } else {
      setJsonRpcService(undefined);
      setAIService(undefined);
    }
  }, [ws, wsStatus]);

  // AI session management
  const {
    sessionInfo,
    status: sessionStatus,
    error: sessionError,
    startSession,
    sendUserMessage
  } = useAISession(aiService, USER_ID);

  // Chat state management
  const {
    messages,
    loading,
    addUserMessage,
    startAIMessage,
    appendAIChunk,
    addSystemMessage,
  } = useChat({ currentAgentId: currentAgent?.id });

  // Function to reload agents
  const reloadAgents = useCallback(async () => {
    if (!aiService) return;
    
    try {
      console.log('[App] Reloading agents...');
      const loadedAgents = await aiService.listAgents();
      const mappedAgents = loadedAgents.map((agent: any) => ({
        id: (agent.agent_id || agent.id).toLowerCase(),
        name: agent.name,
        role: agent.role,
        description: agent.description,
        color: agent.color,
        icon: agent.icon || '🤖',
        status: 'online' as const,
        shortcut: agent.shortcut
      }));
      setAgents(mappedAgents);
      AGENTS = mappedAgents;
      
      // If current agent is not in the new list, switch to Alice
      if (currentAgent && !mappedAgents.find((a: Agent) => a.id === currentAgent.id)) {
        const alice = mappedAgents.find((a: Agent) => a.id.toLowerCase() === 'a');
        if (alice) {
          // Switch to Alice
          try {
            await aiService.switchAgent(alice.id);
            setCurrentAgent(alice);
            addSystemMessage(`Switched to ${alice.name}`);
          } catch (error) {
            console.error('Failed to switch to Alice:', error);
          }
        }
      }
    } catch (error) {
      console.error('Failed to reload agents:', error);
    }
  }, [aiService, currentAgent, addSystemMessage]);

  // Listen for workspace changes
  useEffect(() => {
    const handleWorkspaceChange = () => {
      console.log('[App] Workspace changed, reloading agents...');
      reloadAgents();
    };

    window.addEventListener('workspace-changed', handleWorkspaceChange);
    return () => {
      window.removeEventListener('workspace-changed', handleWorkspaceChange);
    };
  }, [reloadAgents]);

  // Start session and load agents on mount
  useEffect(() => {
    const initializeSession = async () => {
      if (aiService && sessionStatus !== SessionStatus.Active) {
        setIsLoading(true);
        try {
          await startSession();
          
          // Load agents from backend
          const loadedAgents = await aiService.listAgents();
          // Map backend format to frontend format
          const mappedAgents = loadedAgents.map((agent: any) => ({
            id: (agent.agent_id || agent.id).toLowerCase(),  // Ensure lowercase for consistency
            name: agent.name,
            role: agent.role,
            description: agent.description,
            color: agent.color,
            icon: agent.icon || '🤖',
            status: 'online' as const,
            shortcut: agent.shortcut
          }));
          setAgents(mappedAgents);
          AGENTS = mappedAgents; // Update global for compatibility
          
          // Get current agent from backend
          const currentAgentId = await aiService.getCurrentAgent();
          if (currentAgentId) {
            const agent = mappedAgents.find((a: Agent) => a.id.toLowerCase() === currentAgentId.toLowerCase());
            if (agent) {
              setCurrentAgent(agent);
            }
          } else if (mappedAgents.length > 0) {
            // If no current agent, default to first (should be Alice)
            const defaultAgent = mappedAgents.find((a: Agent) => a.id.toLowerCase() === 'a') || mappedAgents[0];
            await handleAgentSelect(defaultAgent.id);
          }
        } catch (error) {
          console.error('Failed to start session:', error);
        } finally {
          setIsLoading(false);
        }
      }
    };

    initializeSession();
  }, [aiService, sessionStatus, startSession]);

  // No need for separate sync, handled in initialization

  // Handle agent switch
  const handleAgentSelect = useCallback(async (agentId: string) => {
    if (!aiService || sessionStatus !== SessionStatus.Active) return;
    
    setIsLoading(true);
    try {
      await aiService.switchAgent(agentId.toLowerCase());
      // Don't update state here - the agent.switched notification will handle it
    } catch (error) {
      console.error('Failed to switch agent:', error);
      addSystemMessage('Failed to switch agent');
    } finally {
      setIsLoading(false);
    }
  }, [aiService, sessionStatus, addSystemMessage]);

  // Handle handoff to agent
  const handleHandoffToAgent = useCallback(async (agentId: string) => {
    if (!aiService || sessionStatus !== SessionStatus.Active) return;
    
    try {
      await aiService.handoffToAgent(agentId.toLowerCase());
      const agent = agents.find(a => a.id === agentId.toLowerCase());
      if (agent) {
        addSystemMessage(`Handing off to ${agent.name}...`);
      }
    } catch (error) {
      console.error('Failed to handoff:', error);
      addSystemMessage('Failed to handoff to agent');
    }
  }, [aiService, sessionStatus, addSystemMessage]);

  // Send message handler
  const handleSendMessage = useCallback(async (text: string) => {
    if (!aiService || sessionStatus !== SessionStatus.Active) return;
    
    addUserMessage(text);
    
    // Handle commands
    if (text.trim().startsWith('/')) {
      try {
        startAIMessage();
        const result = await aiService.dispatchCommand(text.trim());
        if (result.error) {
          addSystemMessage(`ERROR: ${result.error}`);
        } else {
          const output = typeof result.output === 'string' 
            ? result.output 
            : JSON.stringify(result.output, null, 2);
          addSystemMessage(output || JSON.stringify(result));
        }
      } catch (err: any) {
        appendAIChunk({ 
          content: `Command error: ${err.message || err}`, 
          index: 0, 
          isFinal: true 
        });
      }
    } else {
      startAIMessage();
      await sendUserMessage(text);
    }
  }, [aiService, sessionStatus, addUserMessage, startAIMessage, appendAIChunk, addSystemMessage, sendUserMessage]);

  // Set AI message chunk handler
  useEffect(() => {
    if (!aiService) return;
    
    let introductionStarted = false;
    
    aiService.onAIMessageChunk((chunk) => {
      // If we receive a chunk without loading state being true,
      // it's likely an agent introduction, so start the AI message
      if (!loading && chunk.content && !introductionStarted) {
        introductionStarted = true;
        startAIMessage();
      }
      appendAIChunk(chunk);
      
      // Reset the flag when message is final
      if (chunk.isFinal) {
        introductionStarted = false;
      }
    });
    return () => {
      aiService.onAIMessageChunk(() => {});
    };
  }, [aiService, appendAIChunk, loading, startAIMessage]);

  // Set agent change handler
  useEffect(() => {
    if (!aiService) return;
    
    const unsubscribe = aiService.onAgentChanged(async (agentId) => {
      console.log('[App] Agent changed notification received:', agentId);
      const agent = agents.find(a => a.id.toLowerCase() === agentId.toLowerCase());
      if (agent) {
        setCurrentAgent(agent);
        addSystemMessage(`Switched to ${agent.name}`);
      }
    });
    
    return unsubscribe;
  }, [aiService, agents, addSystemMessage]);

  // Handle theme toggle
  const toggleTheme = useCallback(() => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('app.theme', newTheme);
  }, [theme]);

  // Mock data for demo views
  const mockPlanData = {
    id: 'plan-1',
    name: 'Feature Implementation Plan',
    version: 1,
    tasks: [
      {
        id: 'task-1',
        name: 'Setup Project Structure',
        description: 'Initialize the project with required dependencies',
        status: 'completed',
        subtasks: [
          { id: 'sub-1', name: 'Create directories', status: 'completed' },
          { id: 'sub-2', name: 'Install packages', status: 'completed' }
        ]
      },
      {
        id: 'task-2',
        name: 'Implement Core Features',
        description: 'Build the main functionality',
        status: 'in_progress',
        subtasks: [
          { id: 'sub-3', name: 'Create components', status: 'completed' },
          { id: 'sub-4', name: 'Add state management', status: 'in_progress' }
        ]
      }
    ]
  };

  const mockCodeChanges = {
    files: [
      {
        id: 'file-1',
        path: 'src/components/Button.tsx',
        status: 'modified' as const,
        additions: 15,
        deletions: 5,
        oldContent: 'export const Button = () => {\n  return <button>Click</button>;\n};',
        newContent: 'export const Button = ({ onClick, label }) => {\n  return <button onClick={onClick}>{label}</button>;\n};'
      },
      {
        id: 'file-2',
        path: 'src/utils/helpers.ts',
        status: 'added' as const,
        additions: 50,
        deletions: 0,
        oldContent: '',
        newContent: 'export function formatDate(date: Date): string {\n  return date.toISOString();\n}'
      }
    ],
    summary: {
      totalFiles: 2,
      totalAdditions: 65,
      totalDeletions: 5
    }
  };

  const mockTestResults = {
    summary: {
      total: 156,
      passed: 142,
      failed: 8,
      skipped: 6,
      duration: 12.5
    },
    suites: [
      {
        id: 'suite-1',
        name: 'Component Tests',
        path: 'src/components',
        status: 'failed' as const,
        duration: 4.2,
        tests: [
          { id: 'test-1', name: 'renders correctly', status: 'passed' as const, duration: 0.045 },
          { 
            id: 'test-2', 
            name: 'handles user interaction', 
            status: 'failed' as const, 
            duration: 0.123,
            error: {
              message: 'Expected button to be disabled',
              stack: 'at Button.test.tsx:45:23'
            }
          }
        ]
      }
    ]
  };

  // Enhanced agent context for ContextPanel
  const agentContext = currentAgent ? {
    ...currentAgent,
    context: {
      files: ['src/App.tsx', 'src/components/Button.tsx'],
      variables: { projectName: 'AI Whisperer', version: '1.0.0' },
      history: messages.map(m => `${m.sender}: ${m.content.substring(0, 50)}...`)
    }
  } : null;

  return (
    <Router>
      <ProjectProvider>
        <ProjectIntegration jsonRpcService={jsonRpcService} />
        <ViewProvider>
          <MainLayout 
            theme={theme} 
            isLoading={isLoading}
            currentAgent={agentContext}
            currentPlan={currentPlan}
          >
          <Routes>
            {/* Chat Route */}
            <Route path="/chat" element={
              <ChatView 
                messages={messages}
                currentAgent={currentAgent}
                agents={agents}
                onSendMessage={handleSendMessage}
                onAgentSelect={handleAgentSelect}
                onHandoffToAgent={handleHandoffToAgent}
                sessionStatus={sessionStatus}
                wsStatus={wsStatus}
                sessionError={sessionError || undefined}
                onThemeToggle={toggleTheme}
                theme={theme}
              />
            } />
            
            {/* Plans Route */}
            <Route path="/plans" element={
              <JSONPlanView data={mockPlanData} />
            } />
            
            {/* Code Route */}
            <Route path="/code" element={
              <CodeChangesView data={mockCodeChanges} />
            } />
            
            {/* Tests Route */}
            <Route path="/tests" element={
              <TestResultsView data={mockTestResults} />
            } />
            
            {/* Settings Route */}
            <Route path="/settings" element={
              <div style={{ padding: '20px' }}>
                <h2>Settings</h2>
                <div>
                  <label>
                    <input 
                      type="checkbox" 
                      checked={theme === 'dark'} 
                      onChange={toggleTheme}
                    />
                    Dark Theme
                  </label>
                </div>
              </div>
            } />
            
            {/* Default Route */}
            <Route path="/" element={<Navigate to="/chat" replace />} />
          </Routes>
        </MainLayout>
      </ViewProvider>
    </ProjectProvider>
    </Router>
  );
}

export default App;