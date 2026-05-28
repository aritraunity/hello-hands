"""Text analysis for selecting arm animations."""

import json
from dataclasses import dataclass

import requests


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "ibm/granite4.1:3b"

ANIMATION_LABELS = (
    "Greeting",
    "Negative",
    "Thinking",
    "Positive",
)


@dataclass(frozen=True)
class AnalysisResult:
    """Text analysis result."""

    animation: str
    confidence: float
    reason: str

    def to_dict(self) -> dict[str, object]:
        """Convert result to JSON-safe dictionary."""
        return {
            "animation": self.animation,
            "confidence": round(self.confidence, 3),
            "reason": self.reason,
        }


def analyze_text(text: str) -> AnalysisResult:
    """Analyze text and select the best animation."""
    cleaned_text = text.strip()

    if not cleaned_text:
        return AnalysisResult(
            animation="Thinking",
            confidence=0.25,
            reason="Empty input defaults to Thinking.",
        )

    ollama_result = _analyze_with_ollama(cleaned_text)
    if ollama_result is not None:
        return ollama_result

    return _analyze_with_rules(cleaned_text)


def _analyze_with_ollama(text: str) -> AnalysisResult | None:
    """Use local Ollama model to classify text."""
    prompt = (
        "You classify user text into one robot arm animation.\n"
        "Allowed animations: Greeting, Negative, Thinking, Positive.\n"
        "Greeting means hello, hi, welcome, goodbye, waving.\n"
        "Negative means no, rejection, disagreement, refusal, bad, cancel.\n"
        "Thinking means uncertainty, maybe, question, doubt, waiting, pondering.\n"
        "Positive means yes, approval, good, success, thanks, agreement.\n"
        "Return only strict JSON using this schema:\n"
        '{"animation":"Greeting","confidence":0.0,"reason":"short reason"}\n'
        f"Text: {text}"
    )

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                },
            },
            timeout=8,
        )
        response.raise_for_status()
    except requests.RequestException:
        return None

    raw_response = response.json().get("response", "")
    parsed_json = _extract_json(str(raw_response))

    if parsed_json is None:
        return None

    animation = str(parsed_json.get("animation", "Thinking"))
    confidence = float(parsed_json.get("confidence", 0.5))
    reason = str(parsed_json.get("reason", "Classified by Ollama."))

    if animation not in ANIMATION_LABELS:
        return None

    return AnalysisResult(
        animation=animation,
        confidence=max(min(confidence, 1.0), 0.0),
        reason=reason,
    )


def _analyze_with_rules(text: str) -> AnalysisResult:
    """Fallback BERT-like semantic scoring using intent keyword groups."""
    lowered_text = text.lower()

    scores = {
        "Greeting": _score_text(
            lowered_text,
            ("hello", "hi", "hey", "welcome", "greetings", "bye", "goodbye"),
        ),
        "Negative": _score_text(
            lowered_text,
            ("no", "not", "never", "reject", "bad", "wrong", "cancel", "stop"),
        ),
        "Thinking": _score_text(
            lowered_text,
            ("maybe", "think", "unsure", "question", "why", "how", "hmm", "?"),
        ),
        "Positive": _score_text(
            lowered_text,
            ("yes", "good", "great", "ok", "okay", "sure", "thanks", "correct"),
        ),
    }

    animation = max(scores, key=scores.get)
    best_score = scores[animation]

    if best_score == 0:
        return AnalysisResult(
            animation="Thinking",
            confidence=0.3,
            reason="No strong intent match; defaulted to Thinking.",
        )

    total_score = sum(scores.values())
    confidence = best_score / total_score if total_score else 0.3

    return AnalysisResult(
        animation=animation,
        confidence=confidence,
        reason="Selected by fallback semantic keyword comparison.",
    )


def _score_text(text: str, keywords: tuple[str, ...]) -> int:
    """Score text against a keyword group."""
    return sum(1 for keyword in keywords if keyword in text)


def _extract_json(raw_text: str) -> dict[str, object] | None:
    """Extract the first JSON object from model output."""
    start_index = raw_text.find("{")
    end_index = raw_text.rfind("}")

    if start_index == -1 or end_index == -1:
        return None

    try:
        parsed = json.loads(raw_text[start_index : end_index + 1])
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict):
        return None

    return parsed