from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
import json
import re
from typing import Dict, Any, Tuple
from ..prompts.prompts import ConfigPrompt, WorkflowPrompt

class ConfigGenerator:
    """Generator for creating configurations based on user narratives."""
    
    DEFAULT_MODEL = "gpt-4o"
    
    def __init__(self, openai_api_key: str):
        """Initialize the configuration generator with OpenAI API key."""
        self.llm = ChatOpenAI(
            model=self.DEFAULT_MODEL,
            temperature=0,
            openai_api_key=openai_api_key
        )
        
        # Initialize prompts
        self.narrative_prompt = WorkflowPrompt()
        self.config_prompt = ConfigPrompt()
        
        # Create narrative template
        self.narrative_template = ChatPromptTemplate.from_messages([
            ("system", self.narrative_prompt.get_full_prompt()),
            ("human", "{input}")
        ])
        
        # Create config template
        self.config_template = ChatPromptTemplate.from_messages([
            ("system", self.config_prompt.get_full_prompt()),
            ("human", "{input}")
        ])
        
        self.output_parser = StrOutputParser()
        
        # Create the narrative preprocessing chain
        self.narrative_chain = (
            {"input": RunnablePassthrough()}
            | self.narrative_template
            | self.llm
            | self.output_parser
        )
        
        # Create the config generation chain
        self.config_chain = (
            {"input": RunnablePassthrough()}
            | self.config_template
            | self.llm
            | self.output_parser
        )
    
    def _clean_json_response(self, response: str) -> str:
        """Clean the JSON response by removing markdown formatting."""
        cleaned = re.sub(r'^```json\s*|\s*```$', '', response.strip())
        return cleaned
    
    def _validate_narrative(self, narrative: str) -> bool:
        """
        Validate if the narrative output is suitable for config generation.
        Override this method to implement specific validation rules.
        """
        if not narrative or not narrative.strip():
            return False
            
        return True
    
    def generate_config(self, user_input: str) -> Dict[str, Any]:
        """Generate configuration based on user input with narrative preprocessing."""
        try:
            # Generate narrative
            narrative = self.narrative_chain.invoke(user_input)
            
            # Validate narrative
            if not self._validate_narrative(narrative):
                raise ValueError(
                    "Generated narrative does not meet required criteria. "
                    "Please check the narrative output and validation rules."
                )
            
            # Generate config from validated narrative
            result = self.config_chain.invoke(narrative)
            cleaned_result = self._clean_json_response(result)
            
            try:
                return json.loads(cleaned_result)
            except json.JSONDecodeError as e:
                print(f"\nJSON parsing error: {str(e)}")
                print(f"Failed to parse: {cleaned_result}")
                raise
                
        except Exception as e:
            raise Exception(f"Error generating configuration: {str(e)}")
    
    def generate_with_narrative(self, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """Generate configuration and return the intermediate narrative as well."""
        try:
            # Get narrative first
            narrative = self.narrative_chain.invoke(user_input)
            
            # Validate narrative
            if not self._validate_narrative(narrative):
                raise ValueError(
                    "Generated narrative does not meet required criteria. "
                    "Please check the narrative output and validation rules."
                )
            
            # Generate config from validated narrative
            result = self.config_chain.invoke(narrative)
            cleaned_result = self._clean_json_response(result)
            
            config = json.loads(cleaned_result)
            return narrative, config
                
        except Exception as e:
            raise Exception(f"Error in generation pipeline: {str(e)}")