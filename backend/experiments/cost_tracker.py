from typing import Dict, Tuple

class CostTracker:
    # Pricing per 1M tokens (USD)
    # Estimates based on public pricing pages as of late 2024/early 2025
    PRICING = {
        # Gemini 1.5 Pro
        "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
        "gemini-1.5-pro-002": {"input": 3.50, "output": 10.50},
        # Gemini Flash (Very Cheap)
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-1.5-flash-002": {"input": 0.075, "output": 0.30},
        # Claude 3.5 Sonnet
        "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
        # xAI Grok (Estimate, assuming similar to GPT-4o or slightly lower)
        "grok-beta": {"input": 5.00, "output": 15.00}, 
        # Fallback
        "default": {"input": 5.00, "output": 15.00}
    }

    def __init__(self, budget_limit: float = 15.0):
        self.budget_limit = budget_limit
        self.total_spent = 0.0
        self.usage_per_model: Dict[str, float] = {}

    def estimate_cost(self, model_name: str, input_chars: int, output_chars: int) -> float:
        """
        Estimate cost based on character count (1 token ~= 4 chars).
        Real API usage would be better, but character approximation works for pre-flight checks.
        """
        # Simple approximation: 1 token = 4 characters
        input_tokens = input_chars / 4.0
        output_tokens = output_chars / 4.0
        
        return self._calculate_cost(model_name, input_tokens, output_tokens)

    def track_usage(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        Record actual usage after an API call. Returns the cost of that single call.
        """
        cost = self._calculate_cost(model_name, input_tokens, output_tokens)
        
        self.total_spent += cost
        if model_name not in self.usage_per_model:
            self.usage_per_model[model_name] = 0.0
        self.usage_per_model[model_name] += cost
        
        return cost

    def _calculate_cost(self, model_name: str, input_tokens: float, output_tokens: float) -> float:
        # Find best matching price key
        price_key = "default"
        for key in self.PRICING:
            if key in model_name.lower():
                price_key = key
                break
        
        prices = self.PRICING[price_key]
        input_cost = (input_tokens / 1_000_000) * prices["input"]
        output_cost = (output_tokens / 1_000_000) * prices["output"]
        
        return input_cost + output_cost

    def is_over_budget(self) -> bool:
        return self.total_spent >= self.budget_limit

    def get_remaining_budget(self) -> float:
        return max(0.0, self.budget_limit - self.total_spent)
