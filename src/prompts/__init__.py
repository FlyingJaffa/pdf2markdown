"""
Prompts Module
Contains all prompt templates used in the PDF processing pipeline.
"""

from .prompt_templates import get_interpretation_prompt, get_cleanup_prompt, get_text_page_prompt

__all__ = ['get_interpretation_prompt', 'get_cleanup_prompt', 'get_text_page_prompt'] 