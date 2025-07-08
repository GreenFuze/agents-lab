# RESPONSE TYPE GUIDE

You must respond using one of the following action types:

1. **NORMAL_RESPONSE**  
   Use when you need to return free text or ask a question.  
   Fields: `"response"` — your message text.

2. **USE_TOOL**  
   Use when you need to call a tool.  
   Fields: `"tool"` (tool name), `"args"` (arguments as string or object).

3. **TOOL_RETURN**  
   Use when returning the result of a tool you previously called.  
   Fields: `"tool"`, `"result"`, `"success"` (true/false).

4. **DELEGATE_TASK**  
   Use when another agent is better suited to handle the task, or user explicitly request to switch agent.
   Fields: `"agent"`, `"caller_agent"`, `"reason"`, `"user_input"`.

5. **DELEGATE_BACK**
   Use when returning to a previously delegating agent.  
   Fields: `"return_to_agent"`, `"return_from_agent"`, `"reason"`, `"success"`.