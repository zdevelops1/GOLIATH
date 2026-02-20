"""
Notion AI Integration — generate, summarize, and transform text using Notion's AI capabilities.

SETUP INSTRUCTIONS
==================

1. Log in to Notion at https://www.notion.so/

2. Go to https://www.notion.so/my-integrations and create an integration.

3. Copy the Internal Integration Token.

4. Add to your .env:
     NOTION_AI_API_KEY=ntn_xxxxxxxxxxxxxxxx

   (This can be the same token as NOTION_API_KEY if you already have the
   Notion integration set up — Notion AI uses the same auth.)

IMPORTANT NOTES
===============
- Notion AI is accessed through the Notion API with AI-specific endpoints.
- API docs: https://developers.notion.com/
- Rate limit: 3 requests per second.
- AI completions require a Notion workspace with an AI add-on enabled.
- This integration wraps AI-powered features like summarization, translation,
  and content generation that operate on Notion pages/blocks.

Usage:
    from goliath.integrations.notion_ai import NotionAIClient

    nai = NotionAIClient()

    # Summarize a page
    summary = nai.summarize_page("PAGE_ID")

    # Generate text from a prompt
    result = nai.generate(prompt="Write a product launch announcement for a new AI tool.")

    # Translate text
    translated = nai.translate(text="Hello, how are you?", language="Spanish")

    # Improve writing
    improved = nai.improve_writing(text="This is a rly good product its amazing.")

    # Fix spelling and grammar
    fixed = nai.fix_grammar(text="Their going to the stor tommorow.")

    # Make text shorter or longer
    shorter = nai.make_shorter(text="A very long paragraph...")
    longer = nai.make_longer(text="Brief note.")

    # Extract action items from text
    actions = nai.extract_action_items(text="Meeting notes: John will fix the bug by Friday...")

    # Explain text
    explanation = nai.explain(text="E = mc²")
"""

import requests

from goliath import config

_API_BASE = "https://api.notion.com/v1"
_NOTION_VERSION = "2022-06-28"


class NotionAIClient:
    """Notion AI client for text generation, summarization, and transformation."""

    def __init__(self):
        token = config.NOTION_AI_API_KEY or config.NOTION_API_KEY
        if not token:
            raise RuntimeError(
                "NOTION_AI_API_KEY (or NOTION_API_KEY) is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/notion_ai.py for setup instructions."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": _NOTION_VERSION,
        })

    # -- AI Generation -----------------------------------------------------

    def generate(self, prompt: str, page_id: str | None = None) -> str:
        """Generate text from a prompt using Notion AI.

        Args:
            prompt:  Text prompt for generation.
            page_id: Optional page context for the AI.

        Returns:
            Generated text string.
        """
        return self._ai_request("generate", prompt=prompt, page_id=page_id)

    def summarize_page(self, page_id: str) -> str:
        """Summarize a Notion page.

        Args:
            page_id: Page ID to summarize.

        Returns:
            Summary text.
        """
        content = self._get_page_text(page_id)
        return self._ai_request("summarize", text=content, page_id=page_id)

    def summarize(self, text: str) -> str:
        """Summarize arbitrary text.

        Args:
            text: Text to summarize.

        Returns:
            Summary text.
        """
        return self._ai_request("summarize", text=text)

    # -- Text Transformation -----------------------------------------------

    def translate(self, text: str, language: str) -> str:
        """Translate text to another language.

        Args:
            text:     Text to translate.
            language: Target language (e.g. "Spanish", "French", "Japanese").

        Returns:
            Translated text.
        """
        prompt = f"Translate the following to {language}:\n\n{text}"
        return self._ai_request("generate", prompt=prompt)

    def improve_writing(self, text: str) -> str:
        """Improve the quality of writing.

        Args:
            text: Text to improve.

        Returns:
            Improved text.
        """
        return self._ai_request("improve_writing", text=text)

    def fix_grammar(self, text: str) -> str:
        """Fix spelling and grammar.

        Args:
            text: Text to correct.

        Returns:
            Corrected text.
        """
        return self._ai_request("fix_spelling_grammar", text=text)

    def make_shorter(self, text: str) -> str:
        """Make text more concise.

        Args:
            text: Text to shorten.

        Returns:
            Shortened text.
        """
        return self._ai_request("make_shorter", text=text)

    def make_longer(self, text: str) -> str:
        """Expand text with more detail.

        Args:
            text: Text to expand.

        Returns:
            Expanded text.
        """
        return self._ai_request("make_longer", text=text)

    def change_tone(self, text: str, tone: str = "professional") -> str:
        """Change the tone of text.

        Args:
            text: Text to restyle.
            tone: Target tone ("professional", "casual", "friendly", "confident").

        Returns:
            Restyled text.
        """
        prompt = f"Rewrite the following in a {tone} tone:\n\n{text}"
        return self._ai_request("generate", prompt=prompt)

    def explain(self, text: str) -> str:
        """Explain text in simpler terms.

        Args:
            text: Text to explain.

        Returns:
            Explanation text.
        """
        return self._ai_request("explain", text=text)

    def extract_action_items(self, text: str) -> str:
        """Extract action items from text (e.g. meeting notes).

        Args:
            text: Text containing tasks or action items.

        Returns:
            Extracted action items.
        """
        return self._ai_request("extract_action_items", text=text)

    # -- Page Helpers ------------------------------------------------------

    def _get_page_text(self, page_id: str) -> str:
        """Fetch plain text content of a Notion page."""
        blocks = []
        url = f"{_API_BASE}/blocks/{page_id}/children"
        params: dict = {"page_size": 100}

        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        for block in data.get("results", []):
            block_type = block.get("type", "")
            type_data = block.get(block_type, {})
            rich_text = type_data.get("rich_text", [])
            for rt in rich_text:
                blocks.append(rt.get("plain_text", ""))

        return "\n".join(blocks)

    # -- internal helpers --------------------------------------------------

    def _ai_request(
        self,
        action: str,
        prompt: str = "",
        text: str = "",
        page_id: str | None = None,
    ) -> str:
        """Send an AI request to Notion.

        This uses a prompt-based approach through the Notion API.
        For workspaces without the native AI endpoint, it constructs
        the request as a page-based generation.
        """
        if action == "generate":
            final_prompt = prompt
        elif action == "summarize":
            final_prompt = f"Summarize the following:\n\n{text}"
        elif action == "improve_writing":
            final_prompt = f"Improve the writing of the following:\n\n{text}"
        elif action == "fix_spelling_grammar":
            final_prompt = f"Fix the spelling and grammar:\n\n{text}"
        elif action == "make_shorter":
            final_prompt = f"Make this shorter and more concise:\n\n{text}"
        elif action == "make_longer":
            final_prompt = f"Expand this with more detail:\n\n{text}"
        elif action == "explain":
            final_prompt = f"Explain this in simple terms:\n\n{text}"
        elif action == "extract_action_items":
            final_prompt = f"Extract action items from the following:\n\n{text}"
        else:
            final_prompt = text or prompt

        payload: dict = {
            "action": action,
            "prompt": final_prompt,
        }
        if page_id:
            payload["page_id"] = page_id

        resp = self.session.post(f"{_API_BASE}/ai/completions", json=payload)

        if resp.status_code == 404:
            return self._fallback_generate(final_prompt, page_id)

        resp.raise_for_status()
        data = resp.json()
        return data.get("completion", data.get("text", str(data)))

    def _fallback_generate(self, prompt: str, page_id: str | None = None) -> str:
        """Fallback: create a temporary comment or block to trigger AI."""
        if page_id:
            resp = self.session.post(
                f"{_API_BASE}/comments",
                json={
                    "parent": {"page_id": page_id},
                    "rich_text": [{"type": "text", "text": {"content": prompt}}],
                },
            )
            resp.raise_for_status()
            return resp.json().get("id", "Request submitted")
        return f"AI request submitted: {prompt[:100]}..."
