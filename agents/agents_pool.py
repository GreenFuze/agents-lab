import json
from typing import Dict
from agents.agent import Agent
from agents.exceptions import *
from models.bases import InferenceConfig, SummarizationConfig
from models.models_pool import ModelsPoolInstance
import os
import yaml

from utils import logger

class AgentsPool:
	def __init__(self, agents_config_file: str):
		self.pool: Dict[str, Agent] = {}
		self.agents_config_file = agents_config_file
		self._load_agents_config()

	def get_agent(self, name: str) -> Agent:
		if name not in self.pool:
			raise AgentNotFound(f"Agent {name} not found")
		return self.pool[name]

	def add_agent(self, name: str, agent: Agent):
		self.pool[name] = agent

	def _load_agents_config(self):
		with open(self.agents_config_file, 'r') as file:
			agents_config = yaml.safe_load(file)

		# Get the agents dictionary from the config
		agents_dict = agents_config.get('agents', {})
		if not agents_dict:
			logger.warning("No agents found in agents.yaml or 'agents' key missing")

		for agent_name, agent_config in agents_dict.items():
			# Get model from models pool
			model_name = agent_config['model']
			model_info = ModelsPoolInstance.get_model_by_name(model_name)
			
			# Load prompts
			system_prompt = self._load_prompts(agent_config.get('prompts'))
			assert system_prompt is not None, f"No system prompt for agent {agent_name}. Please add at least one prompt to the 'prompts' field in the agents.yaml file."
			
			# Load seed prompts if specified
			seed_prompts = None
			if agent_config.get('seed_prompts_file'):
				seed_prompts = self._load_seed_prompts(agent_config['seed_prompts_file'])
			
			# Load tools if specified and append to system prompt
			if agent_config.get('tools'):
				tools_prompt = self._load_tools(agent_config['tools'])
				if tools_prompt:
					system_prompt += "\n\n" + tools_prompt
   
			# Create inference config
			inference_config_data = agent_config.get('inference_config')
			assert inference_config_data is not None, f"No inference config for agent {agent_name}. Please add an 'inference_config' field in the agents.yaml file."
			
			inference_config = InferenceConfig(
				max_tokens=inference_config_data.get('max_tokens'),
				temperature=inference_config_data.get('temperature'),
				grammar=agent_config.get('grammar'),
				schema=agent_config.get('schema'),
				stop_strings=inference_config_data.get('stop_strings')
			)
   
			assert inference_config.max_tokens is not None, f"Max tokens not specified for agent {agent_name}. Please add a 'max_tokens' field in the inference_config section of the agents.yaml file."
			assert inference_config.temperature is not None, f"Temperature not specified for agent {agent_name}. Please add a 'temperature' field in the inference_config section of the agents.yaml file."
			
			# Create summarization config
			summarization_config_data = agent_config.get('summarization_config')
			assert summarization_config_data is not None, f"No summarization config for agent {agent_name}. Please add a 'summarization_config' field in the agents.yaml file."
			
			summarization_config = SummarizationConfig(
				summarization_threshold=summarization_config_data.get('summarization_threshold'),
				char_to_token_ratio=summarization_config_data.get('char_to_token_ratio'),
				percentage_to_summarize=summarization_config_data.get('percentage_to_summarize')
			)
   
			assert summarization_config.summarization_threshold is not None, f"Summarization threshold not specified for agent {agent_name}. Please add a 'summarization_threshold' field in the summarization_config section of the agents.yaml file."
			assert summarization_config.char_to_token_ratio is not None, f"Char to token ratio not specified for agent {agent_name}. Please add a 'char_to_token_ratio' field in the summarization_config section of the agents.yaml file."
			assert summarization_config.percentage_to_summarize is not None, f"Percentage to summarize not specified for agent {agent_name}. Please add a 'percentage_to_summarize' field in the summarization_config section of the agents.yaml file."
			
			# Create agent instance
			agent = Agent(
				name=agent_name,
				model=model_info,
				system_prompt=system_prompt,
				seed_prompts=seed_prompts,
				inference_config=inference_config,
				summarization_config=summarization_config
			)
			
			# Add to pool
			self.pool[agent_name] = agent

	def _load_tools(self, tools_config: list) -> str:
		"""Load tools from file and return tool prompts"""
		from agents.tools.tool_descriptor import tools_to_prompt
		from agents.prompts import tool_return_prompt
		import importlib.util
		import sys
		import inspect
		
		if not tools_config:
			return ""
		
		tools_dir = os.path.join(os.path.dirname(__file__), 'tools')
		callables = []
		
		for tool_path in tools_config:
			# Parse tool path like "file_tools.write_file"
			if '.' not in tool_path:
				raise ValueError(f"Invalid tool path format: {tool_path}. Expected format: 'module.function' in the tools directory")

			module_name, function_name = tool_path.split('.', 1)
			module_file = os.path.join(tools_dir, f"{module_name}.py")
			if not os.path.exists(module_file):
				raise FileNotFoundError(f"Tool module not found: {module_file}")

			spec = importlib.util.spec_from_file_location(f"agents.tools.{module_name}", module_file)
			if spec is None or spec.loader is None:
				raise ImportError(f"Could not load spec for {module_name}")

			module = importlib.util.module_from_spec(spec)
			sys.modules[f"agents.tools.{module_name}"] = module
			spec.loader.exec_module(module)
			if not hasattr(module, function_name):
				raise AttributeError(f"Function '{function_name}' not found in module '{module_name}'")

			func = getattr(module, function_name)
			# Check return annotation
			sig = inspect.signature(func)

			if sig.return_annotation is not tool_return_prompt:
				logger.warning(f"Tool '{tool_path}' does not return 'tool_return_prompt', skipping.")
				continue

			callables.append(func)

		return tools_to_prompt(callables, heading="AVAILABLE TOOLS")

	def _load_prompts(self, prompt_files: list) -> str:
		"""Load and combine prompt files into a single system prompt"""
		if not prompt_files:
			return ""
		
		agents_dir = os.path.dirname(__file__)
		combined_prompt = ""
		
		for prompt_file in prompt_files:
			# If the path already starts with 'prompts/', use it as-is
			if prompt_file.startswith('prompts/'):
				prompt_path = os.path.join(agents_dir, prompt_file)
			else:
				# Otherwise, assume it's relative to the prompts directory
				prompt_path = os.path.join(agents_dir, 'prompts', prompt_file)
			
			if os.path.exists(prompt_path):
				with open(prompt_path, 'r', encoding='utf-8') as f:
					combined_prompt += f.read() + "\n\n"
			else:
				raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
		
		return combined_prompt.strip()


	def _load_seed_prompts(self, seed_prompts_file: str) -> list:
		"""Load seed prompts from file"""
		if not seed_prompts_file:
			return []
		
		seeds_dir = os.path.join(os.path.dirname(__file__), 'seeds')
		seed_path = os.path.join(seeds_dir, seed_prompts_file)
		
		if not os.path.exists(seed_path):
			raise FileNotFoundError(f"Seed prompts file not found: {seed_path}")
		
		with open(seed_path, 'r', encoding='utf-8') as f:
			seed_prompts = json.load(f)
		
		return seed_prompts

# load agents.yaml in the same directory as this file
CurrentAgentsPool = AgentsPool(os.path.join(os.path.dirname(__file__), 'agents.yaml'))


