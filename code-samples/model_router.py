#!/usr/bin/env python3
"""
Multi-Provider LLM Router with Fallback Chain
Implements cost-aware model selection and automatic fallback.

Usage:
    result = router.call("Summarize this email", task_type="general")
    print(result["text"])  # Output from whichever model succeeded
"""
import os
import time
from typing import Dict, List, Optional

# API Keys (loaded from environment)
KIMI_KEY = os.getenv("KIMI_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

# Cost tracking
MONTHLY_BUDGET_USD = 25.0


class ModelRouter:
    """Routes inference requests across multiple LLM providers with fallback."""

    def __init__(self):
        self.usage_log: List[Dict] = []
        self.chains = {
            "general": ["kimi", "gemini", "claude"],
            "vision": ["gemini", "kimi", "claude"],
            "research": ["perplexity"],
            "coding": ["kimi", "claude", "gemini"],
            "creative": ["claude", "kimi", "gemini"],
            "local": ["local"],
        }

    def call(
        self,
        prompt: str,
        max_tokens: int = 500,
        task_type: str = "general",
        force_model: Optional[str] = None,
    ) -> Dict:
        """
        Route a prompt through the fallback chain.

        Args:
            prompt: The input text
            max_tokens: Maximum output tokens
            task_type: general | vision | research | coding | creative | local
            force_model: Override chain (kimi | gemini | claude | perplexity | local)

        Returns:
            Dict with keys: model, text, latency_ms
        """
        chain = [force_model] if force_model else self.chains.get(task_type, ["kimi"])

        last_error = None
        for model_name in chain:
            try:
                start = time.time()
                result_text = self._dispatch(model_name, prompt, max_tokens)
                elapsed_ms = (time.time() - start) * 1000

                self._log_usage(model_name, prompt, result_text, elapsed_ms)
                return {"model": model_name, "text": result_text, "latency_ms": elapsed_ms}
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"All models failed. Last error: {last_error}")

    def _dispatch(self, model: str, prompt: str, max_tokens: int) -> str:
        """Dispatch to specific provider."""
        if model == "kimi":
            return self._kimi_call(prompt, max_tokens)
        elif model == "gemini":
            return self._gemini_call(prompt, max_tokens)
        elif model == "claude":
            return self._claude_call(prompt, max_tokens)
        elif model == "local":
            return self._ollama_call(prompt, max_tokens)
        else:
            raise ValueError(f"Unknown model: {model}")

    def _kimi_call(self, prompt: str, max_tokens: int) -> str:
        """Call Moonshot Kimi API."""
        import requests

        resp = requests.post(
            "https://api.moonshot.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {KIMI_KEY}"},
            json={
                "model": "kimi-k2.6",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _gemini_call(self, prompt: str, max_tokens: int) -> str:
        """Call Google Gemini API."""
        import requests

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
        )
        resp = requests.post(
            url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens},
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    def _claude_call(self, prompt: str, max_tokens: int) -> str:
        """Call Anthropic Claude API."""
        import requests

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    def _ollama_call(self, prompt: str, max_tokens: int) -> str:
        """Call local Ollama instance."""
        import requests

        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:3b",
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens},
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["response"]

    def _log_usage(self, model: str, prompt: str, result: str, latency_ms: float):
        """Log usage for cost tracking."""
        input_tokens = len(prompt) // 4
        output_tokens = len(result) // 4
        cost = self._estimate_cost(model, input_tokens, output_tokens)

        self.usage_log.append({
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "latency_ms": latency_ms,
        })

    def _estimate_cost(self, model: str, input_tok: int, output_tok: int) -> float:
        """Estimate cost in USD."""
        rates = {
            "kimi": {"in": 0.50, "out": 2.00},
            "gemini": {"in": 0.15, "out": 0.60},
            "claude": {"in": 3.00, "out": 15.00},
            "local": {"in": 0, "out": 0},
        }
        r = rates.get(model, rates["kimi"])
        return (input_tok * r["in"] + output_tok * r["out"]) / 1_000_000

    def monthly_spend(self) -> float:
        """Return estimated monthly spend."""
        return sum(u["cost_usd"] for u in self.usage_log)

    def is_over_budget(self) -> bool:
        """Check if monthly budget is exceeded."""
        return self.monthly_spend() > MONTHLY_BUDGET_USD


# Convenience functions for cron jobs
def quick_infer(prompt: str, max_tokens: int = 100) -> Dict:
    """Fast inference — routes to Gemini for speed."""
    return router.call(prompt, max_tokens, task_type="general", force_model="gemini")


def deep_infer(prompt: str, max_tokens: int = 1000) -> Dict:
    """Deep inference — routes to Kimi for quality."""
    return router.call(prompt, max_tokens, task_type="general", force_model="kimi")


# Global router instance
router = ModelRouter()

if __name__ == "__main__":
    # Test the router
    test_prompt = "Explain what a cron job is in one sentence."
    result = router.call(test_prompt, max_tokens=50, task_type="general")
    print(f"Model: {result['model']}")
    print(f"Latency: {result['latency_ms']:.0f}ms")
    print(f"Response: {result['text']}")
    print(f"Spend so far: ${router.monthly_spend():.4f}")
