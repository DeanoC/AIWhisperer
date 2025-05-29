import React, { useState, useEffect, useRef } from 'react';
import { Agent } from '../types/agent';
import { AIService } from '../services/aiService';
import { AgentAvatar } from './AgentAvatar';
import './AgentSidebar.css';

export interface AgentSidebarProps {
  aiService: AIService | undefined;
  onAgentSelect: (agentId: string) => void;
  disabled?: boolean;
}

export const AgentSidebar: React.FC<AgentSidebarProps> = ({
  aiService,
  onAgentSelect,
  disabled = false
}) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [currentAgentId, setCurrentAgentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredAgent, setHoveredAgent] = useState<string | null>(null);
  const [focusedIndex, setFocusedIndex] = useState(0);
  const sidebarRef = useRef<HTMLDivElement>(null);
  const agentRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Fetch agents from API
  useEffect(() => {
    if (!aiService) {
      setLoading(false);
      return;
    }

    const fetchAgents = async () => {
      try {
        setLoading(true);
        setError(null);
        const [agentList, currentAgent] = await Promise.all([
          aiService.listAgents(),
          aiService.getCurrentAgent().catch(() => null)
        ]);
        setAgents(agentList);
        setCurrentAgentId(currentAgent);
      } catch (err) {
        console.error('Failed to fetch agents:', err);
        setError('Failed to load agents');
      } finally {
        setLoading(false);
      }
    };

    fetchAgents();
  }, [aiService]);

  // Handle agent selection
  const handleAgentClick = async (agentId: string) => {
    if (disabled || agentId === currentAgentId) return;

    try {
      await aiService?.switchAgent(agentId);
      setCurrentAgentId(agentId);
      onAgentSelect(agentId);
    } catch (err) {
      console.error('Failed to switch agent:', err);
    }
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled || agents.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        const nextIndex = Math.min(focusedIndex + 1, agents.length - 1);
        setFocusedIndex(nextIndex);
        agentRefs.current[nextIndex]?.focus();
        break;
      
      case 'ArrowUp':
        e.preventDefault();
        const prevIndex = Math.max(focusedIndex - 1, 0);
        setFocusedIndex(prevIndex);
        agentRefs.current[prevIndex]?.focus();
        break;
      
      case 'Enter':
        e.preventDefault();
        if (agents[focusedIndex]) {
          handleAgentClick(agents[focusedIndex].id);
        }
        break;
    }
  };

  if (loading) {
    return (
      <div className="agent-sidebar" data-testid="agent-sidebar-loading">
        <div className="loading-spinner">Loading agents...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="agent-sidebar">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  return (
    <div 
      className="agent-sidebar"
      data-testid="agent-sidebar"
      ref={sidebarRef}
      tabIndex={0}
      onKeyDown={handleKeyDown}
    >
      <h3 className="sidebar-title">Agents</h3>
      <div className="agent-list">
        {agents.map((agent, index) => (
          <div
            key={agent.id}
            ref={(el: HTMLDivElement | null) => { agentRefs.current[index] = el; }}
            className={`agent-card ${currentAgentId === agent.id ? 'active' : ''} ${disabled ? 'disabled' : ''}`}
            data-testid={`agent-card-${agent.id}`}
            onClick={() => handleAgentClick(agent.id)}
            onMouseEnter={() => setHoveredAgent(agent.id)}
            onMouseLeave={() => setHoveredAgent(null)}
            tabIndex={-1}
            style={{ borderLeft: `4px solid ${agent.color}` }}
          >
            <div className="agent-card-header">
              <AgentAvatar agent={agent} size={40} />
              <div className="agent-info">
                <div className="agent-name">{agent.name}</div>
                <div className="agent-role">{agent.role}</div>
              </div>
              <div 
                className={`agent-status status-${agent.status || 'online'}`}
                data-testid={`agent-status-${agent.id}`}
              />
            </div>
            <div 
              className={`agent-description ${hoveredAgent === agent.id ? 'visible' : ''}`}
              style={{ visibility: hoveredAgent === agent.id ? 'visible' : 'hidden' }}
            >
              {agent.description}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};