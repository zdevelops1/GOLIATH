"""
Perplexity Search Integration — run AI-powered web searches via the Perplexity Sonar API.

SETUP INSTRUCTIONS
==================

1. Go to https://www.perplexity.ai/ and log in.

2. Navigate to Settings > API (or visit https://www.perplexity.ai/settings/api).

3. Generate an API key.

4. Add to your .env:
     PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxx

   (If you already set PERPLEXITY_API_KEY for the model provider, this
   integration reuses the same key — no extra setup needed.)

IMPORTANT NOTES
===============
- This integration uses the Perplexity Sonar API for search-augmented answers.
- Unlike the model provider (which is for general chat), this focuses on
  web search with citations.
- API docs: https://docs.perplexity.ai/
- Rate limit: depends on your plan.
- Returns answers with inline citations from web sources.

Usage:
    from goliath.integrations.perplexity_search import PerplexitySearchClient

    ps = PerplexitySearchClient()

    # Simple search
    result = ps.search("What is the current price of Bitcoin?")
    print(result["answer"])
    print(result["citations"])

    # Search with specific model
    result = ps.search("Latest developments in fusion energy", model="sonar-pro")

    # Search with system prompt for context
    result = ps.search(
        "Best practices for Python async programming",
        system_prompt="You are a senior Python developer. Be specific and cite sources.",
    )

    # Search with recency filter
    result = ps.search("tech news today", recency_filter="day")
"""

import requests

from goliath import config

_API_BASE = "https://api.perplexity.ai"


class PerplexitySearchClient:
    """Perplexity Sonar API client for AI-powered web search with citations."""

    def __init__(self):
        api_key = config.PERPLEXITY_API_KEY
        if not api_key:
            raise RuntimeError(
                "PERPLEXITY_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/perplexity_search.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    # -- Search ------------------------------------------------------------

    def search(
        self,
        query: str,
        model: str = "sonar",
        system_prompt: str = "Be precise and concise. Cite your sources.",
        max_tokens: int | None = None,
        temperature: float = 0.2,
        search_domain_filter: list[str] | None = None,
        recency_filter: str | None = None,
        return_images: bool = False,
        return_related_questions: bool = False,
    ) -> dict:
        """Run an AI-powered web search.

        Args:
            query:                  Search query in natural language.
            model:                  Model to use ("sonar", "sonar-pro").
            system_prompt:          System instructions for the AI.
            max_tokens:             Max tokens in the response.
            temperature:            Response randomness (0–1).
            search_domain_filter:   Limit search to specific domains.
            recency_filter:         Time filter ("hour", "day", "week", "month").
            return_images:          Include image results.
            return_related_questions: Include related follow-up questions.

        Returns:
            Dict with "answer", "citations", and optionally "images"
            and "related_questions".
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        payload: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "return_images": return_images,
            "return_related_questions": return_related_questions,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if search_domain_filter:
            payload["search_domain_filter"] = search_domain_filter
        if recency_filter:
            payload["search_recency_filter"] = recency_filter

        resp = self.session.post(f"{_API_BASE}/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        result: dict = {
            "answer": message.get("content", ""),
            "citations": data.get("citations", []),
            "model": data.get("model", model),
        }

        if return_images:
            result["images"] = data.get("images", [])
        if return_related_questions:
            result["related_questions"] = data.get("related_questions", [])

        usage = data.get("usage", {})
        if usage:
            result["usage"] = usage

        return result

    def quick_search(self, query: str) -> str:
        """Run a quick search and return just the answer text.

        Args:
            query: Search query.

        Returns:
            Answer string.
        """
        return self.search(query)["answer"]
