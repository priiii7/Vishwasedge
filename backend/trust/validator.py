"""Output guardrails: regex-based PII/unsafe-pattern checks + grounding check."""

import re
from dataclasses import dataclass, field

UNSAFE_PATTERNS = [
    re.compile(r"\b(?:ignore (?:all )?(?:previous|prior) instructions)\b", re.IGNORECASE),
    re.compile(r"\bssn\s*[:#]?\s*\d{3}-?\d{2}-?\d{4}\b", re.IGNORECASE),
]


@dataclass
class ValidationResult:
    passed: bool
    warnings: list[str] = field(default_factory=list)


def validate_query(query: str) -> ValidationResult:
    warnings = [f"matched unsafe pattern: {p.pattern}" for p in UNSAFE_PATTERNS if p.search(query)]
    return ValidationResult(passed=not warnings, warnings=warnings)


def validate_response(response: str, source_texts: list[str]) -> ValidationResult:
    """Lightweight grounding guardrail: flag if the response shares almost no
    vocabulary overlap with any retrieved source (possible hallucination)."""
    warnings: list[str] = []
    response_tokens = set(re.findall(r"[a-z0-9]+", response.lower()))
    if source_texts and response_tokens:
        best_overlap = max(
            (len(response_tokens & set(re.findall(r"[a-z0-9]+", src.lower()))) / len(response_tokens))
            for src in source_texts
        )
        if best_overlap < 0.08:
            warnings.append("low lexical overlap with retrieved sources — possible ungrounded content")
    for pattern in UNSAFE_PATTERNS:
        if pattern.search(response):
            warnings.append(f"response matched unsafe pattern: {pattern.pattern}")
    return ValidationResult(passed=not warnings, warnings=warnings)
