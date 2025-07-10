#!/usr/bin/env python3
"""
MetaFFI Local Development LLM Agent System
Main entry point for the multi-agent system
"""

import traceback
from agents.prompts import *
from agents.agent import Agent
from agents.agents_pool import CurrentAgentsPool, CurrentAgent
from agents.tools.tool_executer import run_tool
from models.models_pool import ModelsPoolInstance
import utils.logger as logger

def main_loop():
	global CurrentAgent
	
	assert CurrentAgent is not None, "CurrentAgent is not set"
    
	# Main interaction loop
	while True:
		try:
			user_input = input(f"{CurrentAgent.get_context_display()} >>> ").strip()
			if not user_input:
				continue
			
			# Handle special commands
			if user_input.lower() in ['quit', 'exit', 'q']:
				break

			# Process the user input
			response_json = CurrentAgent.call_llm(user_input)
	
			while response_json['action'] != PromptType.NORMAL_RESPONSE.value:

				if response_json['action'] == PromptType.DELEGATE_TASK.value: # agent asked to delegate a task
					try:
						p = delegation_prompt(response_json)
      
						# check that the requested agent exists, if not, return an error to the calling agent
						if p.agent not in CurrentAgentsPool.pool:
							logger.system(f"Agent {p.agent} does not exist. Please try again.\nAvailable agents: {CurrentAgentsPool.pool.keys()}")
							response_json = CurrentAgent.call_llm(f"Agent {p.agent} does not exist. Please try again.\nAvailable agents: {CurrentAgentsPool.pool.keys()}", False)
							continue
         
						logger.system(f"Delegating task to {p.agent}")
						logger.system(f"Delegation prompt: {p.generate_prompt()}")
						CurrentAgent = CurrentAgentsPool.get_agent(p.agent)
						response_json = CurrentAgent.call_llm(p.generate_prompt())
					except InvalidTaskStructureError as e:
						invalid_structure_prompt = f"Your {PromptType.DELEGATE_TASK.value} prompt is invalid. Error: {e}"
						response_json = CurrentAgent.call_llm(invalid_structure_prompt, False)
				
				elif response_json['action'] == PromptType.DELEGATE_BACK.value: # agent asked to delegate back
					try:
						p = delegation_back_prompt(response_json)
						logger.system(f"Delegating back to {p.return_to_agent}")
						logger.system(f"Delegation back prompt: {p.generate_prompt()}")
						CurrentAgent = CurrentAgentsPool.get_agent(p.return_to_agent)
						response_json = CurrentAgent.call_llm(p.generate_prompt())
					except InvalidTaskStructureError as e:
						invalid_structure_prompt = f"Your DELEGATE_BACK prompt is invalid. Error: {e}"
						response_json = CurrentAgent.call_llm(invalid_structure_prompt, False)
				
				elif response_json['action'] == PromptType.USE_TOOL.value: # agent used a tool
					try:
						t = tools_prompt(response_json)
						tool_res = run_tool(t.tool, t.args)
						response_json = CurrentAgent.call_llm(tool_res.as_json())
					except InvalidTaskStructureError as e:
						invalid_structure_prompt = f"Your USE_TOOL prompt is invalid. Error: {e}"
						response_json = CurrentAgent.call_llm(invalid_structure_prompt, False)
				else:
					raise ValueError(f"You requested an unknown action: {response_json['action']}")
			
			# Log AI response to user
			if response_json['action'] == PromptType.NORMAL_RESPONSE.value:
				logger.ai_to_user(response_json['response'])
			
		except KeyboardInterrupt:
			print("\nReceived interrupt. Type 'quit' to exit or continue...")
			continue
		except EOFError:
			print("\nEnd of input received. quitting...")
			break
		except Exception as e:
			logger.error(f"An error occurred in main loop: {e}\nRecovering...")
			continue


def main():
	"""Main function to run the MetaFFI Agent System"""
 
	global CurrentAgent
 
	try:
		print("=" * 60)
		print("MetaFFI Local Development LLM Agent System")
		print("=" * 60)
		
		logger.info("Loading...")
  
		# Initialize the Root Coordinator
		CurrentAgent = CurrentAgentsPool.get_agent("Zeus")
		
		# Start with greeting
		logger.success("Welcome to MetaFFI Dev room! Type 'quit/exit/q' to exit.")
		
		main_loop()
	
	except Exception as e:
		logger.error(f"Fatal error in main: {e}")
		# log stack trace
		logger.error(traceback.format_exc())
	finally:
		logger.info("Unloading models")
		try:
			ModelsPoolInstance.cleanup()
		except Exception as e:
			logger.error(f"Failed during models unload: {e}")

	logger.success("Goodbye!")

if __name__ == "__main__":
	main()
