# Universal Mailbox System Design

## Overview

The AIWhisperer mailbox system provides a standardized way for agents to communicate with each other and with users. This design offers several advantages over point-to-point communication:

1. **Unified Interface**: All communication goes through standard mailbox tools
2. **Asynchronous Ready**: Can easily extend to async operations
3. **User Integration**: Same system works for agent-to-user communication
4. **Mail Notifications**: Agents get "you've got mail" notifications
5. **Conversation Threading**: Track related messages
6. **Priority Support**: Urgent messages can be flagged

## Components

### 1. Mail Message Structure
```python
@dataclass
class Mail:
    message_id: str
    from_agent: str  # Empty string = user
    to_agent: str    # Empty string = user
    subject: str
    body: str
    priority: MessagePriority
    timestamp: datetime
    status: MessageStatus
    reply_to: Optional[str]
    metadata: Dict[str, Any]
```

### 2. Mailbox Tools

#### send_mail
- Send messages to any agent or user
- Set priority levels
- Include metadata
- Automatic notification on delivery

#### check_mail
- Read unread messages
- View message history
- Filter by status
- Mark messages as read

#### reply_mail
- Reply to existing messages
- Maintains conversation threading
- Auto-generates "Re:" subjects

### 3. Notification System

Agents receive notifications when they have unread mail:
- Count of unread messages
- Appended to agent responses
- Can register custom handlers

## Usage Examples

### Agent E requests clarification from Agent P
```python
# Agent E sends mail
mail = Mail(
    from_agent="agent_e",
    to_agent="agent_p",
    subject="Clarification needed: Authentication task",
    body="Should we use JWT or OAuth2?",
    priority=MessagePriority.HIGH
)
mailbox.send_mail(mail)

# Agent P checks mail
messages = mailbox.check_mail("agent_p")
# Process and reply...
```

### User sends task to agent
```python
# User sends mail (from_agent is empty)
mail = Mail(
    from_agent="",
    to_agent="agent_p",
    subject="Create new RFC",
    body="Please create an RFC for adding dark mode"
)
```

### Mail notification in response
```
Agent P: I've completed the RFC for dark mode. You can find it at...

📬 You have 2 unread messages in your mailbox.
```

## Integration with Existing Systems

1. **Session Manager**: Can switch agents when mail arrives
2. **Tool Registry**: Mail tools available to all agents
3. **Agent Handlers**: Use mailbox instead of direct messaging
4. **Batch Mode**: Can queue messages for later processing

## Future Extensions

1. **Async Processing**: Process mail in background
2. **Mail Filters**: Auto-sort by rules
3. **Attachments**: Include files or data
4. **Broadcast**: Send to multiple agents
5. **Scheduled Delivery**: Send at specific times
6. **Read Receipts**: Know when mail was read

## Benefits Over Direct Messaging

1. **Decoupling**: Agents don't need direct references
2. **History**: All communication is tracked
3. **Flexibility**: Easy to add new agents
4. **Testing**: Can mock mailbox for tests
5. **User-Friendly**: Same interface for human interaction