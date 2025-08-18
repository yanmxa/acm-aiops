"""
Model Factory - Creates LLM instances with consistent configuration
"""

import os
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq


def create_llm(model_name: str = None, temperature: float = 0.1, streaming: bool = True):
    """
    Create an LLM instance with consistent configuration.
    
    Args:
        model_name: Model name to use, if None will use environment defaults
        temperature: Temperature setting for the model
        streaming: Whether to enable streaming
        
    Returns:
        LLM instance
    """
    if model_name is None:
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Check if we should use Groq instead
    use_groq = os.getenv("USE_GROQ", "false").lower() == "true"
    
    if use_groq:
        # Groq configuration - use provided model_name or default
        if model_name == os.getenv("OPENAI_MODEL", "gpt-4o"):
            model_name = os.getenv("GROQ_MODEL", "deepseek-r1-distill-llama-70b")
        
        llm = ChatGroq(
            model=model_name,
            temperature=temperature,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            cache=False,
        )
        return llm
    else:
        # OpenAI configuration
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("YEKA_OPENAI_API_KEY"),
            base_url=os.getenv("YEKA_OPENAI_BASE_URL"),
            streaming=streaming,
        )
        return llm