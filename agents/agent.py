from typing import Dict, List, Optional, Any, Tuple
import json
import time

from models.bases import InferenceConfig, ModelInfo, ModelInstanceBase, SummarizationConfig
from agents.exceptions import *
from models.models_pool import ModelsPoolInstance
import utils.logger as logger


class Agent:
	def __init__(self, name: str,
              		   model: ModelInfo,
                   	   system_prompt: str,
                       seed_prompts: Optional[list[dict[str, str]]],
                       inference_config: InferenceConfig,
                       summarization_config: SummarizationConfig):
		"""
		Initialize the base agent
		
		Args:
			name: Name of the agent
			model: Model info
			system_prompt: Additional system prompt (will be combined with base prompt)
			seed_prompts: Seed prompts
			inference_config: Inference config
			summarization_config: Summarization config
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
			
			summary_prompt = f"""
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


	def call_llm(self, prompt: str, add_to_history: bool = True, override_inference_config: Optional[InferenceConfig] = None) -> Dict[str, Any]:
		"""Call the LLM with the current context and stream response with robust error handling"""
		full_response = ""
		inference_config = override_inference_config if override_inference_config is not None else self.inference_config
		
		try:
			# Call LLM using lmstudio package with streaming and robust error handling
			model = ModelsPoolInstance.ensure_model_loaded(self.model_info)
   
			chat_messages: List[Dict[str, Any]] = [
				{"role": "system", "content": self.full_system_prompt},
				*self.seed_prompts,
				*self.chat_history,       # {"role": .., "content": ..}
				{"role": "user", "content": prompt},
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
				self._add_to_history("user", prompt)
				self._add_to_history("assistant", cleanedup_response)
	   
			return response_json
			
		except KeyboardInterrupt:
			logger.warning("\n[Interrupted by user]")
			from agents.prompts import PromptType
			return {"action": PromptType.NORMAL_RESPONSE, "response": "I was interrupted. Please try again or type 'quit' to exit."}
				
			
	
	