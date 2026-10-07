"""Reasoning Agent: Chain-of-Thought style answer generation over grounded context."""

from dataclasses import dataclass

from backend.agents.grounding_agent import GroundedChunk
from backend.models.llm_client import LLMResponse, generate


@dataclass
class ReasoningOutcome:
    response: LLMResponse
    source_texts: list[str]


def reason(query: str, grounded_chunks: list[GroundedChunk], tier: str) -> ReasoningOutcome:
    source_texts = [g.chunk.text for g in grounded_chunks]
    response = generate(query, source_texts, tier)
    return ReasoningOutcome(response=response, source_texts=source_texts)
