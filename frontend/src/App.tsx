import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ChatMessage, MessageSender } from './types/chat';
import { Agent } from './types/agent';
import { SessionStatus, MessageStatus } from './types/ai';
import './App.css';
import './themes.css';
import { MainLayout } from './components/MainLayout';
import { ViewProvider } from './contexts/ViewContext';
import { ProjectProvider } from './contexts/ProjectContext';
import { ChatView } from './components/ChatView';
import { ChannelChatView } from './components/ChannelChatView';
import JSONPlanView from './components/JSONPlanView';
import { CodeChangesView } from './components/CodeChangesView';
import { TestResultsView } from './components/TestResultsView';
import { useWebSocket } from './hooks/useWebSocket';
import { AIService } from './services/aiService';
import { JsonRpcService } from './services/jsonRpcService';
import { useAISession } from './hooks/useAISession';
import { useChat } from './hooks/useChat';
import { ProjectIntegration } from './components/ProjectIntegration';
import { FileBrowser } from './components/FileBrowser';
import { MainTabs } from './components/MainTabs';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
const USER_ID = 'demo-user';


function App() {
  // Theme state
  const [theme, setTheme] = useState<'light' | 'dark'>(
    (localStorage.getItem('app.theme') as 'light' | 'dark') || 'light'
  );

  // Add debugging for initial render
  // console.log('[App] Component rendering...');

  // WebSocket connection
  const { status: wsStatus, ws } = useWebSocket(WS_URL);

  // AIService instance
  const [aiService, setAIService] = useState<AIService | undefined>(undefined);

  // Current agent state
  const [currentAgent, setCurrentAgent] = useState<Agent | undefined>(undefined);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true); // for very first app load only

  // JSON-RPC service for reuse
  const [jsonRpcService, setJsonRpcService] = useState<JsonRpcService | undefined>(undefined);
  
  // Tab opening handlers
  const [tabHandlers, setTabHandlers] = useState<{ 
    openFilesTab?: () => void;
    openEditorTab?: (filePath: string) => void;
    openSettingsTab?: () => void;
  }>({});
  
  // Track which agent we've updated messages for to prevent duplicate updates
  const lastUpdatedAgentRef = useRef<string | null>(null);

  // Add debugging for state
  // console.log('[App] Current state:', {
  //   wsStatus,
  //   currentAgent: currentAgent?.name,
  //   agentsCount: agents.length,
  //   isLoading,
  //   isInitialLoading
  // });

  // Initialize services when WebSocket is connected
  useEffect(() => {
    if (ws && wsStatus === 'connected') {
      console.log('[App] WebSocket is connected, initializing services');
      // Use longer timeout for file operations which can be slow on large workspaces
      const jsonRpc = new JsonRpcService(ws, 30000); // 30 second timeout
      setJsonRpcService(jsonRpc);
      setAIService(new AIService(jsonRpc));
    } else {
      setJsonRpcService(undefined);
      setAIService(undefined);
    }
  }, [ws, wsStatus]);

  // AI session management
  const {
    status: sessionStatus,
    error: sessionError,
    startSession,
    sendUserMessage
  } = useAISession(aiService, USER_ID);

  // Chat state management
  const {
    messages,
    loading,
    currentAIMessage,
    addUserMessage,
    startAIMessage,
    appendAIChunk,
    addSystemMessage,
    updateMessageAgent,
  } = useChat({ 
    currentAgentId: currentAgent?.id,
    currentAgent: currentAgent || undefined
  });

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

  // Start session and load agents on mount
  useEffect(() => {
    const initializeSession = async () => {
      if (aiService && sessionStatus !== SessionStatus.Active) {
        setIsInitialLoading(true);
        try {
          console.log('[App] Starting session...');
          await startSession();
          console.log('[App] Session started, loading agents...');
          // Load agents from backend
          const loadedAgents = await aiService.listAgents();
          console.log('[App] Loaded agents:', loadedAgents);
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
          console.log('[App] Mapped agents:', mappedAgents);
          
          // Get current agent from backend
          const currentAgentId = await aiService.getCurrentAgent();
          console.log('[App] Current agent ID from backend:', currentAgentId);
          if (currentAgentId) {
            const agent = mappedAgents.find((a: Agent) => a.id.toLowerCase() === currentAgentId.toLowerCase());
            if (agent) {
              console.log('[App] Setting current agent:', agent);
              setCurrentAgent(agent);
            }
          } else if (mappedAgents.length > 0) {
            // If no current agent, default to first (should be Alice)
            const defaultAgent = mappedAgents.find((a: Agent) => a.id.toLowerCase() === 'a') || mappedAgents[0];
            console.log('[App] Setting default agent:', defaultAgent);
            // Wait a bit for session to be fully active before switching
            setTimeout(async () => {
              try {
                await handleAgentSelect(defaultAgent.id);
              } catch (error) {
                console.error('[App] Failed to set default agent:', error);
                // Fallback: just set the agent without backend call
                setCurrentAgent(defaultAgent);
              }
            }, 100);
          }
        } catch (error) {
          console.error('Failed to start session:', error);
        } finally {
          setIsInitialLoading(false);
        }
      }
    };
    initializeSession();
  }, [aiService, sessionStatus, startSession, handleAgentSelect]);

  // No need for separate sync, handled in initialization

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
  }, [aiService, sessionStatus, addSystemMessage, agents]);

  // Send message handler
  const handleSendMessage = useCallback(async (text: string) => {
    console.log('[App] handleSendMessage called:', { text });
    if (!aiService || sessionStatus !== SessionStatus.Active) {
      console.log('[App] Cannot send message - aiService or session not ready');
      return;
    }
    
    // console.log('[App] Adding user message and processing...');
    addUserMessage(text);
    
    // Handle commands
    if (text.trim().startsWith('/')) {
      try {
        startAIMessage();
        const result = await aiService.dispatchCommand(text.trim());
        if (result.error) {
          appendAIChunk({ 
            content: `ERROR: ${result.error}`, 
            index: 0, 
            isFinal: true 
          });
        } else {
          const output = typeof result.output === 'string' 
            ? result.output 
            : JSON.stringify(result.output, null, 2);
          appendAIChunk({ 
            content: output || JSON.stringify(result), 
            index: 0, 
            isFinal: true 
          });
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

  // AI message handling now done via channels

  // Update message agent metadata when current agent is set
  useEffect(() => {
    if (currentAgent && messages.length > 0 && lastUpdatedAgentRef.current !== currentAgent.id) {
      // Find recent AI messages without agent metadata and update them
      // This handles the case where agent introduction arrives before agent data is loaded
      const recentMessages = messages.slice(-3); // Check last 3 messages only
      const updatedAnyMessage = recentMessages.some(msg => {
        if (msg.sender === 'ai' && !msg.metadata?.agent) {
          console.log(`[App] Updating message ${msg.id} with agent metadata for ${currentAgent.name}`);
          updateMessageAgent(msg.id, currentAgent);
          return true;
        }
        return false;
      });
      
      if (updatedAnyMessage || recentMessages.length === 0) {
        lastUpdatedAgentRef.current = currentAgent.id;
      }
    }
  }, [currentAgent, messages, updateMessageAgent]);

  // Set agent change handler
  useEffect(() => {
    if (!aiService) return;
    
    const unsubscribe = aiService.onAgentChanged(async (agentId) => {
      console.log('[App] Agent changed notification received:', agentId);
      const agent = agents.find(a => a.id.toLowerCase() === agentId.toLowerCase());
      if (agent) {
        setCurrentAgent(agent);
        
        // Request introduction from the agent first
        try {
          await aiService.sendUserMessage("Please introduce yourself briefly.");
          // Add system message after AI responds
          setTimeout(() => {
            addSystemMessage(`✓ Switched to ${agent.name}`);
          }, 500);
        } catch (error) {
          console.error('Failed to request agent introduction:', error);
          addSystemMessage(`Switched to ${agent.name}`);
        }
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

  // Memoize chatProps to prevent infinite re-renders
  const chatProps = useMemo(() => ({
    messages,
    currentAgent,
    agents,
    onSendMessage: handleSendMessage,
    onAgentSelect: handleAgentSelect,
    onHandoffToAgent: handleHandoffToAgent,
    sessionStatus,
    wsStatus,
    sessionError: sessionError || undefined,
    onThemeToggle: toggleTheme,
    theme,
    jsonRpcService,
    aiService,
    currentAIMessage,
    loading,
  }), [
    messages, currentAgent, agents, handleSendMessage, handleAgentSelect, 
    handleHandoffToAgent, sessionStatus, wsStatus, sessionError, toggleTheme, 
    theme, jsonRpcService, aiService, currentAIMessage, loading
  ]);

  // Memoize fileBrowserProps to prevent re-renders
  const fileBrowserProps = useMemo(() => ({
    jsonRpcService,
    onFileSelect: (filePath: string) => {
      console.log('File selected:', filePath);
      // TODO: Handle file selection - could add to chat context
    },
  }), [jsonRpcService]);

  // Add debugging for initial render
  console.log('[App] Rendering with:', {
    agents: agents.length,
    currentAgent: currentAgent?.name,
    sessionStatus,
    wsStatus,
    messages: messages.length,
    isInitialLoading
  });

  return (
    <div className={`theme-${theme}`}>
      
      <Router>
        <ProjectProvider>
          <ProjectIntegration jsonRpcService={jsonRpcService} />
          <ViewProvider>
            <MainLayout 
              theme={theme} 
              isLoading={isInitialLoading}
              currentAgent={agentContext}
              onThemeToggle={toggleTheme}
              connectionStatus={wsStatus}
              onOpenFilesTab={tabHandlers.openFilesTab}
              onOpenSettingsTab={tabHandlers.openSettingsTab}
            >
              {/* Main tabbed area */}
              <MainTabs
                chatProps={chatProps}
                fileBrowserProps={fileBrowserProps}
                // Add other props as needed for JSONPlanView, CodeChangesView, etc.
                onTabsReady={setTabHandlers}
              />
            </MainLayout>
          </ViewProvider>
        </ProjectProvider>
      </Router>
    </div>
  );
}

export default App;