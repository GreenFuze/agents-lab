class InvalidTaskStructureError(Exception):
	"""Exception raised when task structure is invalid (missing fields, wrong types, etc.)"""
	pass 


class AgentNotFound(Exception):
    """Agent not found"""
    pass