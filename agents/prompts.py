from enum import Enum
import json
from typing import Dict, Any, Optional
from agents.exceptions import InvalidTaskStructureError


class PromptType(Enum):
	NORMAL_RESPONSE = "NORMAL_RESPONSE"
	DELEGATE_TASK = "DELEGATE_TASK"
	DELEGATE_BACK = "DELEGATE_BACK"
	USE_TOOL = "USE_TOOL"
	TOOL_RETURN = "TOOL_RETURN"
	REFINEMENT_RESPONSE = "REFINEMENT_RESPONSE"


DELEGATION_PROMPT = """
# DELEGATION GUIDELINES AND FORMAT:
- When you need to delegate a task write the following JSON:
```json
{
	"action": "DELEGATE_TASK",
    "agent": "[Agent Name]",
    "caller_agent": "[Agent Name of the agent that is delegating the task]",
    "reason": "[Concise reason for delegation]",
    "user_input": "[User input that triggered the delegation]"
}
```
Make sure it is a valid JSON object.
Return only the JSON object, no other text!
"""

class delegation_prompt:
	def __init__(self, json_data: Dict[str, Any]):
		self._parsed_data = self._validate(json_data)
	
	def _validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
		required_fields = ["action", "agent", "caller_agent", "reason", "user_input"]
		for field in required_fields:
			if field not in data:
				raise InvalidTaskStructureError(f"Missing required field: {field}")
			if not isinstance(data[field], str):
				raise InvalidTaskStructureError(f"Field {field} must be a string")
		
		if data["action"] != "DELEGATE_TASK":
			raise InvalidTaskStructureError("Action must be 'DELEGATE_TASK'")
		
		return data
	
	@property
	def action(self) -> str:
		return self._parsed_data["action"]
	
	@property
	def agent(self) -> str:
		return self._parsed_data["agent"]
	
	@property
	def caller_agent(self) -> str:
		return self._parsed_data["caller_agent"]
	
	@property
	def reason(self) -> str:
		return self._parsed_data["reason"]
		
	@property
	def user_input(self) -> str:
		return self._parsed_data["user_input"]
	
	@property
	def parsed_data(self) -> Dict[str, Any]:
		return self._parsed_data.copy()
	
	def generate_prompt(self) -> str:
		return f"""
You were delegated from {self.caller_agent}.
{self.user_input}.
"""
	
	def __repr__(self) -> str:
		return f"DelegationPrompt(data={self._parsed_data})"

DELEGATION_BACK_PROMPT = """
# DELEGATION BACK GUIDELINES AND FORMAT:
- When you need to return to the caller agent, write the following JSON:
```json
{
	"action": "DELEGATE_BACK",
    "return_to_agent": "[Agent Name to return to]",
    "return_from_agent": "[Agent Name returning from]",
    "reason": "[Concise reason for returning to the caller agent]",
    "success": "[True if the requested task was successful, False otherwise]"
}
```
Make sure it is a valid JSON object.
Return only the JSON object, no other text!
"""

class delegation_back_prompt:
	def __init__(self, json_data: Dict[str, Any]):
		self._parsed_data = self._validate(json_data)
	
	def _validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
		required_fields = ["action", "return_to_agent", "return_from_agent", "reason", "success"]
		for field in required_fields:
			if field not in data:
				raise InvalidTaskStructureError(f"Missing required field: {field}")
			if not isinstance(data[field], str):
				raise InvalidTaskStructureError(f"Field {field} must be a string")
		
		if data["action"] != "DELEGATE_BACK":
			raise InvalidTaskStructureError("Action must be 'DELEGATE_BACK'")
		
		if data["success"] not in ["True", "False"]:
			raise InvalidTaskStructureError("Success field must be 'True' or 'False'")
		
		return data
	
	@property
	def action(self) -> str:
		return self._parsed_data["action"]
	
	@property
	def return_to_agent(self) -> str:
		return self._parsed_data["return_to_agent"]
	
	@property
	def return_from_agent(self) -> str:
		return self._parsed_data["return_from_agent"]
	
	@property
	def reason(self) -> str:
		return self._parsed_data["reason"]
	
	@property
	def success(self) -> str:
		return self._parsed_data["success"]
	
	@property
	def success_bool(self) -> bool:
		return self._parsed_data["success"] == "True"
	
	@property
	def parsed_data(self) -> Dict[str, Any]:
		return self._parsed_data.copy()

	def generate_prompt(self) -> str:
		return f"""
You were delegated back from {self.return_from_agent}.
reason: {self.reason}.
success: {self.success}.
"""
 
	def __repr__(self) -> str:
		return f"DelegationBackPrompt(data={self._parsed_data})"

TOOLS_PROMPT = """
# TOOLS GUIDELINES AND FORMAT:
- When you need to use a tool, write the following JSON:
```json
{
	"action": "USE_TOOL",
	"tool": "[Tool Name]",
	"args": "[Tool arguments seperated by comma. example: 'arg1=value1,arg2=value2,...']"
}
```
Make sure it is a valid JSON object.
Return only the JSON object, no other text!
"""

class tools_prompt:
	def __init__(self, json_data: Dict[str, Any]):
		self._parsed_data = self._validate(json_data)
	
	def _validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
		required_fields = ["action", "tool", "args"]
		for field in required_fields:
			if field not in data:
				raise InvalidTaskStructureError(f"Missing required field: {field}")
			if not isinstance(data[field], str):
				raise InvalidTaskStructureError(f"Field {field} must be a string")
		
		if data["action"] != "USE_TOOL":
			raise InvalidTaskStructureError("Action must be 'USE_TOOL'")
		
		return data
	
	@property
	def action(self) -> str:
		return self._parsed_data["action"]
	
	@property
	def tool(self) -> str:
		return self._parsed_data["tool"]
	
	@property
	def args(self) -> str:
		return self._parsed_data["args"]
	
	@property
	def parsed_data(self) -> Dict[str, Any]:
		return self._parsed_data.copy()
		
	def __repr__(self) -> str:
		return f"ToolsPrompt(data={self._parsed_data})"

TOOL_RETURN_PROMPT = """
# TOOL RETURN GUIDELINES AND FORMAT:
- When a tool execution is complete, write the following JSON:
```json
{
	"action": "TOOL_RETURN",
	"tool": "[Tool Name that was executed]",
	"result": "[Result of the tool execution]",
	"success": "[True if the tool executed successfully, False otherwise]"
}
```
Make sure it is a valid JSON object.
Return only the JSON object, no other text!
"""

class tool_return_prompt:
	def __init__(self, json_data: Optional[Dict[str, Any]] = None):
		if json_data is None:
			json_data = {
				"action": "TOOL_RETURN",
				"tool": "",
				"result": "",
				"success": "False"
			}
		self._parsed_data = self._validate(json_data)
	
	def _validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
		required_fields = ["action", "tool", "result", "success"]
		for field in required_fields:
			if field not in data:
				raise InvalidTaskStructureError(f"Missing required field: {field}")
			if not isinstance(data[field], str):
				raise InvalidTaskStructureError(f"Field {field} must be a string")
		
		if data["action"] != "TOOL_RETURN":
			raise InvalidTaskStructureError("Action must be 'TOOL_RETURN'")
		
		if data["success"] not in ["True", "False"]:
			raise InvalidTaskStructureError("Success field must be 'True' or 'False'")
		
		return data
	
	@property
	def action(self) -> str:
		return self._parsed_data["action"]
	
	@action.setter
	def action(self, value: str):
		self._parsed_data["action"] = value
	
	@property
	def tool(self) -> str:
		return self._parsed_data["tool"]
	
	@tool.setter
	def tool(self, value: str):
		self._parsed_data["tool"] = value
	
	@property
	def result(self) -> str:
		return self._parsed_data["result"]
	
	@result.setter
	def result(self, value: str):
		self._parsed_data["result"] = value
	
	@property
	def success(self) -> str:
		return self._parsed_data["success"]
	
	@success.setter
	def success(self, value: str):
		if value not in ["True", "False"]:
			raise InvalidTaskStructureError("Success field must be 'True' or 'False'")
		self._parsed_data["success"] = value
	
	@property
	def success_bool(self) -> bool:
		return self._parsed_data["success"] == "True"
	
	@property
	def inner_dict(self) -> Dict[str, Any]:
		return self._parsed_data
	
	def as_json(self) -> str:
		return json.dumps(self._parsed_data, indent=4)
 
	def __repr__(self) -> str:
		return f"ToolReturnPrompt(data={self._parsed_data})"


REFINEMENT_RESPONSE_PROMPT = """
# REFINEMENT RESPONSE GUIDELINES AND FORMAT:
- When you need to provide a refinement response, write the following JSON:
```json
{
	"action": "REFINEMENT_RESPONSE",
	"new_plan": "[Your refined plan here]",
	"done": "[yes or no]",
	"score": [0-100],
	"why": "[brief justification (≤40 tokens)]",
	"checklist": {
		"objective": [true or false],
		"inputs": [true or false],
		"outputs": [true or false],
		"constraints": [true or false]
	},
	"success": [true or false]
}
```
Make sure it is a valid JSON object.
Return only the JSON object, no other text!
"""

class refinement_response_prompt:
	def __init__(self, json_data: Optional[Dict[str, Any]] = None):
		if json_data is None:
			json_data = {
				"action": "REFINEMENT_RESPONSE",
				"new_plan": "",
				"done": "no",
				"score": 0,
				"why": "",
				"checklist": {"objective": False, "inputs": False, "outputs": False, "constraints": False},
				"success": False
			}
		self._parsed_data = self._validate(json_data)
	
	def _validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
		required_fields = ["action", "new_plan", "done", "score", "why", "checklist", "success"]
		for field in required_fields:
			if field not in data:
				raise InvalidTaskStructureError(f"Missing required field: {field}")
		
		if data["action"] != "REFINEMENT_RESPONSE":
			raise InvalidTaskStructureError("Action must be 'REFINEMENT_RESPONSE'")
		
		if not isinstance(data["new_plan"], str):
			raise InvalidTaskStructureError("new_plan must be a string")
		
		if data["done"] not in ["yes", "no"]:
			raise InvalidTaskStructureError("done must be 'yes' or 'no'")
		
		if not isinstance(data["score"], int) or data["score"] < 0 or data["score"] > 100:
			raise InvalidTaskStructureError("score must be an integer between 0 and 100")
		
		if not isinstance(data["why"], str):
			raise InvalidTaskStructureError("why must be a string")
		
		if not isinstance(data["checklist"], dict):
			raise InvalidTaskStructureError("checklist must be a dictionary")
		
		required_checklist_fields = ["objective", "inputs", "outputs", "constraints"]
		for field in required_checklist_fields:
			if field not in data["checklist"]:
				raise InvalidTaskStructureError(f"checklist missing required field: {field}")
			if not isinstance(data["checklist"][field], bool):
				raise InvalidTaskStructureError(f"checklist.{field} must be a boolean")
		
		if not isinstance(data["success"], bool):
			raise InvalidTaskStructureError("success must be a boolean")
		
		return data
	
	@property
	def action(self) -> str:
		return self._parsed_data["action"]
	
	@property
	def new_plan(self) -> str:
		return self._parsed_data["new_plan"]
	
	@property
	def done(self) -> str:
		return self._parsed_data["done"]
	
	@property
	def score(self) -> int:
		return self._parsed_data["score"]
	
	@property
	def why(self) -> str:
		return self._parsed_data["why"]
	
	@property
	def checklist(self) -> Dict[str, bool]:
		return self._parsed_data["checklist"].copy()
	
	@property
	def success(self) -> bool:
		return self._parsed_data["success"]
	
	@property
	def parsed_data(self) -> Dict[str, Any]:
		return self._parsed_data.copy()
	
	def as_json(self) -> str:
		return json.dumps(self._parsed_data, indent=4)
 
	def __repr__(self) -> str:
		return f"RefinementResponsePrompt(data={self._parsed_data})"

