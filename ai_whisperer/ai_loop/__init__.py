# Export only the config and stateless implementations
from .ai_config import AIConfig
from .stateless_ai_loop import StatelessAILoop

# Note: The old ai_loopy.AILoop is deprecated due to delegate dependencies
# Use StatelessAILoop for new code