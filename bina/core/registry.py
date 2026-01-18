from typing import Callable, Dict, List, Type, Any, Optional
from dataclasses import dataclass
from .models import Finding, Severity

@dataclass
class RuleDefinition:
    id: str
    description: str
    severity: Severity
    language: str  # e.g., "python"
    check_fn: Callable[..., List[Finding]]

class RuleRegistry:
    _rules: Dict[str, RuleDefinition] = {}

    @classmethod
    def register(cls, id: str, description: str, severity: Severity, language: str = "python"):
        """Decorator to register a rule."""
        def decorator(func: Callable):
            cls._rules[id] = RuleDefinition(
                id=id,
                description=description,
                severity=severity,
                language=language,
                check_fn=func
            )
            return func
        return decorator

    @classmethod
    def get_rules_for_language(cls, language: str) -> List[RuleDefinition]:
        return [r for r in cls._rules.values() if r.language == language]

    @classmethod
    def get_all_rules(cls) -> List[RuleDefinition]:
        return list(cls._rules.values())
