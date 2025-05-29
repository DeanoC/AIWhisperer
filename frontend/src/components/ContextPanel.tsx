import React, { useState, useEffect, useCallback, useRef } from 'react';
import AgentInspectorPanel from './AgentInspectorPanel';
import { PlanPreview } from './PlanPreview';
import { AgentAvatar } from './AgentAvatar';
import './ContextPanel.css';

interface AgentContext {
  files: string[];
  variables: Record<string, any>;
  history: string[];
}

interface Agent {
  id: string;
  name: string;
  role: string;
  color: string;
  icon?: string;
  status?: 'online' | 'busy' | 'offline';
  context: AgentContext;
}

interface Plan {
  id: string;
  name: string;
  tasks: Array<{
    id: string;
    name: string;
    status: string;
  }>;
}

interface ContextPanelProps {
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
  disabled?: boolean;
  currentAgent: Agent | null;
  currentPlan: Plan | null;
  isLoading?: boolean;
  error?: string;
  onRefresh?: () => void;
  onRetry?: () => void;
}

type TabType = 'agent' | 'plan' | 'history';

export const ContextPanel: React.FC<ContextPanelProps> = ({
  collapsed,
  onCollapse,
  disabled = false,
  currentAgent,
  currentPlan,
  isLoading = false,
  error,
  onRefresh,
  onRetry
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('agent');
  const [historyFilter, setHistoryFilter] = useState('');
  const [announcement, setAnnouncement] = useState('');
  const [newHistoryCount, setNewHistoryCount] = useState(0);
  const previousHistoryLength = useRef(currentAgent?.context.history.length || 0);
  const tabListRef = useRef<HTMLDivElement>(null);

  // Track new history items
  useEffect(() => {
    const currentLength = currentAgent?.context.history.length || 0;
    if (currentLength > previousHistoryLength.current) {
      setNewHistoryCount(currentLength - previousHistoryLength.current);
    }
    previousHistoryLength.current = currentLength;
  }, [currentAgent?.context.history]);

  // Clear notification when viewing history
  useEffect(() => {
    if (activeTab === 'history') {
      setNewHistoryCount(0);
    }
  }, [activeTab]);

  // Handle keyboard navigation for tabs
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!tabListRef.current || disabled) return;

      const tabs = tabListRef.current.querySelectorAll('[role="tab"]:not([aria-disabled="true"])');
      const currentIndex = Array.from(tabs).findIndex(tab => tab === document.activeElement);

      if (currentIndex === -1) return;

      let nextIndex = currentIndex;

      switch (e.key) {
        case 'ArrowRight':
          e.preventDefault();
          nextIndex = (currentIndex + 1) % tabs.length;
          break;
        case 'ArrowLeft':
          e.preventDefault();
          nextIndex = currentIndex === 0 ? tabs.length - 1 : currentIndex - 1;
          break;
      }

      if (nextIndex !== currentIndex) {
        (tabs[nextIndex] as HTMLElement).focus();
      }
    };

    tabListRef.current?.addEventListener('keydown', handleKeyDown);
    return () => tabListRef.current?.removeEventListener('keydown', handleKeyDown);
  }, [disabled]);

  // Handle tab change
  const handleTabChange = (tab: TabType) => {
    if (disabled) return;
    setActiveTab(tab);
    setAnnouncement(`Viewing ${tab.charAt(0).toUpperCase() + tab.slice(1)} context`);
  };

  // Export context data
  const handleExport = useCallback(() => {
    const data = {
      agent: currentAgent,
      plan: currentPlan,
      timestamp: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `context-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [currentAgent, currentPlan]);

  // Manage focus when collapsing
  useEffect(() => {
    if (collapsed && document.activeElement?.closest('.context-panel')) {
      const collapseButton = document.querySelector('.context-panel .collapse-button') as HTMLElement;
      collapseButton?.focus();
    }
  }, [collapsed]);

  // Calculate plan progress
  const planProgress = currentPlan ? {
    completed: currentPlan.tasks.filter(t => t.status === 'completed').length,
    total: currentPlan.tasks.length
  } : { completed: 0, total: 0 };

  // Filter history
  const filteredHistory = currentAgent?.context.history.filter(item =>
    !historyFilter || item.toLowerCase().includes(historyFilter.toLowerCase())
  ) || [];

  if (collapsed) {
    return (
      <div className="context-panel collapsed" data-testid="context-panel">
        <button
          className="collapse-button"
          onClick={() => onCollapse(false)}
          aria-label="Expand panel"
          disabled={disabled}
        >
          ←
        </button>
        
        <div className="collapsed-indicators" data-testid="collapsed-indicators">
          {currentAgent && (
            <div 
              className="agent-indicator"
              data-testid="agent-status-indicator"
              title={`${currentAgent.name} (${currentAgent.status})`}
            >
              <AgentAvatar 
                agent={currentAgent} 
                size="small" 
                showStatus={true}
                preferIcon={true}
              />
            </div>
          )}
          
          {currentPlan && (
            <div 
              className="plan-indicator"
              data-testid="plan-progress-indicator"
              title={`Plan: ${planProgress.completed}/${planProgress.total} tasks`}
            >
              {planProgress.completed}/{planProgress.total}
            </div>
          )}
          
          {newHistoryCount > 0 && (
            <div className="history-indicator" title={`${newHistoryCount} new actions`}>
              {newHistoryCount}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div 
      className="context-panel" 
      data-testid="context-panel"
      role="complementary"
      aria-label="Context panel"
    >
      {/* Header */}
      <div className="panel-header">
        <h2>Context</h2>
        <div className="header-actions">
          <button
            onClick={onRefresh}
            disabled={disabled || isLoading}
            aria-label="Refresh context"
            title="Refresh context"
          >
            🔄
          </button>
          <button
            onClick={handleExport}
            disabled={disabled}
            aria-label="Export context"
            title="Export context"
          >
            📥
          </button>
          <button
            className="collapse-button"
            onClick={() => onCollapse(true)}
            aria-label="Collapse panel"
            disabled={disabled}
          >
            →
          </button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="loading-state">
          <div className="spinner" data-testid="loading-spinner" />
          <p>Loading context...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="error-state">
          <p>{error}</p>
          {onRetry && (
            <button onClick={onRetry} disabled={disabled}>
              Retry
            </button>
          )}
        </div>
      )}

      {/* Tabs */}
      {!isLoading && !error && (
        <>
          <div 
            ref={tabListRef}
            className="panel-tabs"
            role="tablist"
            aria-label="Context views"
          >
            <button
              role="tab"
              aria-selected={activeTab === 'agent'}
              aria-controls="agent-panel"
              aria-disabled={disabled}
              className={activeTab === 'agent' ? 'active' : ''}
              onClick={() => handleTabChange('agent')}
            >
              Agent
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'plan'}
              aria-controls="plan-panel"
              aria-disabled={disabled}
              className={activeTab === 'plan' ? 'active' : ''}
              onClick={() => handleTabChange('plan')}
            >
              Plan
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'history'}
              aria-controls="history-panel"
              aria-disabled={disabled}
              className={`${activeTab === 'history' ? 'active' : ''} ${newHistoryCount > 0 ? 'has-notification' : ''}`}
              onClick={() => handleTabChange('history')}
            >
              History
              {newHistoryCount > 0 && (
                <span className="notification-badge">{newHistoryCount}</span>
              )}
            </button>
          </div>

          {/* Tab Panels */}
          <div className="panel-content">
            {/* Agent Tab */}
            {activeTab === 'agent' && (
              <div 
                id="agent-panel"
                role="tabpanel"
                aria-labelledby="agent-tab"
              >
                {currentAgent ? (
                  <AgentInspectorPanel agents={[currentAgent]} />
                ) : (
                  <div className="empty-state">No agent selected</div>
                )}
              </div>
            )}

            {/* Plan Tab */}
            {activeTab === 'plan' && (
              <div 
                id="plan-panel"
                role="tabpanel"
                aria-labelledby="plan-tab"
              >
                {currentPlan ? (
                  <PlanPreview plan={{
                    tasks: currentPlan.tasks.map(task => ({
                      description: task.name,
                      status: task.status
                    })),
                    format: 'json'
                  }} />
                ) : (
                  <div className="empty-state">No active plan</div>
                )}
              </div>
            )}

            {/* History Tab */}
            {activeTab === 'history' && (
              <div 
                id="history-panel"
                role="tabpanel"
                aria-labelledby="history-tab"
              >
                {currentAgent && currentAgent.context.history.length > 0 ? (
                  <>
                    <input
                      type="text"
                      placeholder="Filter history..."
                      value={historyFilter}
                      onChange={(e) => setHistoryFilter(e.target.value)}
                      disabled={disabled}
                      className="history-filter"
                    />
                    <ul className="history-list">
                      {filteredHistory.map((item, index) => (
                        <li key={index} className="history-item">
                          <span className="history-time">
                            {new Date().toLocaleTimeString()}
                          </span>
                          <span className="history-action">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </>
                ) : (
                  <div className="empty-state">No history available</div>
                )}
              </div>
            )}
          </div>
        </>
      )}

      {/* Status announcements */}
      <div role="status" className="sr-only" aria-live="polite">
        {announcement}
      </div>
    </div>
  );
};