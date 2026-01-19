from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any, Dict

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

@dataclass
class Position:
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None

@dataclass
class Finding:
    rule_id: str
    message: str
    severity: Severity
    file: str
    line: int
    column: int
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None

@dataclass
class RuleContext:
    """Context passed to rules during execution."""
    filename: str
    tree: Any  # ast.AST
    config: Optional[Any] = None  # Config object
    # Future: control flow state, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
