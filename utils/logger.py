import colorama

# Initialize colorama
colorama.init()

LOG_COLOR = colorama.Fore.WHITE
WARNING_COLOR = colorama.Fore.YELLOW
ERROR_COLOR = colorama.Fore.RED
SYSTEM_COLOR = colorama.Fore.LIGHTBLUE_EX
USER_COLOR = colorama.Fore.LIGHTGREEN_EX
AI_COLOR = colorama.Fore.MAGENTA
AI_TO_AI_COLOR = colorama.Fore.LIGHTMAGENTA_EX
TOOL_COLOR = colorama.Fore.WHITE
SUCCESS_COLOR = colorama.Fore.GREEN
RESET_COLOR = colorama.Style.RESET_ALL

def log(message: str):
    """Prints a standard log message."""
    print(f"{LOG_COLOR}[LOG] {message}{RESET_COLOR}")
    
def info(message: str):
    """Prints a standard log message."""
    print(f"{LOG_COLOR}[INFO] {message}{RESET_COLOR}")
    
def warning(message: str):
    """Prints a warning message."""
    print(f"{WARNING_COLOR}[WARNING] {message}{RESET_COLOR}")

def error(message: str):
    """Prints an error message."""
    print(f"{ERROR_COLOR}[ERROR] {message}{RESET_COLOR}")

def system(message: str):
    """Prints a system message."""
    print(f"{SYSTEM_COLOR}[SYSTEM] {message}{RESET_COLOR}")
    
def user(message: str):
    """Prints a user message."""
    print(f"{USER_COLOR}[USER] {message}{RESET_COLOR}")
    
def ai_to_ai(message: str, end: str = "\n", flush: bool = False):
    """Prints an AI message."""
    print(f"{AI_TO_AI_COLOR}[AI_TO_AI] {message}{RESET_COLOR}", end=end, flush=flush) 

def ai(message: str, end: str = "\n", flush: bool = False):
    """Prints an AI message."""
    print(f"{AI_COLOR}[AI] {message}{RESET_COLOR}", end=end, flush=flush) 
    
def tool(message: str):
    """Prints a tool message."""
    print(f"{TOOL_COLOR}[TOOL] {message}{RESET_COLOR}")
    
def success(message: str):
    """Prints a success message."""
    print(f"{SUCCESS_COLOR}[SUCCESS] {message}{RESET_COLOR}")