from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional


class BackendNotFoundError(Exception):
	def __init__(self, backend_name: str):
		self.backend_name = backend_name
		super().__init__(f"Backend '{backend_name}' not found")


class BackendInfo:
	def __init__(self, *, name: str, base_url: str, support_schema: bool, support_grammar: bool, max_loaded_models: Optional[int] = None):
		self.name: str = name
		self.base_url: str = base_url
		self.support_schema: bool = support_schema
		self.support_grammar: bool = support_grammar
		self.max_loaded_models = max_loaded_models
  
	def __eq__(self, other) -> bool:
		"""Compare all fields of BackendInfo instances"""
		if not isinstance(other, BackendInfo):
			return False
		
		return (
			self.name == other.name and
			self.base_url == other.base_url and
			self.support_schema == other.support_schema and
			self.support_grammar == other.support_grammar and
			self.max_loaded_models == other.max_loaded_models
		)


class ModelInfo:
	def __init__(self, *, backend_info: BackendInfo, model_name: str, key: str, context_length: int, gpu_ratio: float, stop_strings: Optional[List[str]]):
		# make sure nothing is None
		assert backend_info is not None, "backend_info is required"
		assert model_name is not None, "model_name is required"
		assert key is not None, "key is required"
		assert context_length is not None, "context_length is required"
		assert gpu_ratio is not None, "gpu_ratio is required"
  
		self.backend_info: BackendInfo = backend_info
		self.model_name: str = model_name
		self.key: str = key
		self.context_length: int = context_length
		self.gpu_ratio: float = gpu_ratio
		self.stop_strings: List[str]|None = stop_strings if stop_strings is not None else None
  
	def __eq__(self, other) -> bool:
		"""Compare all fields of ModelInfo instances"""
		if not isinstance(other, ModelInfo):
			return False
		
		return (
			self.backend_info == other.backend_info and
			self.model_name == other.model_name and
			self.key == other.key and
			self.context_length == other.context_length and
			self.gpu_ratio == other.gpu_ratio and
			self.stop_strings == other.stop_strings
		)
  
  
class InferenceConfig:
	def __init__(self, *, max_tokens: int, temperature: float, grammar: Optional[str], schema: Optional[str], stop_strings: Optional[List[str]]):
		assert max_tokens is not None, "max_tokens is required"
		assert temperature is not None, "temperature is required"
  
		self.temperature = temperature
		self.max_tokens = max_tokens
		self.grammar: Optional[str] = grammar
		self.schema: Optional[str] = schema
		self.stop_strings: Optional[List[str]] = stop_strings
  
class SummarizationConfig:
	def __init__(self, *, summarization_threshold: float, char_to_token_ratio: int, percentage_to_summarize: float):
		assert summarization_threshold is not None, "summarization_threshold is required"
		assert char_to_token_ratio is not None, "char_to_token_ratio is required"
		assert percentage_to_summarize is not None, "percentage_to_summarize is required"
  
		self.summarization_threshold = summarization_threshold
		self.char_to_token_ratio = char_to_token_ratio
		self.percentage_to_summarize = percentage_to_summarize
  
	
class ModelInstanceBase(ABC):
	def __init__(self, *, model_info: ModelInfo):
		self.model_info: ModelInfo = model_info
  
	@abstractmethod
	def count_tokens(self, text: str) -> int:
		raise NotImplemented('Inherited class does not implement count_tokens')			

	@abstractmethod
	def complete(self, prompt: str, config: InferenceConfig) -> str:
		raise NotImplemented('Inherited class does not implement complete')

	@abstractmethod
	def complete_stream(self, prompt: str, config: InferenceConfig) -> Iterator[str]:
		raise NotImplemented('Inherited class does not implement complete_stream')

	@abstractmethod
	def apply_prompt_template(self, prompt: List[Dict[str, Any]]) -> str:
		raise NotImplemented('Inherited class does not implement apply_prompt_template')

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

