import os
from typing import List
from .models import Finding
from .registry import RuleRegistry

# We will import this dynamically or strictly in v1 to avoid circular imports if careful
# For now, we will handle imports inside methods or use a clear interface.

class Engine:
    def __init__(self):
        self.registry = RuleRegistry()

    def scan_path(self, path: str) -> List[Finding]:
        findings = []
        if os.path.isfile(path):
            findings.extend(self._analyze_file(path))
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    full_path = os.path.join(root, file)
                    # Skip hidden directories like .git
                    if any(part.startswith('.') for part in full_path.split(os.sep)):
                        continue
                    findings.extend(self._analyze_file(full_path))
        return findings

    def _analyze_file(self, file_path: str) -> List[Finding]:
        if file_path.endswith(".py"):
            from ..python.parser import PythonAnalyzer
            return PythonAnalyzer.analyze(file_path)
        return []
