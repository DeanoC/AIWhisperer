
import React, { useState, useEffect } from "react";
import { useAISession } from '../hooks/useAISession';
import { AIService } from '../services/aiService';

interface Agent {
  id: string;
  name: string;
}


interface AgentInspectorPanelProps {
  agents: Agent[];
  aiService?: AIService;
  sessionId?: string;
}


const AgentInspectorPanel: React.FC<AgentInspectorPanelProps> = ({ agents, aiService, sessionId }) => {
  const [visible, setVisible] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState(agents[0]?.id || "");
  const [infoType, setInfoType] = useState("context");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch context using aiService/JSON-RPC if available
  const fetchContext = async () => {
    if (!aiService || !sessionId || !selectedAgent) {
      setError("Inspector: Missing aiService, sessionId, or agent");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const cmdArgs = JSON.stringify({
        agent_id: selectedAgent,
        info_type: infoType,
        session_id: sessionId
      });
      const cmd = `/agent.inspect ${cmdArgs}`;
      const result = await aiService.dispatchCommand(cmd);
      setData(result.output || result);
    } catch (e) {
      setError("Failed to fetch agent context");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContext();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAgent, infoType]);

  if (!agents.length) {
    return <div>No agents available</div>;
  }

  return (
    <div className="agent-inspector-panel">
      <button onClick={() => setVisible(v => !v)}>{visible ? "Hide Inspector" : "Show Inspector"}</button>
      {visible && (
        <div>
          <h2>Inspector</h2>
          <label>
            Agent:
            <select value={selectedAgent} onChange={e => setSelectedAgent(e.target.value)}>
              {agents.map(agent => (
                <option key={agent.id} value={agent.id}>{agent.name}</option>
              ))}
            </select>
          </label>
          <label>
            Info Type:
            <select value={infoType} onChange={e => setInfoType(e.target.value)}>
              <option value="context">Context</option>
              {/* Future: <option value="state">State</option> */}
            </select>
          </label>
          <button
            onClick={() => {
              setData(null);
              fetchContext();
            }}
            disabled={loading}
          >
            Refresh
          </button>
          {loading && <div>Loading...</div>}
          {error && <div style={{ color: "red" }}>{error}</div>}
          {data && (
            <pre style={{ maxHeight: 300, overflow: "auto" }}>{typeof data === 'string' ? data : JSON.stringify(data, null, 2)}</pre>
          )}
        </div>
      )}
    </div>
  );
};

export default AgentInspectorPanel;
