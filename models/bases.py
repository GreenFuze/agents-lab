from abc import ABC, abstractmethod
from typing import Optional


class BackendNotFoundError(Exception):
	def __init__(self, backend_name: str):
		self.backend_name = backend_name
		super().__init__(f"Backend '{backend_name}' not found")


class BackendInfo:
	def __init__(self, *, name: str, base_url: str, max_loaded_models: Optional[int] = None):
		self.name: str = name
		self.base_url: str = base_url
		self.max_loaded_models = max_loaded_models

	def __eq__(self, other) -> bool:
		"""Compare all fields of BackendInfo instances"""
		if not isinstance(other, BackendInfo):
			return False
		
		return (
			self.name == other.name and
			self.base_url == other.base_url
		)


class ModelInfo:
	def __init__(self, *, backend_info: BackendInfo, model_name: str, temperature: float, context_length: int, max_tokens: int, gpu_ratio: float):
		# make sure nothing is None
		assert backend_info is not None, "backend_info is required"
		assert model_name is not None, "model_name is required"
		assert temperature is not None, "temperature is required"
		assert context_length is not None, "context_length is required"
		assert max_tokens is not None, "max_tokens is required"
		assert gpu_ratio is not None, "gpu_ratio is required"
		
		self.backend_info: BackendInfo = backend_info
		self.model_name: str = model_name
		self.temperature: float = temperature
		self.max_tokens: int = max_tokens
		self.context_length: int = context_length
		self.gpu_ratio: float = gpu_ratio

	def __eq__(self, other) -> bool:
		"""Compare all fields of ModelInfo instances"""
		if not isinstance(other, ModelInfo):
			return False
		
		return (
			self.backend_info == other.backend_info and
			self.model_name == other.model_name and
			self.temperature == other.temperature and
			self.max_tokens == other.max_tokens and
			self.context_length == other.context_length and
			self.gpu_ratio == other.gpu_ratio
		)
  
	
class ModelInstanceBase(ABC):
	def __init__(self, *, model_info: ModelInfo):
		self.model_info: ModelInfo = model_info
  
	@abstractmethod
	def count_tokens(self, text: str) -> int:
		raise NotImplemented('Inherited class does not implement count_tokens')			

	@property
	def model_name(self) -> str:
		return self.model_info.model_name


class BackendClientBase(ABC):
	def __init__(self, base_url: Optional[str] = None):
		self.base_url = base_url
  
	@abstractmethod
	def load_model(self, model_info: ModelInfo) -> ModelInstanceBase:
		raise NotImplemented('Inherited class does not implement load_model')

	@abstractmethod
	def unload_model(self, model_info: ModelInfo) -> None:
		raise NotImplemented('Inherited class does not implement unload_model')

	@abstractmethod
	def unload_all_models(self) -> None:
		raise NotImplemented('Inherited class does not implement unload_all_models')

	@abstractmethod
	def is_model_loaded(self, model_info: ModelInfo) -> bool:
		raise NotImplemented('Inherited class does not implement is_model_loaded')

	@abstractmethod
	def get_balance(self) -> float|None:
		"""
		Check the balance of the model - return None as not relevant
		"""
		raise NotImplemented('Inherited class does not implement get_balance')

