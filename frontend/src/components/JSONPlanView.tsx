import React, { useState, useEffect, useCallback, useRef } from 'react';
import Editor from '@monaco-editor/react';
import './JSONPlanView.css';

// Add type for plan summary
interface PlanSummary {
  plan_name: string;
  _plan_name?: string;
  _status_dir?: string;
  name?: string;
  created_at?: string;
  updated_at?: string;
}

interface JSONPlanViewProps {
  jsonRpcService?: any;
}


interface Task {
  id: string;
  name: string;
  description?: string;
  status: string;
  subtasks?: Task[];
}

interface PlanData {
  id: string;
  name: string;
  version: number;
  tasks: Task[];
  metadata?: any;
}



interface TreeNodeProps {
  node: Task;
  level: number;
  expanded: boolean;
  focused: boolean;
  onToggle: () => void;
  onSelect: () => void;
  onFocus: () => void;
  searchTerm: string;
}


const TreeNode: React.FC<TreeNodeProps> = ({ 
  node, 
  level, 
  expanded, 
  focused,
  onToggle, 
  onSelect,
  onFocus,
  searchTerm
}) => {
  const hasChildren = node.subtasks && node.subtasks.length > 0;
  const isVisible = !searchTerm || 
    node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    node.description?.toLowerCase().includes(searchTerm.toLowerCase());

  if (!isVisible && !hasChildren) return null;

  return (
    <div className={`tree-node ${focused ? 'focused' : ''}`}>
      <div 
        className={`tree-node-content status-${node.status}`}
        data-testid={`tree-node-${node.id}`}
        style={{ paddingLeft: `${level * 20}px` }}
        onClick={onSelect}
        onFocus={onFocus}
        tabIndex={0}
      >
        {hasChildren && (
          <button
            className="expand-button"
            data-testid={`expand-${node.id}`}
            onClick={(e) => {
              e.stopPropagation();
              onToggle();
            }}
          >
            {expanded ? '▼' : '▶'}
          </button>
        )}
        <span className="node-name">{node.name}</span>
        <span className={`status-indicator status-${node.status}`} />
      </div>
      {expanded && hasChildren && (
        <div className="tree-children">
          {node.subtasks!.map((subtask) => (
            <TreeNode
              key={subtask.id}
              node={subtask}
              level={level + 1}
              expanded={false}
              focused={false}
              onToggle={() => {}}
              onSelect={() => {}}
              onFocus={() => {}}
              searchTerm={searchTerm}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const JSONPlanView: React.FC<JSONPlanViewProps> = (props) => {
  const [planList, setPlanList] = useState<PlanSummary[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [planData, setPlanData] = useState<PlanData | null>(null);
  const [loadingPlans, setLoadingPlans] = useState(false);
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editorValue, setEditorValue] = useState('');
  const [showTree, setShowTree] = useState(true);
  const [showEditor, setShowEditor] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchMatches, setSearchMatches] = useState(0);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [focusedNode, setFocusedNode] = useState<string | null>(null);
  const treeRef = useRef<HTMLDivElement>(null);

  // Fetch plan list on mount
  useEffect(() => {
    setLoadingPlans(true);
    setError(null);
    const rpc = props.jsonRpcService || (window as any).jsonRpcService;
    if (rpc) {
      rpc.sendRequest('plan.list', {})
        .then((res: any) => {
          setPlanList(res.plans || []);
        })
        .catch(() => setError('Failed to load plan list'))
        .finally(() => setLoadingPlans(false));
    } else {
      setError('No JSON-RPC service available');
      setLoadingPlans(false);
    }
  }, [props.jsonRpcService]);

  // Fetch plan data when selectedPlan changes
  useEffect(() => {
    if (selectedPlan && (props.jsonRpcService || (window as any).jsonRpcService)) {
      setLoadingPlan(true);
      setError(null);
      const rpc = props.jsonRpcService || (window as any).jsonRpcService;
      rpc.sendRequest('plan.read', { plan_name: selectedPlan })
        .then((res: any) => {
          setPlanData(res.plan || null);
          setEditorValue(res.plan ? JSON.stringify(res.plan, null, 2) : '');
        })
        .catch(() => setError('Failed to load plan'))
        .finally(() => setLoadingPlan(false));
    }
  }, [selectedPlan, props.jsonRpcService]);

  // Validate plan structure
  const isValidPlanStructure = (obj: any): obj is PlanData => {
    return obj && 
      typeof obj === 'object' && 
      'tasks' in obj && 
      Array.isArray(obj.tasks);
  };

  // Handle editor changes
  const handleEditorChange = useCallback((value: string | undefined) => {
    if (!value) return;
    setEditorValue(value);
    setError(null);
    try {
      const parsed = JSON.parse(value);
      if (!isValidPlanStructure(parsed)) {
        setError('Invalid plan structure');
      }
    } catch (e) {
      setError('Invalid JSON');
    }
  }, []);

  // Handle tree node selection
  const handleNodeSelect = useCallback((nodeId: string) => {
    // Find node in planData and update editor
    const findNode = (tasks: Task[]): Task | null => {
      for (const task of tasks) {
        if (task.id === nodeId) return task;
        if (task.subtasks) {
          const found = findNode(task.subtasks);
          if (found) return found;
        }
      }
      return null;
    };
    if (planData && isValidPlanStructure(planData)) {
      const node = findNode(planData.tasks);
      if (node) {
        setEditorValue(JSON.stringify(node, null, 2));
      }
    }
  }, [planData]);

  // Handle tree expansion
  const toggleNode = useCallback((nodeId: string) => {
    setExpandedNodes(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }, []);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!treeRef.current || !treeRef.current.contains(document.activeElement)) return;
      // Implement keyboard navigation logic here
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter') {
        e.preventDefault();
        // Navigation logic would go here
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Handle search
  useEffect(() => {
    if (!searchTerm || !editorValue) {
      setSearchMatches(0);
      return;
    }
    const matches = (editorValue.match(new RegExp(searchTerm, 'gi')) || []).length;
    setSearchMatches(matches);
  }, [searchTerm, editorValue]);

  // Format JSON
  const handleFormat = useCallback(() => {
    try {
      const parsed = JSON.parse(editorValue);
      setEditorValue(JSON.stringify(parsed, null, 2));
      setError(null);
    } catch (e) {
      setError('Cannot format invalid JSON');
    }
  }, [editorValue]);

  // Export JSON
  const handleExport = useCallback(() => {
    const blob = new Blob([editorValue], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `plan-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [editorValue]);

  // Plan selection UI
  if (!planList.length && loadingPlans) {
    return <div className="json-plan-view empty"><p>Loading plans...</p></div>;
  }
  if (!planList.length) {
    return <div className="json-plan-view empty"><p>No plans found.</p></div>;
  }
  if (!selectedPlan) {
    return (
      <div className="json-plan-view empty">
        <h3>Select a plan to view</h3>
        <ul>
          {planList.map(plan => (
            <li key={plan.plan_name || plan._plan_name}>
              <button onClick={() => setSelectedPlan(plan.plan_name || plan._plan_name || '')}>
                {plan.name || plan.plan_name || plan._plan_name}
                {plan._status_dir ? ` (${plan._status_dir})` : ''}
              </button>
            </li>
          ))}
        </ul>
      </div>
    );
  }
  if (loadingPlan) {
    return <div className="json-plan-view empty"><p>Loading plan...</p></div>;
  }
  if (!planData) {
    return <div className="json-plan-view empty"><p>No plan data available</p></div>;
  }
  if (!isValidPlanStructure(planData)) {
    return <div className="json-plan-view error"><p>Invalid plan structure</p></div>;
  }
  return (
    <div className="json-plan-view supports-high-contrast" data-testid="json-plan-view">
      <div className="json-view-header">
        <div className="search-container">
          <input
            type="text"
            placeholder="Search JSON..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Escape') {
                setSearchTerm('');
              }
            }}
          />
          {searchMatches > 0 && (
            <span className="search-results">
              Found {searchMatches} matches
            </span>
          )}
        </div>
        <div className="view-controls">
          <button onClick={() => setShowTree(!showTree)}>
            {showTree ? 'Hide Tree' : 'Show Tree'}
          </button>
          <button onClick={() => setShowEditor(!showEditor)}>
            {showEditor ? 'Hide Editor' : 'Show Editor'}
          </button>
          <button onClick={handleFormat}>Format</button>
          <button onClick={handleExport}>Export JSON</button>
        </div>
      </div>
      <div className="json-view-content">
        {showTree && (
          <div className="json-tree" data-testid="json-tree">
            <div 
              ref={treeRef}
              role="tree"
              aria-label="Plan structure"
              className="tree-container"
            >
              <h3>{planData.name}</h3>
              {planData.tasks.map((task) => (
                <TreeNode
                  key={task.id}
                  node={task}
                  level={0}
                  expanded={expandedNodes.has(task.id)}
                  focused={focusedNode === task.id}
                  onToggle={() => toggleNode(task.id)}
                  onSelect={() => handleNodeSelect(task.id)}
                  onFocus={() => setFocusedNode(task.id)}
                  searchTerm={searchTerm}
                />
              ))}
            </div>
          </div>
        )}
        {showEditor && (
          <div className="json-editor">
            {error && (
              <div className="editor-error">
                {error}
              </div>
            )}
            <Editor
              value={editorValue}
              language="json"
              theme="vs-dark"
              onChange={handleEditorChange}
              options={{
                minimap: { enabled: false },
                formatOnPaste: true,
                formatOnType: true,
                automaticLayout: true,
                'aria-label': 'JSON editor'
              }}
              data-testid="monaco-editor"
              data-language="json"
            />
          </div>
        )}
      </div>
      <div role="status" className="sr-only" aria-live="polite">
        {searchMatches > 0 && `Found ${searchMatches} matches`}
      </div>
      {searchTerm && searchMatches > 0 && (
        <div data-testid="search-highlight" className="hidden" />
      )}
    </div>
  );

};

export default JSONPlanView;