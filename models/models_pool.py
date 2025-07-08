import os
import json
from typing import Dict
from models.bases import *
from models.lmstudio import LMStudioClient


class ModelNotFoundError(Exception):
	def __init__(self, model_name: str):
		self.model_name = model_name
		super().__init__(f"Model '{model_name}' not found")


class ModelsPool:
	"""Manages intelligent model switching for the agent system""" 
	def __init__(self, models_json_path: str):
		self.models_json_path = models_json_path
		self.backends: Dict[str, BackendInfo] = {}
		self.models: Dict[str, ModelInfo] = {}
		
		self._load_models_config()
		
		self.backend_clients: Dict[str, BackendClientBase] = self._load_backend_clients()
  
  
	def _load_backend_clients(self) -> Dict[str, BackendClientBase]:
		"""Load the backend clients from the models configuration"""
		backend_clients = {}
		for backend_name, backend_info in self.backends.items():
			if "lmstudio" in backend_name: # use "in" to allow multiple lmstudios on different urls
				backend_client = LMStudioClient(base_url=backend_info.base_url)
			else:
				raise BackendNotFoundError(backend_name)
			backend_clients[backend_name] = backend_client
		return backend_clients


	def _load_models_config(self):
		"""Load and parse the models configuration JSON file"""
		try:
			with open(self.models_json_path, 'r') as f:
				config = json.load(f)
			
			# Load backends
			backends_config = config.get('backends')
			for backend_name, backend_data in backends_config.items():
				backend_info = BackendInfo(
					name=backend_name,
					base_url=backend_data['url'],
					support_schema=backend_data.get('support_schema', False),
					support_grammar=backend_data.get('support_grammar', False),
					max_loaded_models=backend_data.get('max_loaded_models')
				)
				
				self.backends[backend_name] = backend_info
			
			# Load models
			models_config = config.get('models')
			for model_name, model_data in models_config.items():
				backend_name = model_data['backend']
				if backend_name not in self.backends:
					raise ValueError(f"Backend '{backend_name}' not found for model '{model_name}'")
				
				backend_info = self.backends[backend_name]
				model_info = ModelInfo(
					backend_info=backend_info,
					model_name=model_name,
					key=model_data['key'],
					context_length=model_data['context_length'],
					gpu_ratio=model_data['gpu_ratio'],
					stop_strings=model_data.get('stop_strings')	# optional
				)
    
				# Add any additional fields from the JSON as attributes
				for key, value in model_data.items():
					if not hasattr(model_info, key):  # Skip attributes that already exist
						setattr(model_info, key, value)
    
				self.models[model_name] = model_info
				
		except FileNotFoundError:
			raise FileNotFoundError(f"Models configuration file not found: {self.models_json_path}")
		except json.JSONDecodeError as e:
			raise ValueError(f"Invalid JSON in models configuration file: {e}")
		except KeyError as e:
			raise ValueError(f"Missing required field in models configuration: {e}")
 
  
	def ensure_model_loaded(self, model_info: ModelInfo) -> ModelInstanceBase:
		"""Ensure the optimal model for an agent is loaded"""
		return self.backend_clients[model_info.backend_info.name].load_model(model_info)


	def get_model_by_name(self, model_name: str) -> ModelInfo:
		"""Get a model by name"""
		if model_name not in self.models:
			raise ModelNotFoundError(model_name)
		return self.models[model_name]

	def get_all_models(self) -> Dict[str, ModelInfo]:
		"""Get all models names"""
		return self.models

	def cleanup(self) -> None:
		"""Clean up resources and unload models"""
		# iterate every backend and unload all models
		for _, backend_client in self.backend_clients.items():
			backend_client.unload_all_models()


# Global instance - models.json in the directory of the script
ModelsPoolInstance = ModelsPool(os.path.join(os.path.dirname(__file__), "models.json"))
