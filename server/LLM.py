import os
from typing import Optional, Dict, Any, List
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.manager import CallbackManager
import asyncio
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

@dataclass
class ModelConfig:
    """Configuration class for different GPT models"""
    name: str
    deployment_name: str
    max_tokens: int
    temperature: float
    
class AdvancedAzureLLM:
    """
    Advanced LangChain class for Azure OpenAI GPT models
    Supports multiple model versions with different configurations
    """
    
    def __init__(
        self, 
        api_version: str = None
    ):
        """
        Initialize the Azure LLM client with separate configurations for GPT-4.1 and GPT-5
        
        Args:
            api_version: API version to use (will use from env if not specified)
        """
        # Load environment variables for first Azure system (GPT-4.1)
        self.gpt4_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.gpt4_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.gpt4_api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        # Load environment variables for second Azure system (GPT-5)
        self.gpt5_api_key = os.getenv("AZURE_OPENAI_API_KEY_2")
        self.gpt5_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_2")
        self.gpt5_api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION_2", "2024-02-15-preview")
        
        # Set default API version if not provided
        self.api_version = api_version or "2024-02-15-preview"
        
        # Validate required environment variables
        if not self.gpt4_api_key or not self.gpt4_endpoint:
            raise ValueError("Missing GPT-4.1 Azure credentials. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT")
        
        if not self.gpt5_api_key or not self.gpt5_endpoint:
            raise ValueError("Missing GPT-5 Azure credentials. Please set AZURE_OPENAI_API_KEY_2 and AZURE_OPENAI_ENDPOINT_2")
        
        # Model configurations with Azure system mapping based on your .env file
        self.model_configs = {
            "gpt-4.1": ModelConfig(
                name="gpt-4.1",
                deployment_name=os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME_GPT_4_1", "gpt-4.1"),
                max_tokens=12000,  # Set to 12000 tokens
                temperature=1.0
            ),
            "gpt-5": ModelConfig(
                name="gpt-5", 
                deployment_name=os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME_GPT_5", "gpt-5"),
                max_tokens=12000,  # Set to 12000 tokens
                temperature=1.0
            ),
            "gpt-4.1-mini": ModelConfig(
                name="gpt-4.1-mini",
                deployment_name=os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME_GPT_4_1_MINI", "gpt-4.1-mini"),
                max_tokens=12000,  # Set to 12000 tokens
                temperature=1.0
            ),
            "gpt-5-mini": ModelConfig(
                name="gpt-5-mini",
                deployment_name=os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME_GPT_5_MINI", "gpt-5-mini"),
                max_tokens=12000,  # Set to 12000 tokens
                temperature=1.0
            )
        }
        
        # Model to Azure system mapping
        self.model_to_system = {
            "gpt-4.1": "system1",
            "gpt-4.1-mini": "system1",
            "gpt-5": "system2", 
            "gpt-5-mini": "system2"
        }
        
        # Current model client
        self.current_model = "gpt-5"
        self.client = self._create_client(self.current_model)
    
    def _create_client(
        self, 
        model_name: str, 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: bool = False
    ) -> AzureChatOpenAI:
        """
        Create Azure OpenAI client for specific model using appropriate Azure system credentials
        
        Args:
            model_name: Name of the model to use
            temperature: Override default temperature
            max_tokens: Override default max tokens
            streaming: Enable streaming responses
        
        Returns:
            AzureChatOpenAI client instance
        """
        config = self.model_configs.get(model_name)
        if not config:
            raise ValueError(f"Model {model_name} not configured")
        
        # Get the Azure system for this model
        azure_system = self.model_to_system.get(model_name)
        if not azure_system:
            raise ValueError(f"No Azure system mapping found for model {model_name}")
        
        # Select appropriate credentials based on the model
        if azure_system == "system1":
            api_key = self.gpt4_api_key
            azure_endpoint = self.gpt4_endpoint
            api_version = self.gpt4_api_version
        elif azure_system == "system2":
            api_key = self.gpt5_api_key
            azure_endpoint = self.gpt5_endpoint
            api_version = self.gpt5_api_version
        else:
            raise ValueError(f"Unknown Azure system: {azure_system}")
        
        # Setup callbacks for streaming if needed
        callbacks = None
        if streaming:
            callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
            callbacks = callback_manager
        
        # Use temperature = 1.0 (only supported value for these models)
        # Override any custom temperature with 1.0
        final_temperature = 1.0
        
        return AzureChatOpenAI(
            azure_deployment=config.deployment_name,
            api_version=api_version,
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            temperature=final_temperature,
            max_completion_tokens=max_tokens or config.max_tokens,  # Specify directly, not in model_kwargs
            streaming=streaming,
            callbacks=callbacks
        )
    
    def switch_model(self, model_name: str):
        """Switch to a different model"""
        if model_name not in self.model_configs:
            raise ValueError(f"Model {model_name} not available. Available models: {list(self.model_configs.keys())}")
        
        self.current_model = model_name
        self.client = self._create_client(model_name)
    
    def generate_response(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate response using current model
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            temperature: Override temperature
            max_tokens: Override max tokens
        
        Returns:
            Model response as string
        """
        # Create new client with custom parameters if provided
        if temperature is not None or max_tokens is not None:
            client = self._create_client(
                self.current_model, 
                temperature=temperature, 
                max_tokens=max_tokens
            )
        else:
            client = self.client
        
        # Prepare messages
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        
        # Generate response
        response = client.invoke(messages)
        return response.content
    
    # Specific model methods
    def gpt_4_1(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate response using GPT-4.1"""
        original_model = self.current_model
        self.switch_model("gpt-4.1")
        
        try:
            response = self.generate_response(
                prompt, 
                system_message=system_message, 
                temperature=temperature
            )
            return response
        finally:
            self.switch_model(original_model)
    
    def gpt_5(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate response using GPT-5"""
        original_model = self.current_model
        self.switch_model("gpt-5")
        
        try:
            response = self.generate_response(
                prompt, 
                system_message=system_message, 
                temperature=temperature
            )
            return response
        finally:
            self.switch_model(original_model)
    
    def gpt_4_1_mini(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate response using GPT-4.1-mini"""
        original_model = self.current_model
        self.switch_model("gpt-4.1-mini")
        
        try:
            response = self.generate_response(
                prompt, 
                system_message=system_message, 
                temperature=temperature
            )
            return response
        finally:
            self.switch_model(original_model)
    
    def gpt_5_mini(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate response using GPT-5-mini"""
        original_model = self.current_model
        self.switch_model("gpt-5-mini")
        
        try:
            response = self.generate_response(
                prompt, 
                system_message=system_message, 
                temperature=temperature
            )
            return response
        finally:
            self.switch_model(original_model)
    
    def stream_response(
        self, 
        prompt: str, 
        model_name: Optional[str] = None,
        system_message: Optional[str] = None
    ):
        """
        Stream response from model
        
        Args:
            prompt: User prompt
            model_name: Specific model to use
            system_message: Optional system message
        """
        model_to_use = model_name or self.current_model
        streaming_client = self._create_client(model_to_use, streaming=True)
        
        # Prepare messages
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        
        # Stream response
        streaming_client.invoke(messages)
    
    async def async_generate(
        self, 
        prompt: str, 
        model_name: Optional[str] = None,
        system_message: Optional[str] = None
    ) -> str:
        """
        Asynchronously generate response
        
        Args:
            prompt: User prompt
            model_name: Specific model to use
            system_message: Optional system message
        
        Returns:
            Model response as string
        """
        model_to_use = model_name or self.current_model
        client = self._create_client(model_to_use)
        
        # Prepare messages
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        
        # Generate response asynchronously
        response = await client.agenerate([messages])
        return response.generations[0][0].text
    
    def batch_generate(
        self, 
        prompts: List[str], 
        model_name: Optional[str] = None,
        system_message: Optional[str] = None
    ) -> List[str]:
        """
        Generate responses for multiple prompts
        
        Args:
            prompts: List of prompts
            model_name: Specific model to use
            system_message: Optional system message
        
        Returns:
            List of responses
        """
        model_to_use = model_name or self.current_model
        client = self._create_client(model_to_use)
        
        responses = []
        for prompt in prompts:
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
            messages.append(HumanMessage(content=prompt))
            
            response = client.invoke(messages)
            responses.append(response.content)
        
        return responses
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models and Azure systems"""
        return {
            "current_model": self.current_model,
            "available_models": list(self.model_configs.keys()),
            "model_configs": {
                name: {
                    "deployment_name": config.deployment_name,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "azure_system": self.model_to_system.get(name)
                }
                for name, config in self.model_configs.items()
            },
            "azure_systems": {
                "system1": {
                    "endpoint": self.gpt4_endpoint,
                    "api_key_set": bool(self.gpt4_api_key),
                    "api_version": self.gpt4_api_version
                },
                "system2": {
                    "endpoint": self.gpt5_endpoint,
                    "api_key_set": bool(self.gpt5_api_key),
                    "api_version": self.gpt5_api_version
                }
            }
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of Azure systems configuration"""
        return {
            "system1_gpt4": {
                "api_key_configured": bool(self.gpt4_api_key),
                "endpoint_configured": bool(self.gpt4_endpoint),
                "endpoint": self.gpt4_endpoint if self.gpt4_endpoint else "Not configured",
                "api_version": self.gpt4_api_version,
                "deployment": os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME", "gpt-4.1-mini")
            },
            "system2_gpt5": {
                "api_key_configured": bool(self.gpt5_api_key),
                "endpoint_configured": bool(self.gpt5_endpoint),
                "endpoint": self.gpt5_endpoint if self.gpt5_endpoint else "Not configured",
                "api_version": self.gpt5_api_version,
                "deployment": os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME_2", "gpt-5-mini")
            }
        }

# Usage Example
if __name__ == "__main__":
    # Initialize with automatic environment variable loading
    # Make sure you have the following environment variables set in your .env file:
    # AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION
    # AZURE_OPENAI_API_KEY_2, AZURE_OPENAI_ENDPOINT_2, AZURE_OPENAI_API_DEPLOYMENT_NAME_2, AZURE_OPENAI_API_VERSION_2
    llm = AdvancedAzureLLM()
    
    # Check system status
    system_status = llm.get_system_status()
    print("System status:", system_status)
    
    # Basic usage
    response = llm.generate_response("Hello, how are you?")
    print("Basic response:", response)
    
    # Using specific models
    gpt4_response = llm.gpt_4_1("Explain quantum computing")
    print("GPT-4.1 response:", gpt4_response)
    
    gpt5_response = llm.gpt_5("Write a Python function", temperature=0.3)
    print("GPT-5 response:", gpt5_response)
    
    gpt5mini_response = llm.gpt_5_mini("Write a Python function", temperature=0.3)
    print("GPT-5-mini response:", gpt5mini_response)

    # Using mini models for faster/cheaper responses
    mini_response = llm.gpt_4_1_mini("Quick summary of AI")
    print("Mini response:", mini_response)
    
    # # Batch processing
    # prompts = ["What is AI?", "Explain machine learning", "Define deep learning"]
    # batch_responses = llm.batch_generate(prompts, model_name="gpt-4.1-mini")
    
    # # Streaming example
    # print("Streaming response:")
    # llm.stream_response("Tell me a story about AI", model_name="gpt-5")
    
    # Get model information
    model_info = llm.get_model_info()
    print("Model info:", model_info)
