"""Router Agent: query intent classification (feeds AQR complexity scoring)."""

import re
from dataclasses import dataclass

INTENT_PATTERNS = {
    "factual": re.compile(r"\b(what is|what are|define|when|where|who)\b", re.IGNORECASE),
    "analytical": re.compile(r"\b(why|how|analyze|compare|evaluate)\b", re.IGNORECASE),
    "procedural": re.compile(r"\b(how do i|steps|procedure|process for)\b", re.IGNORECASE),
    "safety": re.compile(r"\b(safe|safety|hazard|risk|emergency|shutdown)\b", re.IGNORECASE),
}


@dataclass
class RoutedQuery:
    intent: str
    query: str


def classify_intent(query: str) -> str:
    for intent, pattern in INTENT_PATTERNS.items():
        if pattern.search(query):
            return intent
    return "general"


def route(query: str) -> RoutedQuery:
    return RoutedQuery(intent=classify_intent(query), query=query.strip())
