"""LLM integration for enhanced reasoning extraction."""

from reasoning_core.llm.base import LLMService
from reasoning_core.llm.ollama_service import OllamaService

__all__ = ["LLMService", "OllamaService"]
