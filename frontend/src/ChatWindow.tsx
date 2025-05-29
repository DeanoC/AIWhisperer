import React from 'react';
import './ChatWindow.css';
import { ChatMessage, MessageSender } from './types/chat';
import { Plan } from './types/plan';
import { Agent } from './types/agent';
import { PlanPreview } from './components/PlanPreview';
import { PlanConfirmation } from './components/PlanConfirmation';
import { PlanExport } from './components/PlanExport';

interface ChatWindowProps {
  messages: ChatMessage[];
  currentAgent?: Agent;
  onConfirmPlan?: () => void;
  onRejectPlan?: () => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ messages, currentAgent, onConfirmPlan, onRejectPlan }) => {
  return (
    <div className="chat-window">
      {currentAgent && (
        <div className="current-agent-banner" style={{ marginBottom: 12, padding: 8, background: currentAgent.color, color: '#fff', borderRadius: 6 }}>
          <b>Current Agent:</b> {currentAgent.name}
        </div>
      )}
      {messages.map((msg, idx) => {
        // Detect plan JSON in AI message content
        let plan: Plan | null = null;
        if (msg.sender === MessageSender.AI) {
          try {
            const parsed = JSON.parse(msg.content);
            if (parsed && parsed.tasks && parsed.format) {
              plan = parsed;
            }
          } catch (e) { /* not JSON, ignore */ }
        }
        return (
          <div
            key={msg.id || idx}
            className={`chat-message ${msg.sender === MessageSender.User ? 'user' : msg.sender === MessageSender.AI ? 'ai' : 'system'}`}
          >
            {msg.sender === MessageSender.System && msg.content.startsWith('ERROR:') ? (
              <span className="system-error">{msg.content.split('\n').map((line, i) => (
                <React.Fragment key={i}>
                  {line}
                  {i < msg.content.split('\n').length - 1 && <br />}
                </React.Fragment>
              ))}</span>
            ) : plan ? (
              <div>
                <PlanPreview plan={plan} />
                <PlanConfirmation onConfirm={onConfirmPlan || (() => {})} onReject={onRejectPlan || (() => {})} />
                <PlanExport plan={plan} />
              </div>
            ) : (
              msg.content.split('\n').map((line, i) => (
                <React.Fragment key={i}>
                  {line}
                  {i < msg.content.split('\n').length - 1 && <br />}
                </React.Fragment>
              ))
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ChatWindow;
