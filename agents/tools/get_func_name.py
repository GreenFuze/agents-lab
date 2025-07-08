import inspect

def get_current_function_name():
    frame = inspect.currentframe()
    if frame is None:
        return "unknown"
    return frame.f_code.co_name
