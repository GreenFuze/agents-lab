import re

def clean_tool_output(text: str) -> str:
    """
    Removes markdown code blocks and surrounding whitespace from a string.
    """
    # Pattern to find a markdown code block, capturing the content inside
    pattern = r"```(?:\w+\n)?(.*?)```"
    
    match = re.search(pattern, text, re.DOTALL)
    
    # If a markdown block is found, return its content, stripped of whitespace
    if match:
        return match.group(1).strip()
        
    # Otherwise, return the original text, stripped of whitespace
    return text.strip() 