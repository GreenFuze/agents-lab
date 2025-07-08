import inspect
from typing import Callable, Iterable

def tools_to_prompt(
	tools: Iterable[Callable],
	*,
	heading: str | None = None,
	sep: str = "\n\n",
) -> str:
	"""
	Convert a list/iterable of callables (plain or @tool-wrapped) into a single
	prompt-friendly string.

	Parameters
	----------
	tools   : iterable of callables (@tool objects or plain functions)
	heading : optional first line (e.g. "Available tools:")
	sep     : separator between tool blocks (default: blank line)

	Returns
	-------
	str
		A human-readable description of all tools, ready to embed in a prompt.
	"""

	def _describe(func: Callable) -> str:
		sig = inspect.signature(getattr(func, "fn", func))
		base_name = getattr(func, "name", func.__name__)
		
		# Get module name and create full tool name
		module_name = func.__module__
		if module_name.startswith('agents.tools.'):
			# Extract just the module name without the full path
			module_short_name = module_name.split('.')[-1]
			name = f"{module_short_name}.{base_name}"
		else:
			name = base_name
			
		doc  = (getattr(func, "description", "") or func.__doc__ or "").strip().split("\n")[0] \
			   or "No description provided."

		# Build argument list
		arg_lines = []
		for p in sig.parameters.values():
			if p.name == "self":
				continue
			ann = p.annotation if p.annotation is not inspect._empty else "Any"
			ann_name = ann.__name__ if hasattr(ann, "__name__") else str(ann) # type: ignore
			if p.default is inspect._empty:
				arg_lines.append(f"  - {p.name} ({ann_name})")
			else:
				arg_lines.append(f"  - {p.name} ({ann_name}, default={p.default!r})")

		arg_block = "\n".join(arg_lines) or "  (no arguments)"
		return f"Tool: {name}\nDescription: {doc}\nArguments:\n{arg_block}"

	body = sep.join(_describe(f) for f in tools)
	return f"# {heading}\n{body}" if heading else body
