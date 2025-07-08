import os
import importlib.util
import inspect
from typing import Any
from agents.prompts import tool_return_prompt, PromptType


def _convert_value_to_type(value: str, target_type) -> Any:
	"""Convert string value to the target type."""
	if target_type == bool:
		# Handle boolean conversion
		if value.lower() in ('true', '1', 'yes', 'on'):
			return True
		elif value.lower() in ('false', '0', 'no', 'off'):
			return False
		else:
			raise ValueError(f"Cannot convert '{value}' to boolean")
	elif target_type == int:
		return int(value)
	elif target_type == float:
		return float(value)
	elif target_type == str:
		return value
	else:
		# For other types, return as string (could be extended for more types)
		return value


def run_tool(name: str, args: str) -> tool_return_prompt:
	# Parse tool name to get module and function
	if '.' not in name:
		raise ValueError(f"Invalid tool name format: {name}. Expected format: 'module.function'")
	
	module_name, function_name = name.split('.', 1)
	
	# Load the tool module
	tools_dir = os.path.join(os.path.dirname(__file__))
	module_file = os.path.join(tools_dir, f"{module_name}.py")
	
	if not os.path.exists(module_file):
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': name,
			'result': f'Tool module not found: {module_file}',
			'success': 'False'
		})
	
	try:
		# Import the module dynamically
		spec = importlib.util.spec_from_file_location(f"agents.tools.{module_name}", module_file)
		if spec is None or spec.loader is None:
			return tool_return_prompt({
				'action': PromptType.TOOL_RETURN.value,
				'tool': name,
				'result': f'Could not load spec for {module_name}',
				'success': 'False'
			})
		
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		
		# Get the function from the module
		if not hasattr(module, function_name):
			return tool_return_prompt({
				'action': PromptType.TOOL_RETURN.value,
				'tool': name,
				'result': f'Function {function_name} not found in module {module_name}',
				'success': 'False'
			})
		
		tool_func = getattr(module, function_name)
		
		# Parse args string in format "arg1=value1,arg2=value2,..."
		parsed_args = {}
		if args.strip():
			for arg_pair in args.split(','):
				arg_pair = arg_pair.strip()
				if '=' in arg_pair:
					key, value = arg_pair.split('=', 1)
					parsed_args[key.strip()] = value.strip()
		
		# Get tool's signature to match parameters by name
		sig = inspect.signature(tool_func)
		bound_args = {}
		
		for param_name, param in sig.parameters.items():
			if param_name in parsed_args:
				# Convert string value to proper type based on annotation
				value = parsed_args[param_name]
				if param.annotation != inspect.Parameter.empty:
					bound_args[param_name] = _convert_value_to_type(value, param.annotation)
				else:
					bound_args[param_name] = value
			elif param.default != inspect.Parameter.empty:
				bound_args[param_name] = param.default
			else:
				raise ValueError(f"Missing required argument: {param_name}")
		
		# Call the tool with matched arguments
		return tool_func(**bound_args)
		
	except Exception as e:
		return tool_return_prompt({
			'action': PromptType.TOOL_RETURN.value,
			'tool': name,
			'result': f'Error executing tool: {str(e)}',
			'success': 'False'
		})