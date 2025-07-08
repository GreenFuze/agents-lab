from typing import Dict, List, Optional, Any, Tuple
import json
import time
import difflib

from models.bases import InferenceConfig, ModelInfo, ModelInstanceBase, SummarizationConfig
from agents.exceptions import *
from models.models_pool import ModelsPoolInstance
import utils.logger as logger


# Global prompt templates
SUMMARIZATION_PROMPT = """
Summarize the following agent conversation history into a concise bullet-point list.
Focus on facts, decisions, and tool usage. Avoid redundant or low-signal information.

Conversation:
{summary_content}

Your summary should emphasize:
- Key user requests
- Actions taken by the agent (e.g. tool calls, delegations)
- Results or important returned values
- Current state or pending decisions

Format your summary as a clean bullet list (use '-' for each point).
"""

SCRATCHPAD_REFINEMENT_PROMPT = """
You are refining a task request step by step.

Current plan:
{plan}

Full context that led to this plan:
{full_context}

Think step by step and rewrite the plan to be clearer, more complete, or more precise.
If already optimal, return it unchanged.

### Thought process:
[Think through what could be improved about the current plan]

### New plan:
[Your refined version of the plan]

Now evaluate whether the following are present in your new plan (true/false):
- Objective: Is the goal clear?
- Inputs: Are required inputs specified?
- Outputs: Are expected outputs defined?
- Constraints: Are limitations/constraints mentioned?

You must respond with a JSON object following this exact format:
{{
  "action": "REFINEMENT_RESPONSE",
  "new_plan": "your refined plan here",
  "done": "yes or no",
  "score": 0-100,
  "why": "brief justification (≤40 tokens)",
  "checklist": {{
    "objective": true or false,
    "inputs": true or false,
    "outputs": true or false,
    "constraints": true or false
  }},
  "success": true or false
}}
"""


class ScratchpadConfig:
	def __init__(self, *, enabled: bool = True, max_iterations: int = 5, score_lower_bound: int = 70, 
				 similarity_threshold: float = 0.9, unchanged_limit: int = 2):
		self.enabled = enabled
		self.max_iterations = max_iterations
		self.score_lower_bound = score_lower_bound
		self.similarity_threshold = similarity_threshold
		self.unchanged_limit = unchanged_limit


class Agent:
	def __init__(self, name: str,
              		   model: ModelInfo,
                   	   system_prompt: str,
                       seed_prompts: Optional[list[dict[str, str]]],
                       inference_config: InferenceConfig,
                       summarization_config: SummarizationConfig,
                       scratchpad_config: Optional[ScratchpadConfig] = None):
		"""
		Initialize the base agent
		
		Args:
			name: Name of the agent
			model: Model info
			system_prompt: Additional system prompt (will be combined with base prompt)
			seed_prompts: Seed prompts
			inference_config: Inference config
			summarization_config: Summarization config
			scratchpad_config: Scratchpad reasoning config
		"""
  
		assert model is not None, f"Model is required for {name} agent"
		assert system_prompt is not None, f"System prompt is required for {name} agent"
		assert inference_config is not None, f"Inference config is required for {name} agent"
		assert summarization_config is not None, f"Summarization config is required for {name} agent"
  
		self.name = name
		self.model_info = model
		self.seed_prompts = seed_prompts if seed_prompts is not None else []
		
		# Combine base system prompt with agent-specific prompt
		self.full_system_prompt = f"{system_prompt}".strip()
		
		# Chat history for this agent
		self.chat_history: List[Dict[str, Any]] = []
		
		# Context window management (summarization)
		self.summarization_config = summarization_config

		# Inference config
		self.inference_config = inference_config
		
		# Scratchpad reasoning config
		self.scratchpad_config = scratchpad_config or ScratchpadConfig()

		logger.info(f"Initialized agent {self.name}")
	
 
	def get_context_usage(self) -> Tuple[int, float]:
		"""Get current context window usage"""
		# Estimate token count (rough approximation: 1 token ≈ 4 characters)
		total_chars = len(self.full_system_prompt)
		
		for message in self.seed_prompts:
			total_chars += len(str(message))
	
		for message in self.chat_history:
			total_chars += len(str(message))
		
		estimated_tokens = total_chars // self.summarization_config.char_to_token_ratio
		usage_percentage = (estimated_tokens / self.model_info.context_length) * 100
		
		return estimated_tokens, usage_percentage
	
 
	def get_context_display(self) -> str:
		"""Get context usage display string"""
		tokens, percentage = self.get_context_usage()
		return f"[{self.name} {percentage:.1f}%/{self.model_info.context_length}]"

	
	def should_summarize_history(self) -> bool:
		"""Check if we should summarize the chat history"""
		_, usage_percentage = self.get_context_usage()
		return usage_percentage >= (self.summarization_config.summarization_threshold * 100)
	
 
	def summarize_history(self):
		"""Summarize chat history to reduce context window usage"""
  
		# if history takes more than 65% of the context window, summarize it
		# not just the count of messages, but the total size of the history
		if self.get_context_usage()[1] < self.summarization_config.percentage_to_summarize * 100:
			return  # Keep at least recent messages
		
		logger.info(f"{self.get_context_display()} {self.name} summarizing chat history...")
		
		try:
			# keep 40% of the recent history, and summarize the rest
			recent_messages = self.chat_history[-int(len(self.chat_history) * self.summarization_config.percentage_to_summarize):]
			messages_to_summarize = self.chat_history[:-int(len(self.chat_history) * self.summarization_config.percentage_to_summarize)]
			
			if not messages_to_summarize:
				return
			
			# Create summarization prompt
			summary_content = "\n".join([
				f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
				for msg in messages_to_summarize
			])
			
			summary_prompt = SUMMARIZATION_PROMPT.format(summary_content=summary_content)
			
			# Get summary from LLM
			summary_response = self.call_llm(summary_prompt, add_to_history=False)
			
			# Replace old messages with summary
			summary_message = {
				"role": "system",
				"content": f"[CONVERSATION SUMMARY]: {summary_response}",
				"timestamp": time.time(),
				"type": "summary"
			}
			
			self.chat_history = [summary_message] + recent_messages
			
			tokens, percentage = self.get_context_usage()
			logger.success(f"{self.get_context_display()} History summarized - now using {percentage:.1f}% of context window")
			
		except Exception as e:
			logger.error(f"Failed to summarize history for {self.name}: {e}")
	
	def _add_to_history(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
		"""Add message to chat history"""
		message = {
			"role": role,
			"content": content,
			"timestamp": time.time(),
			"metadata": metadata or {}
		}
		
		self.chat_history.append(message)
		
		# Check if we need to summarize
		if self.should_summarize_history():
			self.summarize_history()
   
   
	def send_llm(self, model: ModelInstanceBase, full_prompt: str, inference_config: InferenceConfig) -> str:
		
		# Use non-streaming for non-interactive mode (pipes, etc.)
		logger.ai("thinking...")
		full_response = model.complete(full_prompt, config=inference_config)
		if full_response == '' or full_response is None:
			logger.error(f"Failed to get a response from {self.name} model")
			return ''

		logger.ai(full_response)
   
		return full_response


	def cleanup_response(self, full_response: str) -> str:
		# The response is from "```json" to "```"
		start_marker = "```json"
		end_marker = "```"
		
		start_index = full_response.find(start_marker)
		if start_index == -1:
			# If no JSON marker found, raise an error
			raise ValueError(f"Could not find JSON start marker '{start_marker}' in response")
		
		# Find the start of the JSON content (after the marker)
		json_start = start_index + len(start_marker)
		
		# Find the end marker from the end of the response
		end_index = full_response.rfind(end_marker)
		if end_index == -1:
			# If no end marker found, raise an error
			raise ValueError(f"Could not find JSON end marker '{end_marker}' in response")
		
		# Extract the JSON content between markers
		json_content = full_response[json_start:end_index].strip()
		return json_content


	def _nearly_identical(self, text1: str, text2: str) -> bool:
		"""Check if two texts are nearly identical using difflib"""
		similarity = difflib.SequenceMatcher(None, text1.strip(), text2.strip()).ratio()
		return similarity >= self.scratchpad_config.similarity_threshold


	def _checklist_score(self, checklist: Dict[str, bool]) -> int:
		"""Calculate checklist completeness score"""
		if not checklist:
			return 0
		return sum(1 for value in checklist.values() if value)


	def _llm_refine(self, plan: str, full_context: str, model: ModelInstanceBase) -> Dict[str, Any]:
		"""Call LLM for plan refinement"""
		refine_prompt = SCRATCHPAD_REFINEMENT_PROMPT.format(plan=plan, full_context=full_context)
		
		# Create a temporary inference config for refinement
		refine_config = InferenceConfig(
			max_tokens=self.inference_config.max_tokens,
			temperature=0.3,  # Lower temperature for more focused refinement
			grammar=self.inference_config.grammar,
			schema=self.inference_config.schema,
			stop_strings=self.inference_config.stop_strings
		)
		
		try:
			# Simple messages for refinement
			messages = [
				{"role": "system", "content": "You are a helpful assistant that refines task plans."},
				{"role": "user", "content": refine_prompt}
			]
			
			full_prompt = model.apply_prompt_template(messages)
			full_response = self.send_llm(model, full_prompt, refine_config)
			cleaned_response = self.cleanup_response(full_response)
			
			# Parse the JSON response
			response_json = json.loads(cleaned_response)
			
			# Check if it's a valid REFINEMENT_RESPONSE
			if response_json.get("action") == "REFINEMENT_RESPONSE":
				return response_json
			else:
				raise ValueError("Invalid response format from refinement LLM - expected REFINEMENT_RESPONSE")
			
		except Exception as e:
			logger.error(f"Failed to refine plan: {e}")
			return {
				"new_plan": plan,
				"done": "yes",
				"score": 50,
				"why": "refinement failed",
				"checklist": {"objective": False, "inputs": False, "outputs": False, "constraints": False},
				"success": False
			}


	def _reason_scratchpad(self, initial_prompt: str, full_context: str, model: ModelInstanceBase) -> str:
		"""Perform scratchpad reasoning to refine the initial prompt"""
		if not self.scratchpad_config.enabled:
			return initial_prompt
		
		logger.think(f"Starting scratchpad reasoning for: {initial_prompt[:100]}...")
		
		plan = initial_prompt
		prev = ""
		unchanged = 0
		
		for step in range(self.scratchpad_config.max_iterations):
			logger.think(f"Reasoning step {step + 1}/{self.scratchpad_config.max_iterations}")
			
			resp = self._llm_refine(prev or initial_prompt, full_context, model)
			new_plan = resp.get("new_plan", plan)
			done = resp.get("done", "no")
			score = resp.get("score", 0)
			why = resp.get("why", "")
			checklist = resp.get("checklist", {})
			
			logger.think(f"Step {step + 1}: score={score}, done={done}, why='{why}'")
			logger.think(f"Checklist: {checklist}")
			
			# 0. Model says it's done
			if done == "yes" and score >= self.scratchpad_config.score_lower_bound:
				logger.think(f"Model indicates completion with score {score}")
				plan = new_plan
				break
			
			# 1. Semantic similarity check
			if prev and self._nearly_identical(prev, new_plan):
				logger.think("Plan is nearly identical to previous iteration")
				plan = new_plan
				break
			
			# 2. Unchanged iterations check
			unchanged = unchanged + 1 if prev.strip() == new_plan.strip() else 0
			if unchanged >= self.scratchpad_config.unchanged_limit:
				logger.think(f"Plan unchanged for {unchanged} iterations")
				plan = new_plan
				break
			
			# 3. Checklist completeness
			checklist_max = 4  # objective, inputs, outputs, constraints
			if self._checklist_score(checklist) == checklist_max:
				logger.think("Checklist fully complete")
				plan = new_plan
				break
			
			prev = new_plan
			plan = new_plan
		
		logger.think(f"Scratchpad reasoning complete. Final plan: {plan[:100]}...")
		return plan


	def call_llm(self, prompt: str, add_to_history: bool = True, override_inference_config: Optional[InferenceConfig] = None) -> Dict[str, Any]:
		"""Call the LLM with the current context and stream response with robust error handling"""
		full_response = ""
		inference_config = override_inference_config if override_inference_config is not None else self.inference_config
		
		try:
			# Call LLM using lmstudio package with streaming and robust error handling
			model = ModelsPoolInstance.ensure_model_loaded(self.model_info)
			
			# Create full context for scratchpad reasoning
			full_context = f"System: {self.full_system_prompt}\n\n"
			if self.seed_prompts:
				full_context += "Seed prompts:\n"
				for seed in self.seed_prompts:
					full_context += f"- {seed.get('role', 'unknown')}: {seed.get('content', '')}\n"
				full_context += "\n"
			
			if self.chat_history:
				full_context += "Chat history:\n"
				for msg in self.chat_history:
					full_context += f"- {msg.get('role', 'unknown')}: {msg.get('content', '')}\n"
				full_context += "\n"
			
			full_context += f"Current request: {prompt}"
			
			# Perform scratchpad reasoning first
			refined_prompt = self._reason_scratchpad(prompt, full_context, model)
   
			chat_messages: List[Dict[str, Any]] = [
				{"role": "system", "content": self.full_system_prompt},
				*self.seed_prompts,
				*self.chat_history,       # {"role": .., "content": ..}
				{"role": "user", "content": refined_prompt},
			]

			
			# parse response to JSON and call "handle_response" that is implemented in the child classes
			done = False
			intermediate_prompt = ""
			cleanedup_response = ''
			response_json: Dict[str, Any] = {}
			while not done:
				try:
					# if there's an intermediate response (fixup or future CoT)
					if intermediate_prompt != '':
						chat_messages.append({"role": "user", "content": intermediate_prompt})
						
					# apply model's prompt template
					full_prompt = model.apply_prompt_template(chat_messages)
        
					full_response = self.send_llm(model, full_prompt, inference_config)
					cleanedup_response = self.cleanup_response(full_response)
				
					response_json = json.loads(cleanedup_response)

					done = True
				except json.JSONDecodeError as e:
					logger.error(f"Failed to parse response to JSON!!!: {e}\nFailed JSON:\n{cleanedup_response}")
					intermediate_prompt = '\n\nThe JSON block you provided is malformed! Write right it correctly!!!'
				except ValueError as e:
					logger.error(f"I failed to find a json block within '```json' and '```'. Here's the error:  {e}\ndid you forget that?")
					intermediate_prompt = f'\n\nDid you forgot you MUST respond with a JSON within a code block?\n\n'
				except InvalidTaskStructureError as e:
					logger.error(f"Invalid task structure: {e}")
					intermediate_prompt = '\n\nFix the JSON!'
			
			if add_to_history:
				self._add_to_history("user", prompt)  # Store original prompt, not refined
				self._add_to_history("assistant", cleanedup_response)
	   
			return response_json
			
		except KeyboardInterrupt:
			logger.warning("\n[Interrupted by user]")
			from agents.prompts import PromptType
			return {"action": PromptType.NORMAL_RESPONSE, "response": "I was interrupted. Please try again or type 'quit' to exit."}
				
			
	
	