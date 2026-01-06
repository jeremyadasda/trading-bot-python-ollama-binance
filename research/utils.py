#!/usr/bin/env python3
"""
Utility functions for prompt engineering research.
"""

import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

def load_prompts(file_path: str = "prompts.json") -> List[Dict]:
    """Load prompts from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get("prompts", [])
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        return []

def format_prompt(template: str, variables: Dict[str, str]) -> str:
    """Format a prompt template with the given variables."""
    try:
        return template.format(**variables)
    except KeyError as e:
        logger.error(f"Missing variable in template: {e}")
        raise

def test_prompt(model, tokenizer, prompt: str, max_length: int = 50) -> str:
    """Test a prompt with a given model and tokenizer."""
    try:
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_length=max_length)
        return tokenizer.decode(outputs[0], skip_special_tokens=True)
    except Exception as e:
        logger.error(f"Failed to test prompt: {e}")
        raise