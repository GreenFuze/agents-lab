import subprocess
import os
from langchain_core.tools import tool
from agents.prompts import tool_return_prompt
from utils import logger

def read_file(path: str) -> tool_return_prompt:
	"""
	Reads a file from a given path and returns its contents.
	Args:
		path: Path to the file to read
	Returns:
		Contents of the file
	"""
	logger.log(f"[LOG] I am reading a file: {path}")
	
	if not os.path.exists(path):
		return tool_return_prompt({'action':'TOOL_RETURN', 'tool':'read_file', 'result':'File not found', 'success':'False'})
	try:
		data = open(path, encoding="utf-8").read()
		return tool_return_prompt({'action':'TOOL_RETURN', 'tool':'read_file', 'result':f'{data}', 'success':'True'})
	except Exception as e:
		return tool_return_prompt({'action':'TOOL_RETURN', 'tool':'read_file', 'result':f'{e}', 'success':'False'})

def write_file(path: str, data: str) -> tool_return_prompt:
	"""
	Writes data to a file at a given path.
	Args:
		path: Path to the file to write to
		data: Data to write to the file
	Returns:
		Result of the operation
	"""
	logger.log(f"[LOG] I am writing to a file: {path}")
	
	if not os.path.exists(path):
		return tool_return_prompt({'action':'TOOL_RETURN', 'tool':'write_file', 'result':'File not found', 'success':'False'})
	
	try:
		with open(path, 'w', encoding="utf-8") as f:
			f.write(data)
		return tool_return_prompt({'action':'TOOL_RETURN', 'tool':'write_file', 'result':'File written successfully', 'success':'True'})
	except Exception as e:
		return tool_return_prompt({'action':'TOOL_RETURN', 'tool':'write_file', 'result':f'{e}', 'success':'False'})

def execute_command(tool_name: str, cmd: list[str], cwd: str) -> tool_return_prompt:
	"""
	Execute a command and return the output.
	Args:
		cmd: Command to execute
	Returns:
		Output of the command
	"""
	# Spawn the child: one pipe, text-mode, line-buffered
	proc = subprocess.Popen(
		cmd,
		cwd=cwd,
		stdout=subprocess.PIPE,      # <-- makes proc.stdout a TextIO object
		stderr=subprocess.STDOUT,    # merge stderr into that same pipe
		text=True,                   # give us str, not bytes
		bufsize=1                    # line-buffered (needs text=True)
	)
 
	assert proc.stdout is not None

	captured = []

	# .stdout is guaranteed not-None now; iterate line-by-line
	for line in proc.stdout:        # same as iter(proc.stdout.readline, '')
		print(line, end='')         # real-time console echo
		captured.append(line)       # keep a copy

	proc.stdout.close()             # allow child to detect closed pipe
	proc.wait()                     # reap the child

	res = tool_return_prompt()
	res.success = "True" if proc.returncode == 0 else "False"
	res.result = ''.join(captured)
	res.tool = tool_name

	return res
