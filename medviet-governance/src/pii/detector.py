# src/pii/detector.py
from dataclasses import dataclass
import re

from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider


@dataclass
class SimpleResult:
    entity_type: str
    start: int
    end: int
    score: float = 0.85


class _NoOpRegistry:
    def add_recognizer(self, _recognizer) -> None:
        return None


class VietnameseAnalyzer:
    def __init__(self):
        self.registry = _NoOpRegistry()
        self._patterns = {
            "PERSON": re.compile(r"\b[A-ZÀ-ỸĐ][a-zà-ỹđ]+(?:\s+[A-ZÀ-ỸĐ][a-zà-ỹđ]+){1,3}\b"),
            "EMAIL_ADDRESS": re.compile(r"[\w.+\-]+@[\w\-]+\.[\w\.-]+"),
            "VN_CCCD": re.compile(r"\b\d{11,12}\b"),
            "VN_PHONE": re.compile(r"\b(?:0)?(?:3|5|7|8|9)\d{8}\b"),
        }

    def analyze(self, text: str, language: str = "vi", entities: list | None = None):
        requested_entities = entities or list(self._patterns.keys())
        results = []
        for entity in requested_entities:
            pattern = self._patterns.get(entity)
            if pattern is None:
                continue
            for match in pattern.finditer(text):
                results.append(SimpleResult(entity, match.start(), match.end()))
        return results

def build_vietnamese_analyzer() -> AnalyzerEngine:
    """
    TODO: Xây dựng AnalyzerEngine với các recognizer tùy chỉnh cho VN.
    """
    return VietnameseAnalyzer()


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    """
    TODO: Detect PII trong text tiếng Việt.
    Trả về list các RecognizerResult.
    Entities cần detect: PERSON, EMAIL_ADDRESS, VN_CCCD, VN_PHONE
    """
    results = analyzer.analyze(
        text=text,
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"]
    )
    return results
