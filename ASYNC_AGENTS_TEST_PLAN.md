# Async Agents Comprehensive Test Plan

## Overview
Systematic test plan to validate both synchronous mail switching and async agent capabilities.

## Test Categories

### 1. Synchronous Mail Tests

#### 1.1 Basic Tests ✅
- [x] Simple conversation test
- [x] Basic tool call after switch
- [ ] Long complex task with multiple steps

#### 1.2 Complex Multi-Step Task Test
**Test**: Send mail to Debbie to analyze codebase and generate report
```
Alice → Debbie: "Please analyze the ai_whisperer/tools directory:
1. Count total files
2. List all tool categories
3. Find the most complex tool
4. Generate a summary report"
```
**Expected**: Debbie performs multiple tool calls and returns comprehensive report

#### 1.3 Agent Chain Test (A → D → P)
**Test**: Alice delegates to Debbie who delegates to Patricia
```
Alice → Debbie: "Debug why RFC creation is slow"
Debbie → Patricia: "Analyze RFC creation workflow"
Patricia → Debbie: "Found bottleneck in file I/O"
Debbie → Alice: "Issue identified and solution proposed"
```
**Expected**: Full chain executes with proper context

#### 1.4 Circular Detection Test
**Test**: Create circular mail chain
```
Alice → Debbie: "Forward this to Patricia"
Debbie → Patricia: "Forward this to Alice"
Patricia → Alice: "Forward this to Debbie"
```
**Expected**: System detects and prevents infinite loop

### 2. Background Async Tests

#### 2.1 Scheduled Wake Test
**Test**: Agent wakes on timer to monitor system
```
1. Put Debbie to sleep for 5 seconds
2. Debbie wakes up
3. Checks system health
4. Goes back to sleep
```
**Expected**: Autonomous wake and task execution

#### 2.2 Wake and Check Mail Tests

##### 2.2.1 No Mail Test
```
1. Put Debbie to sleep with mail check wake event
2. Trigger wake event
3. Debbie checks mail (finds none)
4. Goes back to sleep
```

##### 2.2.2 Mail Processing Test
```
1. Put Debbie to sleep
2. Alice sends mail to sleeping Debbie
3. Wake Debbie with mail event
4. Debbie processes mail and responds
```

#### 2.3 Agent Inspection Test
**Test**: Debbie monitors other agents
```
1. Alice and Patricia running tasks
2. Debbie wakes periodically
3. Inspects agent states
4. Reports anomalies
```

#### 2.4 Wake and Send Sync Mail
**Test**: Background agent uses sync mail
```
1. Debbie sleeping with timer
2. Wakes and detects issue
3. Uses send_mail_with_switch to alert Alice
4. Waits for Alice's response
```

#### 2.5 Wake and Send Async Mail
**Test**: Background agent sends async mail
```
1. Debbie monitoring in background
2. Detects multiple issues
3. Sends async mail to multiple agents
4. Continues monitoring without waiting
```

### 3. Advanced Scenarios

#### 3.1 Parallel Task Distribution
**Test**: Alice distributes work to multiple agents
```
1. Alice receives complex request
2. Breaks into subtasks
3. Sends to D, E, P simultaneously
4. Collects results asynchronously
```

#### 3.2 Event-Driven Coordination
**Test**: Agents coordinate via events
```
1. Patricia completes RFC draft
2. Broadcasts "rfc_ready" event
3. Eamonn wakes to review
4. Debbie wakes to validate
```

#### 3.3 Resource Management
**Test**: System handles resource limits
```
1. Start maximum agents
2. Try to start one more
3. Verify graceful rejection
4. Stop agent and retry
```

## Implementation Plan

### Phase 1: Core Sync Tests
1. Implement complex multi-step test
2. Implement chain test
3. Verify circular detection

### Phase 2: Basic Async Tests
1. Implement scheduled wake
2. Implement mail checking
3. Test sleep/wake cycles

### Phase 3: Advanced Async
1. Agent inspection
2. Mixed sync/async communication
3. Parallel workflows

### Phase 4: Stress Testing
1. Multiple agents running
2. High message volume
3. Resource limits

## Test File Structure
```
tests/integration/async_agents/
  test_sync_mail_complex.py
  test_sync_mail_chains.py
  test_async_wake_schedule.py
  test_async_mail_events.py
  test_async_inspection.py
  test_async_coordination.py
  test_resource_limits.py
```

## Success Criteria
- [ ] All sync mail patterns work reliably
- [ ] Async agents wake/sleep correctly
- [ ] Mail events trigger properly
- [ ] No resource leaks
- [ ] Circular detection prevents loops
- [ ] Mixed sync/async patterns work
- [ ] System remains stable under load