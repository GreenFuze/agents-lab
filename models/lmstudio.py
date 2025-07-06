"""
This module provides a client for interacting with the LM Studio API using the official Python SDK.

Only to:
1. load/unload models
2. get model info
"""

import lmstudio as lms
from lmstudio._sdk_models import GpuSetting
from typing import Dict, Any, Optional

from models.bases import BackendClientBase, ModelInfo, ModelInstanceBase


class LMStudioModelInstance(ModelInstanceBase):
	def __init__(self, *, model_info: ModelInfo, lms_llm: lms.LLM, load_config: lms.LlmLoadModelConfig):
		super().__init__(model_info=model_info)
		self.lms_llm = lms_llm

		self.load_config = load_config
  
	def count_tokens(self, text: str) -> int:
		"""
		Count tokens in a text string using the specified model's tokenizer.
		
		:param model_name: The name of the model to use for tokenization.
		:param text: The text to tokenize and count.
		:return: Token count information.
		"""
		# Count tokens using the model's tokenizer
		return len(self.lms_llm.tokenize(text))


class LMStudioClient(BackendClientBase):
	def __init__(self, base_url: Optional[str] = None):
		"""
		Initialize the LM Studio client using the official Python SDK.
		
		:param base_url: The base URL of the LM Studio API (optional, uses default if not provided).
		"""
		super().__init__(base_url)
		self.loaded_models: Dict[str, LMStudioModelInstance] = {}


	def load_model(self, model_info: ModelInfo) -> ModelInstanceBase:
		assert "lmstudio" in model_info.backend_info.name
		assert model_info.backend_info.max_loaded_models is not None
     
		# Check if model is loaded, and that the context window size and temperature are correct
		if model_info.model_name in self.loaded_models:
			# check if the model was loaded with the requested configuration
			loaded_model = self.loaded_models[model_info.model_name]
			if loaded_model.model_info == model_info:
				return loaded_model # model is loaded with correct configuration
			
		while len(self.loaded_models) >= model_info.backend_info.max_loaded_models:
			to_unload_model = next(iter(self.loaded_models.values())) # TODO: needs to be an LRU
			to_unload_model.lms_llm.unload()
			del self.loaded_models[to_unload_model.model_name]

		# Load the model using the API
		load_cfg = lms.LlmLoadModelConfig(
			context_length=model_info.context_length,
			gpu=GpuSetting(ratio=model_info.gpu_ratio),
			flash_attention=True
		)

		return LMStudioModelInstance(model_info=model_info,
                               lms_llm=lms.llm(model_info.model_name, config=load_cfg),
                               load_config=load_cfg)

	def unload_all_models(self):
		"""
		Unload all models.
		"""
		for _, to_unload_model in self.loaded_models.items():
			to_unload_model.lms_llm.unload()
   
		self.loaded_models.clear()
  
	def unload_model(self, model_info: ModelInfo):
		"""
		Unload a model.
		"""
		if model_info.model_name in self.loaded_models:
			self.loaded_models[model_info.model_name].lms_llm.unload()
			del self.loaded_models[model_info.model_name]

	def is_model_loaded(self, model_info: ModelInfo) -> bool:
		"""
		Check if a model is loaded.
		"""
		return model_info.model_name in self.loaded_models

	def get_balance(self) -> float|None:
		"""
		Check the balance of the model - return None as not relevant
		"""
		return None
