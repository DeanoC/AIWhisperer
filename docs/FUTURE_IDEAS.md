# Future Ideas and Improvements

This document tracks ideas, nice-to-have features, and improvements that we want to remember but don't need to implement immediately.

## File Browser & AI Tools Enhancements

### Caching Layer (from Phase 4)
- Implement caching for repeated operations
  - Cache directory listings with TTL
  - Cache file metadata (size, modified time)
  - Add intelligent cache invalidation based on file system events
  - Consider using LRU cache with size limits
  - Cache workspace statistics for performance

### Phase 5: File Browser UI Enhancements (from file_browser_implementation_plan.md)
- **Advanced File Filtering**
  - Add file type filter dropdown
  - Add date range filters
  - Add size filters
  - Save filter presets

- **File Preview**
  - Show file preview on hover
  - Syntax highlighting for code files
  - Image thumbnails
  - Markdown rendering

- **Multi-file Selection**
  - Checkbox selection mode
  - Select all/none buttons
  - Bulk operations

- **File Operations**
  - Create new file/folder
  - Rename files
  - Delete files (with confirmation)
  - Move/copy files

- **Search Enhancements**
  - Search file contents (not just names)
  - Regular expression search
  - Search history
  - Search result highlighting

### Nice to Have Features (from file_browser_implementation_priority.md)

#### Performance Optimizations
- Virtual scrolling for large directories
- Lazy loading of directory contents
- WebSocket connection pooling
- Implement request debouncing for rapid navigation
- Add progress indicators for long operations

#### UI/UX Improvements
- Drag and drop file selection
- Keyboard navigation improvements
  - Vim-style navigation (j/k for up/down)
  - Tab completion for paths
- File icons based on file type
- Customizable file browser themes
- Split pane view for comparing directories
- Bookmarks/favorites for frequently accessed paths

#### Advanced Features
- Git integration
  - Show git status in file browser
  - Display modified/staged/untracked files differently
- File history/versions
- Integration with external tools
- File metadata editor
- Custom file actions/plugins

## AI Tool Improvements

### Tool Enhancements
- **FindPatternTool**
  - Add support for negative patterns (exclude matches)
  - Implement incremental search with streaming results
  - Add fuzzy matching option
  - Support for binary file detection and handling
  - Add replace functionality (find and replace)

- **WorkspaceStatsTool**
  - Add trend analysis (growth over time)
  - Export statistics to various formats (CSV, JSON, charts)
  - Add code complexity metrics
  - Integration with git for contribution statistics
  - Performance profiling for slow operations

### New Tool Ideas
- **CodeAnalysisTool**
  - Static code analysis
  - Dependency tracking
  - Code quality metrics
  - Security vulnerability scanning

- **RefactoringTool**
  - Automated refactoring suggestions
  - Code formatting
  - Import optimization
  - Dead code detection

- **DocumentationTool**
  - Generate documentation from code
  - API documentation extraction
  - README generation
  - Docstring validation

## Agent System Enhancements

### Agent Improvements
- Dynamic agent switching based on task
- Agent collaboration framework
- Agent performance metrics
- Custom agent creation UI
- Agent marketplace/sharing

### Response Channels (Inspired by ChatGPT)
- **Multi-channel Response Architecture**
  - Separate channels for different types of content:
    - `analysis` channel: Private reasoning and analysis (never shown to user)
    - `commentary` channel: User-visible tool calls only (no plain text)
    - `final` channel: Polished user-facing response (no tool calls or reasoning)
  - Benefits:
    - Clean separation of concerns
    - No JSON/metadata leaking into user responses
    - Better control over what users see
    - Enables parallel processing of different response types
  - Implementation ideas:
    - Modify AI response structure to support multiple channels
    - Update streaming to handle channel-specific content
    - Frontend routing based on channel type
    - Channel-specific formatting and display rules
  - Would solve current issue where continuation metadata appears in chat

### Context Management (Extended)
- Persistent context across sessions
- Context templates for common scenarios
- Context versioning
- Shared context between agents
- **API Endpoints for Context Management**
  - GET /api/context/{session_id}/{agent_id} - Get current context
  - POST /api/context/refresh - Refresh stale items
  - DELETE /api/context/item/{item_id} - Remove specific item
  - GET /api/context/history/{session_id} - Context access history
  - POST /api/context/template - Save context as template
  - GET /api/context/templates - List available templates
- **Context-Aware Features**
  - Auto-suggest related files based on context
  - Context-based code completion hints
  - Warning when referencing outdated context
  - Context search (find in all context items)
  - Context bookmarks for important sections

## Interactive Mode Enhancements

### UI Improvements
- Multiple chat tabs/sessions
- Chat history search
- Export chat transcripts
- Custom UI layouts
- Theme customization

### Collaboration Features
- Multi-user sessions
- Screen sharing integration
- Code review mode
- Pair programming support

## Performance & Scalability

### Backend Optimizations
- Database integration for large-scale operations
- Distributed task processing
- Resource usage monitoring
- Auto-scaling for heavy workloads

### Caching Strategy
- Redis integration for distributed caching
- Smart cache warming
- Cache analytics
- Edge caching for static resources

## Security Enhancements

### Access Control
- Fine-grained permissions per tool
- Role-based access control
- Audit logging
- Secure token management

### Sandboxing
- Isolated execution environments
- Resource limits per operation
- Network access control
- File system quotas

## Integration Ideas

### Version Control
- Deep git integration
  - Show git blame info in context items
  - Track context items across git history
  - Auto-refresh context on git pull
  - Context diff between branches
- Support for other VCS (SVN, Mercurial)
- Automated commit message generation
- Branch management UI

### External Services
- Cloud storage integration (S3, GCS)
- CI/CD pipeline integration
- Issue tracker integration
- Documentation platform integration

### IDE Integration
- VS Code extension
- JetBrains plugin
- Vim/Neovim plugin
- Emacs package

### Claude SDK Integration
- Implement Claude CLI SDK as a proper AIService
  - Handle --verbose and --output-format stream-json for real-time output
  - Manage tool permissions with --allowedTools and --disallowedTools
  - Integrate MCP (Model Context Protocol) tools
  - Handle permission granting for tools
  - Implement timeout and error recovery
  - Stream response handling for better UX
- Benefits over cut-and-paste approach:
  - Automated execution without manual intervention
  - Better error handling and recovery
  - Structured output parsing
  - Tool usage capabilities
  - Session management
- Challenges to address:
  - Tool execution hanging issues
  - Permission management complexity
  - MCP tool discovery and integration
  - Different behavior with/without streaming

## Developer Experience

### Testing Improvements
- Visual regression testing for UI
- Performance benchmarking suite
- Automated accessibility testing
- Cross-browser testing

### Documentation
- Interactive tutorials
- Video walkthroughs
- API playground
- Example gallery

### Developer Tools
- Plugin/extension system
- Custom tool development kit
- Debugging utilities
- Performance profiler

## Notes

- Items in this document are not prioritized
- Some ideas may conflict or overlap
- Consider user feedback before implementing
- Evaluate ROI for each feature
- Some features may require significant architectural changes

## Recently Implemented Items

### Agent Context Tracking (2024-01-29)
- ✅ Core context tracking models (ContextItem, AgentContextManager)
- ✅ @ file reference parsing and automatic loading
- ✅ Integration with session manager
- ✅ Context freshness tracking
- ✅ Basic context size management

**Still TODO for Context Tracking:**
- File watching for automatic refresh
  - Use watchdog library for file system monitoring
  - Queue refresh operations for batch processing
  - Configurable refresh policies (auto/manual/hybrid)
- Context panel UI component
  - Show files/sections in current context
  - Freshness indicators (green/yellow/red based on staleness)
  - Quick actions (refresh, remove, view full file)
  - Context size and token count display
- Context timeline visualization
  - Visual timeline of when files were added/removed
  - Show file modifications over time
  - Context size changes graph
  - Agent switch events on timeline
- Cross-agent context sharing
  - Ability to transfer context between agents
  - Shared context pool for common files
  - Context inheritance when switching agents
- Smart section extraction (AST parsing)
  - Extract relevant functions/classes for context
  - Language-aware parsing (Python, JS, etc.)
  - Automatic related code discovery
  - Context compression for large files
- Context persistence/storage layer
  - SQLite/PostgreSQL storage backend
  - Context versioning and history
  - Export/import context sets
  - Context analytics and usage patterns
- Advanced Context Features
  - Context templates for common tasks
  - ML-based relevance scoring for context items
  - Automatic context pruning based on usage
  - Context diff visualization (what changed)
  - Integration with git for tracking file changes
  - Context recommendations based on current task

## Recently Deferred Items

### From Phase 4 Implementation
- Caching layer implementation (deferred due to time constraints)
  - Would significantly improve performance for large workspaces
  - Consider implementing before scaling to production

### From File Browser Implementation
- Advanced file operations (create, rename, delete)
  - Deferred to focus on read-only operations first
  - Important for full file management capabilities


## Async Multi-Agent Workflows (HIGH PRIORITY)

### Independent Agent AI Loops with Mailbox Coordination
Revolutionary architecture where each agent runs its own AI loop independently, enabling true parallel multi-agent workflows:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Agent E    │    │  Agent C    │    │  Agent P    │
│ (AI Loop 1) │◄──►│ (AI Loop 2) │◄──►│ (AI Loop 3) │
│ Plan Mgmt   │    │ Coding      │    │ RFC Design  │
└─────┬───────┘    └─────┬───────┘    └─────┬───────┘
      │                  │                  │
      └──────────────────┼──────────────────┘
                         │
                   ┌─────▼───────┐
                   │  Mailbox    │
                   │  System     │
                   └─────────────┘
```

**Agent Capabilities:**
- 🛌 **Sleep/Wake Control**: Agents can sleep on timers or events, wake up to check progress
- 📬 **Async Mailbox Communication**: "Hey Colin, can you implement this task?"
- 🔄 **Progress Monitoring**: "Alice, update me when user responds"
- ⚡ **Parallel Execution**: Multiple agents working simultaneously on different aspects
- 🤝 **Agent Coordination**: Agents can request help, delegate tasks, and collaborate

**Example Workflows:**
- **Agent E** decomposes plan → sleeps while **Agent C** codes individual tasks → wakes to commit completed work
- **Agent P** works on RFC planning while **Agent M** manages context in background
- **Alice** handles user interaction while specialized agents collaborate behind the scenes
- **Agent E** periodically checks task status and coordinates next steps

**Technical Architecture:**
- Independent AI session per agent
- Async task queues and event systems  
- Agent sleep/wake scheduling
- Mailbox-driven inter-agent communication
- Conflict resolution for shared resources
- Agent lifecycle management

**Benefits:**
- True parallel agent workflows
- Agents can specialize without blocking others
- Complex multi-step tasks can be decomposed and executed in parallel
- User interaction remains responsive while background work continues
- Natural delegation and collaboration patterns

**Implementation Challenges:**
- Managing multiple AI loops without conflicts
- Agent coordination and synchronization
- Resource sharing and locking
- Error handling across agent boundaries
- Debugging multi-agent interactions

## MCP (Model Context Protocol) Enhancements

### Connection Pooling for MCP Client
- Implement connection pooling for improved performance
  - Reuse connections for multiple requests
  - Configurable pool size limits
  - Connection health checking and automatic recovery
  - Load balancing across multiple MCP servers
  - Connection timeout and retry strategies
  - Metrics for pool utilization and performance
- Benefits:
  - Reduced connection overhead
  - Better resource utilization
  - Improved response times for frequent requests
  - Support for high-concurrency scenarios

## Async Agent Workflows - Completed Examples (2025-06-06)

### Implemented Workflows Using TDD
We've successfully implemented two comprehensive workflow examples demonstrating the async agent architecture:

#### 1. Bug Investigation Workflow ✅
- **Purpose**: Collaborative bug hunting with multiple agents
- **Features**:
  - Automatic bug severity classification based on keywords
  - Urgency-based agent wake patterns (critical bugs wake agents immediately)
  - Multi-agent collaboration (Debbie leads, Alice analyzes, Patricia designs fixes)
  - Root cause analysis and systemic issue detection
  - Security-aware fix generation
  - Batch investigation support for multiple bugs
  - Error recovery with confidence levels
- **Agents Used**: Debbie (Lead), Alice (Analysis), Patricia (Architecture), Eamonn (Implementation), Tessa (Testing)
- **Real-world Use Case**: Production bug triage and resolution

#### 2. Documentation Generation Workflow ✅
- **Purpose**: Intelligent multi-agent documentation creation
- **Features**:
  - Multiple documentation types (API, Tutorial, Migration, Comprehensive)
  - Multi-format output generation (Markdown, HTML, PDF, Docstrings)
  - Collaborative review process with iterations
  - Style guide enforcement (Google, NumPy, Sphinx)
  - Outdated documentation detection
  - Batch documentation for multiple targets
  - Tutorial generation with exercises
  - Migration guide with breaking change analysis
- **Agents Used**: Alice (Analysis), Patricia (Writing), Debbie (Debugging), Eamonn (Examples), Tessa (Review)
- **Real-world Use Case**: Maintaining up-to-date project documentation

### Future Workflow Ideas

#### 3. Continuous Monitoring Workflow
- **Purpose**: Background agents monitoring system health
- **Features**:
  - Periodic health checks with configurable intervals
  - Alert escalation based on severity
  - Trend analysis and anomaly detection
  - Auto-remediation for known issues
  - Integration with external monitoring tools
  - Dashboard generation for metrics
- **Agents**: New monitoring-focused agents, Debbie for issue investigation
- **Use Case**: Production system monitoring and alerting

#### 4. Code Review Workflow
- **Purpose**: Automated PR review and feedback
- **Features**:
  - Multi-agent code analysis
  - Style guide compliance checking
  - Security vulnerability detection
  - Performance impact analysis
  - Test coverage verification
  - Automated review comments generation
- **Agents**: Alice (Analysis), Tessa (Testing), new security-focused agent
- **Use Case**: Automated first-pass code review

#### 5. Release Management Workflow
- **Purpose**: Coordinate software releases
- **Features**:
  - Changelog generation from commits
  - Dependency update checking
  - Breaking change detection
  - Release notes drafting
  - Cross-platform build coordination
  - Deployment verification
- **Agents**: Patricia (Documentation), Eamonn (Execution), new deployment agent
- **Use Case**: Automated release process

#### 6. Learning and Training Workflow
- **Purpose**: Create personalized learning paths
- **Features**:
  - Skill assessment and gap analysis
  - Personalized tutorial generation
  - Progress tracking and adaptation
  - Exercise generation with solutions
  - Peer learning coordination
  - Knowledge retention testing
- **Agents**: Eamonn (Examples), Patricia (Content), new pedagogy agent
- **Use Case**: Developer onboarding and training

### Frontend Enhancements for Async Workflows

#### Workflow Visualization
- **Live Agent Status Dashboard**
  - Real-time agent state visualization (IDLE, ACTIVE, SLEEPING, WAITING)
  - Agent task queues and progress bars
  - Wake/sleep event timeline
  - Resource usage per agent
  
- **Workflow Designer UI**
  - Drag-and-drop workflow creation
  - Agent role assignment interface
  - Configuration templates
  - Visual workflow execution tracking
  
- **Inter-Agent Communication View**
  - Mailbox message flow visualization
  - Agent collaboration graph
  - Message priority indicators
  - Communication patterns analysis

#### Enhanced User Controls
- **Workflow Management**
  - Start/stop/pause workflow execution
  - Agent wake/sleep manual controls
  - Priority adjustment for running tasks
  - Workflow history and replay
  
- **Real-time Monitoring**
  - Live log streaming per agent
  - Performance metrics dashboard
  - Error and warning notifications
  - Agent health indicators

#### Interactive Features
- **Dynamic Agent Interaction**
  - Direct messaging to specific agents
  - Agent recommendation system
  - Task delegation interface
  - Collaborative workspace view
  
- **Workflow Templates**
  - Pre-built workflow templates
  - Custom workflow saving
  - Workflow sharing and import
  - Community workflow marketplace

### Technical Enhancements for Workflows

#### Performance Optimizations
- **Resource Management**
  - Dynamic agent pooling
  - Adaptive sleep/wake scheduling
  - Memory-aware task distribution
  - GPU acceleration for AI operations
  
- **Scalability Features**
  - Distributed agent execution
  - Workflow checkpointing
  - Partial workflow recovery
  - Load balancing across agents

#### Advanced Capabilities
- **Machine Learning Integration**
  - Workflow optimization based on historical data
  - Predictive task duration estimation
  - Anomaly detection in workflows
  - Auto-tuning of agent parameters
  
- **External Integrations**
  - Webhook support for workflow triggers
  - API endpoints for workflow management
  - Third-party tool integration
  - Event-driven workflow activation

## Random unstructured ideas
- MCP server ✅ (Implemented)
- MCP client ✅ (Implemented Phase 1)
- Alice to get a new project setup feature (can talk to agent P by mail for ideas on languages etc.)
- Agent C - Colin the Coder specialist coder. To coding tasks in Agent E plans
- Agent M - Mary the Memory. Reasonable for context manager + compact + per agent & project memory storage
- Our workspace project file only support 1 git worktree at a time, would be good to allow multiple worktree so multi plans can be run at the some time in isolation
- Base git integration on the right view and provided to agents
- Agent E should commit after each successful task
- ~~https://manus.im/share/file/5c80a565-2a61-449a-8f2b-350e2c41333a Manus.im for continuation for AI (High priority)~~
- Idea notepad that the quick ideas can be added to and agent P can select one for a new efc and plan if the user asks it
- Github integration for an agent or as an Agent? Agent R Roger the Repo Man
- Massive doc cleanup
- PDF and image support
- drag and drop in the frontend
- Agent specific model and providers
- Alice has a knowledge base about AIWhisperer, other topics?, other agents can to find info
- Discoverable tool and sets. Start with descriptioons, agents can ask to use them and it inserted into there tool 
- 'Minor Agents' double letter names and a hidden from the roster, mostly used by agents via mailbox
- Think on the idea of 'agents as tools' specialist intelligent tools that other agents can use.
  - Intellignt merge
  - Websearcher
  - A/B tester - agents can ask to test which is better for a given criteria, A/B can apply optimisations techniques.
- Prompt development refinement / agentic approach? https://manus.im/share/WZHngJw4Woo44W0IxgcYbh?replay=1 https://github.com/dontriskit/awesome-ai-system-prompts
- AI useable debuggers https://manus.im/share/file/18d10fa9-12ea-475c-8ac8-5f66a371420c
- Add options to be less 'friendly' for experienced use. i.e. AI introductions can be short/missing, agent E always tells you how to use claude
- Integrate AI dynamic buttons in the message bubbles, allow agents to create buttons using the output markdown for easy user interaction


## Notes about conceptual framework for multi-agent systems:
Our interface is a chat system. The main chat is a group chat which all agents can be part of we can also have (in theory, not implelented yet) private chats with an agents and small group chats as well (not implemented yet).
The main group chat doesn't nessecarily have a focused agent in the real world. I chat to all my mates, some will reply some not. Group chats like discord, irc, slack, etc. are all like this.
The question is does that make sense for agents?
The primary issue is confusion for the agents and cost of all the AI listening to everything
An alternative is to have a primary agent that is the main chat agent and the others are secondary agents that can be called on
This would have the current UI active agent get the users messages and prehaps a @name at the start of the message to indicate which agent to send it to
this solves several issues:
- Agents can be focused on specific tasks
- Costs are reduced as only the active agent is processing messages
- Agents can 'wake up' and process the messages that have happened while they were asleep (though this might get complicated)
To really work we might need rooms
We have a mailbox system that allows agents to send messages to each other, this is a good way to allow agents to communicate without needing to be in the same chat.
The other paradigm is to not base it on a chat system and more like email. The user sends and recieves messages from agents, they can reply to messages and the agents can reply back. This biggest issue is that the user won't see much of the interaction between agents, which is a key part of the system.

Prehaps we always open 2 chats at start, a private one with Alice The Assistant and the main group chat. If you want a quiet life you can chat with alice who will update and route your messages to the correct agent/s. If you want to see the group chat you can but it might get rowdy like a real shared group chat...

---

*Last Updated: 2025-06-05*

