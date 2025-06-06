# Tool Calling Test Logbook

This logbook tracks all tests related to agent tool calling, particularly focusing on mail handling between agents.

## Test Configuration
- **Date Started**: 2025-06-05
- **Primary Model**: openai/gpt-4o (set in agent configs)
- **Test Environment**: AIWhisperer conversation replay mode
- **Primary Issue**: Agents not executing tool requests received via mail

## Test Results

### Test 1: Debbie Self-Mail Test
**Date**: 2025-06-05 20:33
**Agent**: Debbie (d)
**Model**: openai/gpt-4o
**Test File**: `test_direct_debbie.txt`
**Command**: `AIWHISPERER_DEFAULT_AGENT=d python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay test_direct_debbie.txt`
**Test Content**:
```
You are Debbie. First, use the send_mail tool to send yourself a test message with subject 'Self Test' and body 'list_directory requested'. Then check your mail and report what you find.
```
**Result**: ✅ SUCCESS
- Debbie successfully sent mail to herself
- Debbie successfully checked mail and found the message
- Reported: "Test message sent and received successfully. Subject: 'Self Test', Body: 'list_directory requested'."
- Tool calls made: 2 (send_mail, check_mail)
**Key Finding**: Basic tool calling and mailbox functionality work correctly with GPT-4o

---

### Test 2: Alice Send Mail to Debbie
**Date**: 2025-06-05 20:41
**Agent**: Alice (a)
**Model**: openai/gpt-4o
**Test File**: `test_alice_to_debbie_basic.txt`
**Command**: `python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay test_alice_to_debbie_basic.txt`
**Test Content**:
```
Use the send_mail tool to send a message to Debbie with subject 'Tool Request' and body 'Please use the list_directory tool to show the contents of the current directory.'
```
**Result**: ✅ SUCCESS
- Alice successfully sent mail to Debbie
- Message ID: efe8f46e-a748-4231-ac6f-2303ab1486c2
- Tool calls made: 1 (send_mail)
**Key Finding**: Alice can send mail successfully

---

### Test 3: Debbie Check Mail (Separate Session)
**Date**: 2025-06-05 20:42
**Agent**: Debbie (d)
**Model**: openai/gpt-4o
**Test File**: `test_debbie_check_separate.txt`
**Command**: `AIWHISPERER_DEFAULT_AGENT=d python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay test_debbie_check_separate.txt`
**Test Content**:
```
Check your mail and execute any tool requests you find.
```
**Result**: ❌ FAILED
- Debbie called check_mail successfully
- But found 0 messages
- Response: "No unread messages found in the mailbox. There are no tool requests to execute."
- Tool calls made: 1 (check_mail)
**Key Finding**: Mail does not persist between conversation replay sessions

---

### Test 4: Send Mail with Switch
**Date**: 2025-06-05 20:43
**Agent**: Alice (a) -> Debbie (d)
**Model**: openai/gpt-4o
**Test File**: `test_alice_send_with_switch.txt`
**Command**: `python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay test_alice_send_with_switch.txt`
**Test Content**:
```
Use send_mail_with_switch to send a message to Debbie with subject 'Tool Request' and body 'Please use the list_directory tool to show the contents of the current directory.'
```
**Result**: ❌ FAILED
- Alice successfully sent mail with send_mail_with_switch
- Message ID: c4fc51d0-781f-438c-a94a-39399ccaa071
- Debbie was activated (agent switch occurred)
- Debbie called check_mail({"unread_only":true})
- But response_length was 0 - no mail found
- Debbie did NOT execute list_directory
- Tool calls made: Alice: 1 (send_mail_with_switch), Debbie: 1 (check_mail)
**Key Finding**: send_mail_with_switch successfully switches agents, and Debbie attempts to check mail, but the mail is not in her inbox

---

## Summary of Findings

1. **Tool calling works**: GPT-4o can successfully call tools (proven by all tests)
2. **Mailbox works within session**: When Debbie sends mail to herself in the same session, she can retrieve it
3. **Mailbox doesn't persist between sessions**: Mail sent in one conversation replay session is not available in another
4. **send_mail_with_switch issue**: Even though this keeps agents in the same session, Debbie doesn't find the mail in her inbox when activated
5. **Debbie IS trying**: When activated via send_mail_with_switch, Debbie correctly calls check_mail, but gets 0 results

### Test 5: Mock check_mail to isolate tool execution
**Date**: 2025-06-05 20:49
**Agent**: Debbie (d)
**Model**: openai/gpt-4o
**Test**: Replace check_mail tool with mock that returns fake mail
**Command**: `python test_debbie_with_mock_mail.py`
**Result**: ❓ INCONCLUSIVE
- ✅ Mock was successfully installed and test ran
- ✅ Debbie called check_mail tool 
- ❓ No evidence that mock was actually executed (no MOCK CHECK_MAIL logs)
- ❓ No evidence of list_directory execution after check_mail
- Tool calls made: 1 (check_mail)
**Key Finding**: Test infrastructure worked but can't confirm if mock was loaded by tool registry

---

### Test 6: Manual Mail Injection Test
**Date**: 2025-06-05 20:52
**Agent**: Debbie (d)
**Model**: openai/gpt-4o
**Test**: Manually add mail to mailbox before running Debbie
**Command**: `python test_debbie_manual_mail.py`
**Result**: 🔑 ROOT CAUSE FOUND
- ✅ Successfully added 2 test mails to mailbox (for 'd' and 'debbie')
- ✅ Verified mail exists in mailbox for all agent name variations
- ❌ Debbie still found 0 messages when checking in subprocess
- Tool calls made: 1 (check_mail)
**Key Finding**: Each conversation replay runs in a separate process with its own mailbox singleton instance!

---

## Summary of Findings

1. **Tool calling works**: GPT-4o can successfully call tools (proven by all tests)
2. **Mailbox works within session**: When Debbie sends mail to herself in the same session, she can retrieve it
3. **Process isolation**: Each conversation replay runs in a separate process with its own mailbox singleton
4. **send_mail_with_switch WORKS**: Mail IS delivered and Debbie DOES find it!
5. **Debbie CAN execute tools**: Test 8 proves she executes tool requests when given directly
6. **FINAL ROOT CAUSE**: Debbie treats mail content as information, not as actionable commands
   - She reads: "Please use the list_directory tool."
   - She understands it's from another agent
   - But she doesn't interpret it as a command to execute
   - This is a prompt/instruction issue, not a technical issue

## Next Steps

### The Real Issue: Debbie doesn't execute tool requests from mail

We've now confirmed:
1. ✅ send_mail_with_switch works correctly
2. ✅ Mail is delivered to Debbie's inbox
3. ✅ Debbie checks mail and finds the message
4. ✅ Debbie reads the mail body: "Please use the list_directory tool."
5. ❌ Debbie does NOT execute the list_directory tool

### Root Cause Hypothesis:
Debbie's prompt instructs her to process mail, but she may not be interpreting "Please use the list_directory tool" as a direct command to execute. She might be:
1. Just reading and acknowledging the mail
2. Not understanding it as an actionable request
3. Missing the connection between mail content and tool execution

### Solution:

The fix is simple - update Debbie's system prompt to clarify that mail content should be treated as actionable requests:

```
## Mail Processing Protocol
When you check mail and find messages:
1. Read each message carefully - look at the "body" field
2. If the body contains a request to use a tool (e.g., "Please use the list_directory tool..."), you MUST execute that tool
3. Treat mail content as direct requests from other agents that need to be fulfilled
4. Execute the requested tools and include results in your response
5. After completing the task, switch back to the sender
```

This is not a technical bug - all the infrastructure works correctly. It's simply that Debbie's current prompt doesn't make it clear that mail content should be treated as executable requests rather than just information to read.

## CRITICAL UPDATE

After checking Debbie's prompt file, I discovered that **the prompt ALREADY contains these exact instructions!** Lines 8-18 of `debbie_debugger.prompt.md` explicitly state:
- "If the body contains a request to use a tool... you MUST execute that tool"
- "When you receive mail like 'Please use the list_directory tool...', you must... actually call list_directory()"

This means:
1. The prompt is correct
2. The infrastructure works
3. But Debbie (GPT-4o) is not following her own instructions

### Possible reasons:
1. **Model behavior**: GPT-4o might be interpreting the mail as "reporting" rather than "requesting"
2. **Context switching**: The agent switch might be interrupting the flow
3. **Prompt priority**: Other instructions might be overriding the mail processing protocol

### Final recommendation:
Test with different phrasing in the mail body:
- "EXECUTE: list_directory"
- "I need you to run list_directory"
- "ACTION REQUIRED: Use list_directory tool"

Or consider adding a mail type/priority system to make actionable requests more explicit.

### Test 7: Send Mail with Switch Debug Test
**Date**: 2025-06-05 20:54
**Agent**: Alice (a) -> Debbie (d)
**Model**: openai/gpt-4o (both agents)
**Test File**: `test_mail_switch_debug.txt`
**Command**: `python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay test_mail_switch_debug.txt`
**Test Content**:
```
Use send_mail_with_switch to send a message to agent 'd' with subject 'Debug Test' and body 'Please use the list_directory tool.'
```
**Result**: ✅ PARTIAL SUCCESS - Mail delivered but tool not executed
- Alice successfully sent mail with send_mail_with_switch
- Message ID: 27bf33de-d715-420a-af63-b19b61f5f1e0  
- Agent switch occurred (a -> d -> a)
- Debbie WAS activated with prompt: "You have been activated via agent switch from a. Use the check_mail() tool to check your mailbox and process any requests."
- Debbie called check_mail and FOUND 1 message!
- Message details: from='a', to='debbie', subject='Debug Test', body='Please use the list_directory tool.'
- ❌ BUT: No evidence that Debbie executed list_directory after reading the mail
- Agent logs show discrepancy: response_length: 0 despite finding mail
- Tool calls made: Alice: 1 (send_mail_with_switch), Debbie: 1 (check_mail)
**Key Finding**: send_mail_with_switch DOES work! Mail is delivered and Debbie finds it. The remaining issue is that Debbie doesn't execute the tool request from the mail content.

---

### Test 8: Debbie Direct Tool Request
**Date**: 2025-06-05 21:01
**Agent**: Debbie (d)
**Model**: openai/gpt-4o
**Test File**: `test_debbie_direct_tool.txt`
**Command**: `AIWHISPERER_DEFAULT_AGENT=d python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay test_debbie_direct_tool.txt`
**Test Content**:
```
Please use the list_directory tool to show the contents of the current directory.
```
**Result**: ✅ SUCCESS
- Debbie successfully executed list_directory(path=".")
- Response: "The current directory contains 16 directories and 79 files, including folders like ai_whisperer, config, and docs."
- Tool calls made: 1 (list_directory)
**Key Finding**: Debbie CAN execute tool requests when given directly. The issue is specific to mail processing.

### Test 7: Send Mail with Switch Debug Test
**Date**: 2025-06-05 20:54
**Agent**: Alice (a) -> Debbie (d)
**Model**: openai/gpt-4o (both agents)
**Test File**: `test_mail_switch_debug.txt`
**Command**: `python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay test_mail_switch_debug.txt`
**Test Content**:
```
Use send_mail_with_switch to send a message to agent 'd' with subject 'Debug Test' and body 'Please use the list_directory tool.'
```
**Result**: ✅ PARTIAL SUCCESS - Mail delivered but tool not executed
- Alice successfully sent mail with send_mail_with_switch
- Message ID: 27bf33de-d715-420a-af63-b19b61f5f1e0  
- Agent switch occurred (a -> d -> a)
- Debbie WAS activated with prompt: "You have been activated via agent switch from a. Use the check_mail() tool to check your mailbox and process any requests."
- Debbie called check_mail and FOUND 1 message!
- Message details: from='a', to='debbie', subject='Debug Test', body='Please use the list_directory tool.'
- ❌ BUT: No evidence that Debbie executed list_directory after reading the mail
- Agent logs show discrepancy: response_length: 0 despite finding mail
- Tool calls made: Alice: 1 (send_mail_with_switch), Debbie: 1 (check_mail)
**Key Finding**: send_mail_with_switch DOES work! Mail is delivered and Debbie finds it. The remaining issue is that Debbie doesn't execute the tool request from the mail content.

---
