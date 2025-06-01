# Technical Specifications for UI Improvements

## TASK 1: Chat UI Message Box Enhancement

### Current Implementation Analysis
```typescript
// Current in MessageInput.tsx (line ~47)
<input
  type="text"
  value={input}
  onChange={(e) => setInput(e.target.value)}
  onKeyDown={handleKeyDown}
  placeholder="Type your message..."
  className="flex-1 px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
/>
```

### Proposed Implementation
```typescript
// Replace with textarea
<textarea
  value={input}
  onChange={(e) => setInput(e.target.value)}
  onKeyDown={handleKeyDown}
  placeholder="Type your message... (Shift+Enter for new line, Enter to send)"
  className="flex-1 px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none resize-none"
  rows={1}
  style={{
    minHeight: '2.5rem',
    maxHeight: '8rem',
    overflowY: 'auto'
  }}
  ref={textareaRef}
/>
```

### Key Changes Required:
1. **Auto-resize textarea**: Implement auto-height adjustment
2. **Enter key handling**: Shift+Enter for new line, Enter to send
3. **Preserve existing features**: @ symbol file picker, command suggestions
4. **Styling adjustments**: Maintain current design while supporting multi-line

### Implementation Details:
```typescript
// Add to MessageInput component
const textareaRef = useRef<HTMLTextAreaElement>(null);

// Auto-resize function
const adjustTextareaHeight = () => {
  const textarea = textareaRef.current;
  if (textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 128) + 'px';
  }
};

// Modified handleKeyDown
const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
  // ... rest of existing logic
};

// Add to onChange
const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
  setInput(e.target.value);
  adjustTextareaHeight();
  // ... existing @ symbol logic
};
```

---

## TASK 2: Plan Viewer Integration

### Backend API Endpoints Needed

#### 1. List Plans Endpoint
```typescript
// JSON-RPC method: list_plans
interface ListPlansRequest {
  workspace_path?: string;
  include_archived?: boolean;
}

interface ListPlansResponse {
  plans: {
    id: string;
    name: string;
    status: 'in_progress' | 'archived';
    created_at: string;
    modified_at: string;
    file_path: string;
  }[];
}
```

#### 2. Get Plan Content Endpoint
```typescript
// JSON-RPC method: get_plan
interface GetPlanRequest {
  plan_id: string;
  workspace_path?: string;
}

interface GetPlanResponse {
  plan: {
    id: string;
    name: string;
    content: any; // JSON plan structure
    metadata: {
      created_at: string;
      modified_at: string;
      status: string;
    };
  };
}
```

### Frontend Integration
```typescript
// New hooks for plan data
const usePlans = (workspacePath?: string) => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPlans = useCallback(async () => {
    setLoading(true);
    try {
      const response = await sendJsonRpcRequest('list_plans', {
        workspace_path: workspacePath,
        include_archived: true
      });
      setPlans(response.plans);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [workspacePath]);

  return { plans, loading, error, refetch: fetchPlans };
};

const usePlan = (planId?: string) => {
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPlan = useCallback(async () => {
    if (!planId) return;
    
    setLoading(true);
    try {
      const response = await sendJsonRpcRequest('get_plan', { plan_id: planId });
      setPlan(response.plan);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [planId]);

  return { plan, loading, error, refetch: fetchPlan };
};
```

### JSONPlanView Component Updates
```typescript
// Replace placeholder data with real data
const JSONPlanView: React.FC = () => {
  const [selectedPlanId, setSelectedPlanId] = useState<string>();
  const { plans, loading: plansLoading } = usePlans();
  const { plan, loading: planLoading } = usePlan(selectedPlanId);

  // Plan list in sidebar
  const renderPlansList = () => (
    <div className="plan-list">
      {plans.map(plan => (
        <div
          key={plan.id}
          className={`plan-item ${selectedPlanId === plan.id ? 'selected' : ''}`}
          onClick={() => setSelectedPlanId(plan.id)}
        >
          <span className="plan-name">{plan.name}</span>
          <span className={`plan-status ${plan.status}`}>{plan.status}</span>
        </div>
      ))}
    </div>
  );

  // Monaco editor with real content
  return (
    <div className="json-plan-view">
      <div className="plans-sidebar">
        {plansLoading ? <LoadingSpinner /> : renderPlansList()}
      </div>
      <div className="plan-content">
        {planLoading ? (
          <LoadingSpinner />
        ) : plan ? (
          <MonacoEditor
            value={JSON.stringify(plan.content, null, 2)}
            language="json"
            theme="vs-dark"
            options={{ readOnly: true }}
          />
        ) : (
          <div className="no-plan-selected">Select a plan to view</div>
        )}
      </div>
    </div>
  );
};
```

---

## TASK 3: Browse Button Implementation

### Directory Browser Component
```typescript
interface DirectoryBrowserProps {
  onSelect: (path: string) => void;
  onCancel: () => void;
  initialPath?: string;
}

const DirectoryBrowser: React.FC<DirectoryBrowserProps> = ({ onSelect, onCancel, initialPath }) => {
  const [currentPath, setCurrentPath] = useState(initialPath || '/');
  const [directories, setDirectories] = useState<DirectoryItem[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchDirectories = async (path: string) => {
    setLoading(true);
    try {
      const response = await sendJsonRpcRequest('list_directories', { path });
      setDirectories(response.directories);
    } catch (error) {
      console.error('Failed to fetch directories:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="directory-browser-modal">
      <div className="browser-header">
        <h3>Select Project Directory</h3>
        <div className="current-path">{currentPath}</div>
      </div>
      <div className="directory-list">
        {/* Parent directory */}
        {currentPath !== '/' && (
          <div 
            className="directory-item parent"
            onClick={() => {
              const parentPath = path.dirname(currentPath);
              setCurrentPath(parentPath);
              fetchDirectories(parentPath);
            }}
          >
            📁 ..
          </div>
        )}
        
        {/* Directory listing */}
        {directories.map(dir => (
          <div
            key={dir.path}
            className="directory-item"
            onClick={() => {
              if (dir.type === 'directory') {
                setCurrentPath(dir.path);
                fetchDirectories(dir.path);
              }
            }}
          >
            {dir.type === 'directory' ? '📁' : '📄'} {dir.name}
          </div>
        ))}
      </div>
      <div className="browser-actions">
        <button onClick={onCancel}>Cancel</button>
        <button onClick={() => onSelect(currentPath)}>Select Current Directory</button>
      </div>
    </div>
  );
};
```

### Backend Directory Listing Handler
```python
# In interactive_server/handlers/workspace_handler.py

async def handle_list_directories(self, request: Dict[str, Any]) -> Dict[str, Any]:
    """List directories and files in a given path"""
    try:
        path = request.get('path', '/')
        
        # Security check - prevent path traversal attacks
        if not self._is_safe_path(path):
            raise ValueError("Invalid path")
            
        directories = []
        
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                directories.append({
                    'name': item,
                    'path': item_path,
                    'type': 'directory'
                })
            elif os.path.isfile(item_path):
                directories.append({
                    'name': item,
                    'path': item_path,
                    'type': 'file'
                })
        
        # Sort directories first, then files
        directories.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
        
        return {
            'directories': directories,
            'current_path': path
        }
        
    except Exception as e:
        raise JsonRpcError(-32603, f"Failed to list directories: {str(e)}")

def _is_safe_path(self, path: str) -> bool:
    """Check if path is safe to access"""
    # Normalize path and check for traversal attempts
    normalized = os.path.normpath(path)
    return not normalized.startswith('..') and os.path.exists(normalized)
```

---

## TASK 4: Terminal Implementation

### Frontend Terminal Component
```typescript
// Terminal.tsx
import { Terminal as XTerm } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebglAddon } from 'xterm-addon-webgl';

interface TerminalProps {
  sessionId?: string;
}

const Terminal: React.FC<TerminalProps> = ({ sessionId }) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm>();
  const wsRef = useRef<WebSocket>();
  const fitAddonRef = useRef<FitAddon>();

  useEffect(() => {
    if (!terminalRef.current) return;

    // Initialize xterm.js
    const xterm = new XTerm({
      theme: {
        background: '#1a1a1a',
        foreground: '#ffffff',
        cursor: '#ffffff'
      },
      fontSize: 14,
      fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
      cursorBlink: true
    });

    const fitAddon = new FitAddon();
    xterm.loadAddon(fitAddon);
    xterm.loadAddon(new WebglAddon());

    xterm.open(terminalRef.current);
    fitAddon.fit();

    xtermRef.current = xterm;
    fitAddonRef.current = fitAddon;

    // WebSocket connection
    const ws = new WebSocket(`ws://localhost:8000/terminal/${sessionId || 'default'}`);
    wsRef.current = ws;

    ws.onopen = () => {
      xterm.write('Terminal connected\r\n');
    };

    ws.onmessage = (event) => {
      xterm.write(event.data);
    };

    ws.onclose = () => {
      xterm.write('\r\nTerminal disconnected');
    };

    // Send input to backend
    xterm.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'input',
          data: data
        }));
      }
    });

    // Cleanup
    return () => {
      ws.close();
      xterm.dispose();
    };
  }, [sessionId]);

  // Handle resize
  useEffect(() => {
    const handleResize = () => {
      if (fitAddonRef.current) {
        fitAddonRef.current.fit();
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className="terminal-container">
      <div className="terminal-header">
        <span>Terminal {sessionId}</span>
        <button onClick={() => {
          // Clear terminal
          xtermRef.current?.clear();
        }}>Clear</button>
      </div>
      <div ref={terminalRef} className="terminal-content" />
    </div>
  );
};
```

### Backend Terminal Handler
```python
# interactive_server/handlers/terminal_handler.py
import asyncio
import os
import pty
import subprocess
from typing import Dict, Any
import websockets

class TerminalHandler:
    def __init__(self):
        self.sessions: Dict[str, TerminalSession] = {}
    
    async def handle_websocket(self, websocket, session_id: str):
        """Handle WebSocket connection for terminal session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = TerminalSession()
        
        session = self.sessions[session_id]
        
        try:
            await session.connect(websocket)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            if session_id in self.sessions:
                await session.cleanup()
                del self.sessions[session_id]

class TerminalSession:
    def __init__(self):
        self.process = None
        self.master_fd = None
        
    async def connect(self, websocket):
        """Start bash process and handle I/O"""
        # Create pseudo-terminal
        self.master_fd, slave_fd = pty.openpty()
        
        # Start bash process
        self.process = subprocess.Popen(
            ['/bin/bash'],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            preexec_fn=os.setsid
        )
        
        os.close(slave_fd)
        
        # Handle process output
        async def read_output():
            while self.process.poll() is None:
                try:
                    data = os.read(self.master_fd, 1024)
                    if data:
                        await websocket.send(data.decode('utf-8', errors='ignore'))
                except OSError:
                    break
        
        # Start output reader
        output_task = asyncio.create_task(read_output())
        
        try:
            # Handle input from WebSocket
            async for message in websocket:
                data = json.loads(message)
                if data.get('type') == 'input':
                    input_data = data.get('data', '')
                    os.write(self.master_fd, input_data.encode('utf-8'))
        finally:
            output_task.cancel()
    
    async def cleanup(self):
        """Clean up terminal session"""
        if self.process:
            self.process.terminate()
            self.process.wait()
        if self.master_fd:
            os.close(self.master_fd)
```

### WebSocket Route Setup
```python
# In main server setup
from websockets.server import serve

async def terminal_websocket_handler(websocket, path):
    session_id = path.split('/')[-1]
    terminal_handler = TerminalHandler()
    await terminal_handler.handle_websocket(websocket, session_id)

# Start WebSocket server
websocket_server = serve(terminal_websocket_handler, "localhost", 8001)
```

---

## Package Dependencies

### Frontend (package.json additions)
```json
{
  "dependencies": {
    "xterm": "^5.3.0",
    "xterm-addon-fit": "^0.8.0",
    "xterm-addon-webgl": "^0.16.0",
    "react-textarea-autosize": "^8.5.3"
  }
}
```

### Backend (requirements.txt additions)
```
websockets>=11.0.3
```

This completes the technical specifications for all four UI improvement tasks.
