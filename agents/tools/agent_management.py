import os
import json
import yaml
from typing import List, Dict, Any, Optional
from agents.prompts import PromptType, tool_return_prompt
from models.models_pool import ModelsPoolInstance
from utils import logger


def get_available_models() -> tool_return_prompt:
	"""
	Get all available models from the models pool.
	Returns:
		List of available model names with their details
	"""
	logger.log("[LOG] Getting available models")
	
	try:
		models = ModelsPoolInstance.get_all_models()
		model_list = []
		
		for model_name, model_info in models.items():
			model_details = {
				"name": model_name,
				"backend": model_info.backend_info.name,
				"context_length": model_info.context_length,
				"gpu_ratio": model_info.gpu_ratio,
				"key": model_info.key
			}
			model_list.append(model_details)
		
		result = json.dumps(model_list, indent=2)
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'get_available_models',
			'result': result,
			'success': 'True'
		})
		
	except Exception as e:
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'get_available_models',
			'result': f'Error getting models: {str(e)}',
			'success': 'False'
		})


def get_available_tools() -> tool_return_prompt:
	"""
	Get all available tools by parsing the tools directory.
	Returns:
		List of available tools in module.function format
	"""
	logger.log("Getting available tools")
	
	try:
		tools_dir = os.path.dirname(__file__)
		available_tools = []
		
		# Get all Python files in the tools directory
		for filename in os.listdir(tools_dir):
			if filename.endswith('.py') and filename != '__init__.py':
				module_name = filename[:-3]  # Remove .py extension
				module_path = os.path.join(tools_dir, filename)
				
				# Import the module to get its functions
				import importlib.util
				spec = importlib.util.spec_from_file_location(f"agents.tools.{module_name}", module_path)
				if spec is None or spec.loader is None:
					continue
					
				module = importlib.util.module_from_spec(spec)
				spec.loader.exec_module(module)
				
				# Get all callable functions that return tool_return_prompt
				import inspect
				for name, obj in inspect.getmembers(module):
					if inspect.isfunction(obj) and not name.startswith('_'):
						# Check if function returns tool_return_prompt
						sig = inspect.signature(obj)
						if sig.return_annotation is tool_return_prompt:
							tool_name = f"{module_name}.{name}"
							
							# Get function documentation
							doc = obj.__doc__ or "No description available"
							doc_first_line = doc.strip().split('\n')[0]
							
							available_tools.append({
								"name": tool_name,
								"description": doc_first_line,
								"module": module_name,
								"function": name
							})
		
		result = json.dumps(available_tools, indent=2)
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'get_available_tools',
			'result': result,
			'success': 'True'
		})
		
	except Exception as e:
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'get_available_tools',
			'result': f'Error getting tools: {str(e)}',
			'success': 'False'
		})


def get_available_prompts() -> tool_return_prompt:
	"""
	Get all available prompt files from the prompts directory.
	Returns:
		List of available prompt files
	"""
	logger.log("Getting available prompts")
	
	try:
		prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
		available_prompts = []
		
		if os.path.exists(prompts_dir):
			for filename in os.listdir(prompts_dir):
				if filename.endswith('.md'):
					filepath = os.path.join(prompts_dir, filename)
					file_size = os.path.getsize(filepath)
					
					available_prompts.append({
						"filename": filename,
						"path": f"prompts/{filename}",
						"size_bytes": file_size
					})
		
		result = json.dumps(available_prompts, indent=2)
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'get_available_prompts',
			'result': result,
			'success': 'True'
		})
		
	except Exception as e:
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'get_available_prompts',
			'result': f'Error getting prompts: {str(e)}',
			'success': 'False'
		})


def get_existing_agents() -> tool_return_prompt:
	"""
	Get all existing agents from agents.yaml.
	Returns:
		List of existing agent names and their basic info
	"""
	logger.log("Getting existing agents")
	
	try:
		agents_yaml_path = os.path.join(os.path.dirname(__file__), '..', 'agents.yaml')
		
		if not os.path.exists(agents_yaml_path):
			return tool_return_prompt({
				'action': PromptType.TOOL_RETURN.value,
				'tool': 'get_existing_agents',
				'result': 'agents.yaml file not found',
				'success': 'False'
			})
		
		with open(agents_yaml_path, 'r') as file:
			agents_config = yaml.safe_load(file)
		
		# Get the agents dictionary from the config
		agents_dict = agents_config.get('agents', {})
		
		existing_agents = []
		for agent_name, agent_config in agents_dict.items():
			agent_info = {
				"name": agent_name,
				"model": agent_config.get('model', 'unknown'),
				"tools": agent_config.get('tools', []),
				"prompts": agent_config.get('prompts', [])
			}
			existing_agents.append(agent_info)
		
		result = json.dumps(existing_agents, indent=2)
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'get_existing_agents',
			'result': result,
			'success': 'True'
		})
		
	except Exception as e:
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'get_existing_agents',
			'result': f'Error getting existing agents: {str(e)}',
			'success': 'False'
		})


def create_agent_prompt_file(agent_name: str, prompt_content: str) -> tool_return_prompt:
	"""
	Create a new prompt file for an agent.
	Args:
		agent_name: Name of the agent
		prompt_content: Content of the prompt file
	Returns:
		Result of the operation
	"""
	logger.log(f"Creating prompt file for agent: {agent_name}")
	
	try:
		prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
		
		# Ensure prompts directory exists
		os.makedirs(prompts_dir, exist_ok=True)
		
		# Create the prompt file
		prompt_filename = f"{agent_name}.md"
		prompt_path = os.path.join(prompts_dir, prompt_filename)
		
		with open(prompt_path, 'w', encoding='utf-8') as f:
			f.write(prompt_content)
		
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'create_agent_prompt_file',
			'result': f'Prompt file created: prompts/{prompt_filename}',
			'success': 'True'
		})
		
	except Exception as e:
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'create_agent_prompt_file',
			'result': f'Error creating prompt file: {str(e)}',
			'success': 'False'
		})


def create_seed_prompts_file(agent_name: str, seed_prompts: str) -> tool_return_prompt:
	"""
	Create a seed prompts JSON file for an agent.
	Args:
		agent_name: Name of the agent
		seed_prompts: JSON string containing seed prompts
	Returns:
		Result of the operation
	"""
	logger.log(f"Creating seed prompts file for agent: {agent_name}")
	
	try:
		seeds_dir = os.path.join(os.path.dirname(__file__), '..', 'seeds')
		
		# Ensure seeds directory exists
		os.makedirs(seeds_dir, exist_ok=True)
		
		# Validate JSON
		try:
			json.loads(seed_prompts)
		except json.JSONDecodeError:
			return tool_return_prompt({
				'action': PromptType.TOOL_RETURN.value,
				'tool': 'create_seed_prompts_file',
				'result': 'Invalid JSON format for seed prompts',
				'success': 'False'
			})
		
		# Create the seed prompts file
		seed_filename = f"{agent_name}.json"
		seed_path = os.path.join(seeds_dir, seed_filename)
		
		with open(seed_path, 'w', encoding='utf-8') as f:
			f.write(seed_prompts)
		
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'create_seed_prompts_file',
			'result': f'Seed prompts file created: seeds/{seed_filename}',
			'success': 'True'
		})
		
	except Exception as e:
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'create_seed_prompts_file',
			'result': f'Error creating seed prompts file: {str(e)}',
			'success': 'False'
		})


def add_agent(agent_name: str, model: str, prompts: str, tools: str, 
              temperature: float, max_tokens: int, stop_strings: str,
              summarization_threshold: float, percentage_to_summarize: float, 
              char_to_token_ratio: int, schema: Optional[str] = None, grammar: Optional[str] = None, 
              seed_prompts_file: Optional[str] = None, scratchpad_enabled: bool = True,
              scratchpad_max_iterations: int = 5, scratchpad_score_lower_bound: int = 70,
              scratchpad_similarity_threshold: float = 0.9, scratchpad_unchanged_limit: int = 2) -> tool_return_prompt:
	"""
	Add a new agent configuration to agents.yaml.
	Args:
		agent_name: Name of the new agent
		model: Model name to use
		prompts: Comma-separated list of prompt files
		tools: Comma-separated list of tools in module.function format
		temperature: Temperature for inference
		max_tokens: Maximum tokens for inference
		stop_strings: Comma-separated list of stop strings
		summarization_threshold: Threshold for summarization (0.0-1.0)
		percentage_to_summarize: Percentage of history to summarize (0.0-1.0)
		char_to_token_ratio: Character to token ratio for estimation
		schema: Optional schema file path
		grammar: Optional grammar file path
		seed_prompts_file: Optional seed prompts file path
		scratchpad_enabled: Enable scratchpad reasoning (default: True)
		scratchpad_max_iterations: Maximum reasoning iterations (default: 5)
		scratchpad_score_lower_bound: Minimum score for completion (default: 70)
		scratchpad_similarity_threshold: Similarity threshold for convergence (default: 0.9)
		scratchpad_unchanged_limit: Max unchanged iterations before stopping (default: 2)
	Returns:
		Result of the operation
	"""
	logger.log(f"Adding agent to agents.yaml: {agent_name}")
	
	try:
		agents_yaml_path = os.path.join(os.path.dirname(__file__), '..', 'agents.yaml')
		
		# Read existing agents.yaml
		existing_config = {}
		if os.path.exists(agents_yaml_path):
			with open(agents_yaml_path, 'r') as file:
				existing_config = yaml.safe_load(file) or {}
		
		# Ensure agents key exists
		if 'agents' not in existing_config:
			existing_config['agents'] = {}
		
		# Check if agent already exists
		if agent_name in existing_config['agents']:
			return tool_return_prompt({
				'action': PromptType.TOOL_RETURN.value,
				'tool': 'add_agent',
				'result': f'Agent {agent_name} already exists in agents.yaml',
				'success': 'False'
			})
		
		# Parse comma-separated lists
		prompts_list = [p.strip() for p in prompts.split(',') if p.strip()]
		tools_list = [t.strip() for t in tools.split(',') if t.strip()]
		stop_strings_list = [s.strip() for s in stop_strings.split(',') if s.strip()]
		
		# Build agent configuration
		agent_config = {
			'model': model,
			'seed_prompts_file': seed_prompts_file,
			'grammar': grammar,
			'schema': schema,
			'inference_config': {
				'temperature': temperature,
				'max_tokens': max_tokens,
				'stop_strings': stop_strings_list if stop_strings_list else None
			},
			'summarization_config': {
				'summarization_threshold': summarization_threshold,
				'percentage_to_summarize': percentage_to_summarize,
				'char_to_token_ratio': char_to_token_ratio
			},
			'scratchpad_config': {
				'enabled': scratchpad_enabled,
				'max_iterations': scratchpad_max_iterations,
				'score_lower_bound': scratchpad_score_lower_bound,
				'similarity_threshold': scratchpad_similarity_threshold,
				'unchanged_limit': scratchpad_unchanged_limit
			},
			'prompts': prompts_list,
			'tools': tools_list if tools_list else None
		}
		
		# Remove None values to keep YAML clean
		def remove_none_values(d):
			if isinstance(d, dict):
				return {k: remove_none_values(v) for k, v in d.items() if v is not None}
			return d
		
		agent_config = remove_none_values(agent_config)
		
		# Add the new agent
		existing_config['agents'][agent_name] = agent_config
		
		# Write back to file with proper formatting
		with open(agents_yaml_path, 'w') as file:
			yaml.dump(existing_config, file, default_flow_style=False, sort_keys=False, indent=4)
		
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'add_agent',
			'result': f'Agent {agent_name} successfully added to agents.yaml',
			'success': 'True'
		})
		
	except Exception as e:
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'add_agent',
			'result': f'Error adding agent to agents.yaml: {str(e)}',
			'success': 'False'
		})


def check_schema_file_exists(schema_path: str) -> tool_return_prompt:
	"""
	Check if a schema file exists.
	Args:
		schema_path: Path to the schema file (relative to agents directory)
	Returns:
		Result indicating if the file exists
	"""
	logger.log(f"Checking schema file: {schema_path}")
	
	try:
		full_path = os.path.join(os.path.dirname(__file__), '..', schema_path)
		exists = os.path.exists(full_path)
		
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'check_schema_file_exists',
			'result': f'Schema file {schema_path} exists: {exists}',
			'success': 'True'
		})
		
	except Exception as e:
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'check_schema_file_exists',
			'result': f'Error checking schema file: {str(e)}',
			'success': 'False'
		})


def check_grammar_file_exists(grammar_path: str) -> tool_return_prompt:
	"""
	Check if a grammar file exists.
	Args:
		grammar_path: Path to the grammar file (relative to agents directory)
	Returns:
		Result indicating if the file exists
	"""
	logger.log(f"Checking grammar file: {grammar_path}")
	
	try:
		full_path = os.path.join(os.path.dirname(__file__), '..', grammar_path)
		exists = os.path.exists(full_path)
		
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'check_grammar_file_exists',
			'result': f'Grammar file {grammar_path} exists: {exists}',
			'success': 'True'
		})
		
	except Exception as e:
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': 'check_grammar_file_exists',
			'result': f'Error checking grammar file: {str(e)}',
			'success': 'False'
		}) 