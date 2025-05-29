# Project Management System Architecture

## Overview
The project management system allows users to connect AIWhisperer to existing code workspaces. Each workspace gets a dedicated `.WHISPER` folder for storing AIWhisperer-specific data, plans, agent context, and development artifacts. AIWhisperer operates within the existing codebase to help develop features.

## Data Model

### Project
```typescript
interface Project {
  id: string;                    // UUID
  name: string;                  // Display name
  path: string;                  // Absolute path to project directory
  whisperPath: string;           // Path to .WHISPER folder
  createdAt: Date;
  lastAccessedAt: Date;
  description?: string;
  settings?: ProjectSettings;
}

interface ProjectSettings {
  defaultAgent?: string;         // Default agent for the project
  autoSave?: boolean;           // Auto-save conversations
  // Future settings...
}
```

### Project History
```typescript
interface ProjectHistory {
  recentProjects: ProjectSummary[];
  lastActiveProjectId?: string;
  maxRecentProjects: number;     // Default: 10
}

interface ProjectSummary {
  id: string;
  name: string;
  path: string;
  lastAccessedAt: Date;
}
```

## Directory Structure

When AIWhisperer is connected to an existing codebase, it creates a `.WHISPER` folder in the workspace root:

```
/existing/code/workspace/
├── src/                        # Existing source code
├── tests/                      # Existing tests
├── docs/                       # Existing documentation
├── package.json               # Existing project files
├── README.md                  # Existing README
└── .WHISPER/                  # AIWhisperer data (created)
    ├── project.json           # AIWhisperer project metadata
    ├── plans/                 # Feature development plans
    │   ├── initial/          # Initial feature plans
    │   └── refined/          # Refined/detailed plans
    ├── sessions/             # Development sessions
    │   └── {session-id}.json # Individual session data
    ├── agents/               # Agent-specific workspaces
    │   ├── alice/           # Alice's planning workspace
    │   ├── patricia/        # Patricia's validation workspace
    │   └── tessa/           # Tessa's testing workspace
    ├── features/            # Feature development tracking
    │   └── {feature-id}/    # Individual feature data
    └── artifacts/           # Generated code snippets
```

## Backend API

### Endpoints

#### Project Management
- `POST /api/projects/create` - Create new project
- `GET /api/projects` - List all projects
- `GET /api/projects/recent` - Get recent projects
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project
- `POST /api/projects/{id}/activate` - Set as active project

#### Project Settings
- `GET /api/settings/project-defaults` - Get default project settings
- `PUT /api/settings/project-defaults` - Update default settings
- `GET /api/settings/ui` - Get UI settings (auto-load, etc.)
- `PUT /api/settings/ui` - Update UI settings

### Request/Response Examples

#### Connect to Workspace
```json
// Request
POST /api/projects/connect
{
  "name": "My React App",
  "path": "/home/user/code/my-react-app",
  "description": "React application for task management"
}

// Response
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My React App",
  "path": "/home/user/code/my-react-app",
  "whisperPath": "/home/user/code/my-react-app/.WHISPER",
  "createdAt": "2025-05-29T10:00:00Z",
  "lastAccessedAt": "2025-05-29T10:00:00Z",
  "description": "React application for task management"
}
```

## Frontend Components

### Project Management UI

#### ProjectSelector Component
- Dropdown/modal for selecting active project
- Shows project name and path
- Quick access to recent projects
- "Create New Project" option

#### ConnectWorkspaceDialog
- Form for connecting to existing workspace
- Fields: Name, Path (with folder picker), Description
- Validation for path accessibility and existence
- Checks if workspace already has .WHISPER folder
- Creates .WHISPER folder on confirmation

#### ProjectSettings Component
- Project-specific settings
- Global default settings
- UI behavior settings (auto-load last project)

#### RecentProjectsList
- List of recently accessed projects
- Shows name, path, last accessed
- Quick activate/delete actions
- Search/filter capability

## Integration Points

### Session Management
- Sessions are now scoped to projects
- Session IDs include project context
- Agent state is project-specific

### Agent System
- Agents operate within project context
- Agent workspaces in .WHISPER/agents/
- Project-specific agent configurations

### File Operations
- All file operations scoped to project
- PathManager updated to respect project boundaries
- .WHISPER folder is managed by system

## Implementation Plan

1. **Backend Infrastructure**
   - Project model and database schema
   - CRUD operations for projects
   - Project activation/switching logic
   - .WHISPER folder management

2. **API Development**
   - RESTful endpoints for project operations
   - WebSocket notifications for project changes
   - Settings management endpoints

3. **Frontend Development**
   - Project selector in main UI
   - Create project dialog
   - Recent projects view
   - Settings management UI

4. **Integration**
   - Update session management for project scope
   - Modify agent system for project context
   - Update file operations for project boundaries

5. **Testing**
   - Unit tests for project operations
   - Integration tests for project switching
   - E2E tests for complete workflow

## Security Considerations

- Path validation to prevent directory traversal
- Permission checks for project directories
- Sanitization of project names
- Isolation between projects

## Future Enhancements

- Project templates
- Import/export projects
- Project sharing (read-only access)
- Project archiving
- Git integration for project versioning