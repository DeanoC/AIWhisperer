from typing import Dict, Any, Optional

class AIConfig:
    """
    Configuration for the AILoop.
    """
    def __init__(
        self,
        api_key: str,
        model_id: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        max_reasoning_tokens: Optional[int] = None,
        **kwargs: Any
    ):
        self.api_key = api_key
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_reasoning_tokens = max_reasoning_tokens  # 0 = exclude reasoning entirely
        # Store any additional keyword arguments
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        return f"AIConfig(model_id='{self.model_id}', ...)"