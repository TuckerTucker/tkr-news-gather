from anthropic import Anthropic
from typing import Dict, List, Optional
from .logger import get_logger

logger = get_logger(__name__)

class AnthropicClient:
    def __init__(self, config):
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.ANTHROPIC_MODEL
        self.temperature = config.LLM_TEMP
        self.max_tokens = config.LLM_MAX_TOKENS
    
    async def generate_completion(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> str:
        """Generate completion using Anthropic API"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=temperature or self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise