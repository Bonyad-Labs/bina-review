import json
import os
import hashlib
from typing import List, Dict, Set
from .models import Finding

class BaselineManager:
    def __init__(self, baseline_path: str = "bina-report-baseline.json"):
        self.baseline_path = baseline_path
        self.baseline_fingerprints: Set[str] = set()
        self.loaded = False

    def load(self):
        """Load baseline from file if it exists."""
        if os.path.exists(self.baseline_path):
            try:
                with open(self.baseline_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.baseline_fingerprints = set(data)
                self.loaded = True
            except Exception as e:
                print(f"Warning: Failed to load baseline from {self.baseline_path}: {e}")

    def save(self, findings: List[Finding]):
        """Save current findings as the new baseline."""
        fingerprints = [self._compute_fingerprint(f) for f in findings]
        try:
            with open(self.baseline_path, 'w') as f:
                json.dump(fingerprints, f, indent=2)
            print(f"Baseline saved to {self.baseline_path} with {len(fingerprints)} issues.")
        except Exception as e:
            print(f"Error saving baseline: {e}")

    def filter(self, findings: List[Finding]) -> List[Finding]:
        """Return only findings that are NOT in the baseline."""
        if not self.loaded:
            return findings
        
        new_findings = []
        for f in findings:
            fp = self._compute_fingerprint(f)
            if fp not in self.baseline_fingerprints:
                new_findings.append(f)
        return new_findings

    def _compute_fingerprint(self, finding: Finding) -> str:
        """
        Compute a stable hash for a finding.
        WE incorporate: file path relative to root, rule_id, and line content context?
        Ideally context helps if lines shift. For MVP V2, just file + rule + line/col or nearby context.
        Let's try file + rule + line first context hash if possible?
        For now: simple signature: rule_id|filename|line|column
        Ideally we want to be resilient to line shifts, but that requires snippet context.
        If models.py has 'code_snippet', use that?
        V1 models might not have snippet populated reliably yet.
        Let's use a combination.
        """
        # If we have snippet, it's better. But simpler: Rule + File + Line
        # We enforce relative paths in 'file' field ideally.
        keys = [finding.rule_id, finding.file, str(finding.line)]
        if finding.code_snippet:
             # Hash the snippet to allow movement?
             # Or just include it to distinguish different errors on same line?
             keys.append(hashlib.md5(finding.code_snippet.encode('utf-8')).hexdigest())
        
        raw_key = "|".join(keys)
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
