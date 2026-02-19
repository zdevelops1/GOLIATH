"""
Image Generation Integration — generate images from text prompts via OpenAI DALL-E.

SETUP INSTRUCTIONS
==================

1. Get an OpenAI API key at https://platform.openai.com/api-keys

2. Add it to your .env file:
     OPENAI_API_KEY=sk-...

   If you already have OPENAI_API_KEY set for the OpenAI model provider,
   no extra setup is needed — this integration reuses the same key.

3. (Optional) Set a default model:
     IMAGEGEN_DEFAULT_MODEL=dall-e-3

   Supported models: dall-e-3 (default), dall-e-2, gpt-image-1

Usage:
    from goliath.integrations.imagegen import ImageGenClient

    ig = ImageGenClient()

    # Generate an image and get the URL
    result = ig.generate("A futuristic city skyline at sunset")
    print(result["url"])

    # Generate and save to disk
    path = ig.generate_and_save("A cat wearing a top hat", "cat.png")

    # Generate with specific options
    result = ig.generate(
        "Mountain landscape",
        size="1792x1024",
        quality="hd",
        style="natural",
    )

    # Generate multiple images (dall-e-2 only)
    results = ig.generate("Abstract art", n=4, model="dall-e-2", size="512x512")

    # Edit an existing image with a prompt (dall-e-2 only)
    result = ig.edit(
        image="photo.png",
        prompt="Add a rainbow in the sky",
        mask="mask.png",   # optional — transparent areas will be edited
    )

    # Create a variation of an existing image (dall-e-2 only)
    result = ig.variation("photo.png")
"""

from pathlib import Path

import requests
from openai import OpenAI

from goliath import config

_VALID_SIZES_DALLE3 = {"1024x1024", "1792x1024", "1024x1792"}
_VALID_SIZES_DALLE2 = {"256x256", "512x512", "1024x1024"}


class ImageGenClient:
    """OpenAI DALL-E image generation client."""

    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. "
                "Add it to .env or export as an environment variable. "
                "See integrations/imagegen.py for setup instructions."
            )
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.default_model = getattr(config, "IMAGEGEN_DEFAULT_MODEL", "dall-e-3")

    # -- public API --------------------------------------------------------

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        n: int = 1,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
    ) -> dict | list[dict]:
        """Generate image(s) from a text prompt.

        Args:
            prompt:  Text description of the desired image.
            model:   Model to use. Defaults to IMAGEGEN_DEFAULT_MODEL.
            n:       Number of images (dall-e-3 only supports 1).
            size:    Image size. dall-e-3: 1024x1024, 1792x1024, 1024x1792.
                     dall-e-2: 256x256, 512x512, 1024x1024.
            quality: "standard" or "hd" (dall-e-3 only).
            style:   "vivid" or "natural" (dall-e-3 only).

        Returns:
            Single dict with "url" and "revised_prompt" keys when n=1,
            or list of dicts when n > 1.
        """
        model = model or self.default_model

        kwargs: dict = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
        }

        if model == "dall-e-3":
            kwargs["quality"] = quality
            kwargs["style"] = style

        response = self.client.images.generate(**kwargs)

        results = []
        for img in response.data:
            entry: dict = {"url": img.url}
            if img.revised_prompt:
                entry["revised_prompt"] = img.revised_prompt
            results.append(entry)

        return results[0] if n == 1 else results

    def generate_and_save(
        self,
        prompt: str,
        save_path: str,
        **kwargs,
    ) -> Path:
        """Generate an image and save it to disk.

        Args:
            prompt:    Text description of the desired image.
            save_path: Local file path to save the image.
            **kwargs:  Additional arguments passed to generate().

        Returns:
            Path object of the saved file.
        """
        result = self.generate(prompt, **kwargs)
        url = result["url"] if isinstance(result, dict) else result[0]["url"]
        return self._download(url, save_path)

    def edit(
        self,
        image: str,
        prompt: str,
        mask: str | None = None,
        n: int = 1,
        size: str = "1024x1024",
    ) -> dict | list[dict]:
        """Edit an existing image with a text prompt (dall-e-2 only).

        Args:
            image:  Path to the source image (PNG, must be square, < 4 MB).
            prompt: Description of the desired edit.
            mask:   Path to mask image. Transparent areas indicate where to edit.
            n:      Number of images to generate.
            size:   Output size (256x256, 512x512, or 1024x1024).

        Returns:
            Single dict with "url" key when n=1, or list of dicts when n > 1.
        """
        image_path = Path(image)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image}")

        kwargs: dict = {
            "model": "dall-e-2",
            "image": open(image_path, "rb"),
            "prompt": prompt,
            "n": n,
            "size": size,
        }

        if mask:
            mask_path = Path(mask)
            if not mask_path.exists():
                raise FileNotFoundError(f"Mask not found: {mask}")
            kwargs["mask"] = open(mask_path, "rb")

        try:
            response = self.client.images.edit(**kwargs)
        finally:
            kwargs["image"].close()
            if "mask" in kwargs:
                kwargs["mask"].close()

        results = [{"url": img.url} for img in response.data]
        return results[0] if n == 1 else results

    def variation(
        self,
        image: str,
        n: int = 1,
        size: str = "1024x1024",
    ) -> dict | list[dict]:
        """Create variation(s) of an existing image (dall-e-2 only).

        Args:
            image: Path to the source image (PNG, must be square, < 4 MB).
            n:     Number of variations to generate.
            size:  Output size (256x256, 512x512, or 1024x1024).

        Returns:
            Single dict with "url" key when n=1, or list of dicts when n > 1.
        """
        image_path = Path(image)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image}")

        with open(image_path, "rb") as f:
            response = self.client.images.create_variation(
                model="dall-e-2",
                image=f,
                n=n,
                size=size,
            )

        results = [{"url": img.url} for img in response.data]
        return results[0] if n == 1 else results

    # -- internal helpers --------------------------------------------------

    def _download(self, url: str, save_path: str) -> Path:
        """Download an image from a URL to a local file."""
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()

        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:
            f.write(resp.content)

        return path
