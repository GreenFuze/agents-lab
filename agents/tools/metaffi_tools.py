import os
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool

from agents.prompts import tool_return_prompt
from tools.get_func_name import *
from tools.file_tools import execute_command


def get_metaffi_absolute_root_source_path() -> tool_return_prompt:
	"""Get MetaFFI absolute root source directory path"""
	return tool_return_prompt({'action':'TOOL_RETURN',
							'tool': get_current_function_name(),
							'result':f'{str(Path("C:\\src\\github.com\\MetaFFI").resolve())}',
							'success':'True'})
 

def get_metaffi_build_path(platform: str, build_type: str) -> tool_return_prompt:
	"""
	Get MetaFFI relative build directory path
	Args:
		platform: Platform name ("windows", "linux")
		build_type: Build type ("debug", "relwithdebinfo")
	Returns:
		Relative path to MetaFFI build directory
	"""
	if platform == "windows":
		platform = ""
	elif platform == "linux":
		platform = "-wsl-2404"
	else:
		return tool_return_prompt({'action':'TOOL_RETURN',
							'tool': get_current_function_name(),
							'result':f"You have requested an invalid platform: {platform}. Please choose from 'windows' or 'linux'",
							'success':'False'})
	
	if build_type != "debug" and build_type != "relwithdebinfo":
		return tool_return_prompt({'action':'TOOL_RETURN',
							'tool': get_current_function_name(),
							'result':f"You have requested an invalid build type: {build_type}. Please choose from 'debug' or 'relwithdebinfo'",
							'success':'False'})
	
	return tool_return_prompt({'action': 'TOOL_RETURN',
							'tool': get_current_function_name(),
							'result': f"/cmake-build{platform}-{build_type}",
							'success': 'True'})


def get_metaffi_output_path(platform: str, build_type: str, architecture: str = "x64") -> tool_return_prompt:
	"""
	Get MetaFFI relative output directory path
	Args:
		platform: Platform name ("windows", "linux")
		build_type: Build type ("debug", "relwithdebinfo")
	Returns:
		Relative path to MetaFFI output directory
	"""
	if platform == "windows":
		platform = "windows"
	elif platform == "linux":
		platform = "ubuntu"
	else:
		return tool_return_prompt({'action':'TOOL_RETURN',
							'tool': get_current_function_name(),
							'result':f"You have requested an invalid platform: {platform}. Please choose from 'windows' or 'linux'",
							'success':'False'})
	
	if build_type != "debug" and build_type != "relwithdebinfo":
		return tool_return_prompt({'action':'TOOL_RETURN',
							'tool': get_current_function_name(),
							'result':f"You have requested an invalid build type: {build_type}. Please choose from 'debug' or 'relwithdebinfo'",
							'success':'False'})
	
	if build_type == "debug":
		build_type = "Debug"
	elif build_type == "relwithdebinfo":
		build_type = "RelWithDebInfo"
	
	if architecture != 'x86' and architecture != 'x64' and architecture != 'arm64':
		return tool_return_prompt({'action':'TOOL_RETURN',
							'tool': get_current_function_name(),
							'result': f"You have requested an invalid architecture: {architecture}. Please choose from 'x86', 'x64' or 'arm64'",
							'success':'False'})
	
	return tool_return_prompt({'action':'TOOL_RETURN',
							'tool': get_current_function_name(),
							'result': f"/output/{platform}/{architecture}/{build_type}/",
							'success':'True'})


def get_list_of_metaffi_targets() -> tool_return_prompt:
	"""
	Get list of MetaFFI targets
	"""
	# execute build_target.py --list, print output to console, but also return the output.
	# append the exit code to the output
	metaffi_root = str(Path("C:\\src\\github.com\\MetaFFI").resolve())
	build_script = os.path.join(metaffi_root, "build_target.py")
	
	# Prepare command arguments
	cmd = [build_script, "--list"]
	
	return execute_command('get_list_of_metaffi_targets', cmd, metaffi_root)
	
	
def build_metaffi_target(target: str, build_type: str, is_clean: bool) -> tool_return_prompt:
	"""
	Build MetaFFI target.
 	The target "MetaFFI" the whole project
	Args:
		target: Target name
		build_type: Build type ("debug", "relwithdebinfo")
		is_clean: Whether to clean the build directory
	"""
	# execute build_target.py, print output to console, but also return the output.
	# append the exit code to the output
	
	metaffi_root = str(Path("C:\\src\\github.com\\MetaFFI").resolve())
	build_script = os.path.join(metaffi_root, "build_target.py")
	
	# if windows (not "nt") - it should run "py", in linux - it should run "python3"
	import platform
	system = platform.system()
	if system == "Windows":
		exec_name = "py"
	else:
		exec_name = "python3"
 
	# Prepare command arguments
	cmd = [exec_name, build_script, target]
	
	# Add build type argument
	if build_type.lower() == "debug":
		cmd.extend(["--build-type", "Debug"])
	elif build_type.lower() == "relwithdebinfo":
		cmd.extend(["--build-type", "RelWithDebInfo"])
	else:
		return tool_return_prompt({'action':'TOOL_RETURN',
							'tool': get_current_function_name(),
							'result': f"You have requested an invalid build type: {build_type}. Please choose from 'debug' or 'relwithdebinfo'.",
							'success':'False'})
	
	# Add clean flag if requested
	if is_clean:
		cmd.append("--clean")
	
	# Add verbose flag for detailed output
	cmd.append("--verbose")
	
	return execute_command(get_current_function_name(), cmd, metaffi_root)
	
	
def get_list_of_metaffi_tests() -> tool_return_prompt:
	"""
	Get list of MetaFFI tests
	""" 
 
	metaffi_root = str(Path("C:\\src\\github.com\\MetaFFI").resolve())
 
	# Prepare command arguments
	cmd = ['ctest', "--test-dir", 'cmake-build-debug', '--show-only']
	
	return execute_command(get_current_function_name(), cmd, metaffi_root)


def run_metaffi_test(test_name: Optional[str] = None) -> tool_return_prompt:
	"""
	Run MetaFFI test
	Args:
		test_name (optional): Test name to run. If not provided, all tests will be run.
	"""
	
	metaffi_root = str(Path("C:\\src\\github.com\\MetaFFI").resolve())
	build_path_res = get_metaffi_build_path("windows", "debug")
	
	if not build_path_res.success_bool:
		return build_path_res

	build_path = build_path_res.result
 
	# remove any trailing slash (/ or \)
	build_path = build_path.lstrip('/').lstrip('\\')
 
	if test_name:
		cmd = ['ctest', "--test-dir", build_path, '-R', test_name, '--output-on-failure']
	else:
		cmd = ['ctest', "--test-dir", build_path, '--output-on-failure']
	
	return execute_command(get_current_function_name(), cmd, metaffi_root)
	
	
	