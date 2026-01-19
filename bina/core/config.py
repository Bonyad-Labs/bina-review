import yaml
import os
import glob
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from .models import Severity

@dataclass
class RuleConfig:
    severity: Optional[Severity] = None
    enabled: bool = True

@dataclass
class Config:
    rules: Dict[str, RuleConfig] = field(default_factory=dict)
    exclude: List[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: str = "bina.yaml") -> 'Config':
        if not os.path.exists(path):
            return cls()
        
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            # Fallback to defaults on error? Or raise?
            # For now, print warning and return default
            print(f"Warning: Failed to load config from {path}: {e}")
            return cls()

        rules = {}
        if 'rules' in data and isinstance(data['rules'], dict):
            for rule_id, rule_data in data['rules'].items():
                # Rule data can be string "HIGH"/"OFF" or dict
                r_config = RuleConfig()
                if isinstance(rule_data, str):
                    if rule_data.upper() == "OFF":
                        r_config.enabled = False
                    elif rule_data.upper() in Severity.__members__:
                        r_config.severity = Severity[rule_data.upper()]
                elif isinstance(rule_data, bool):
                    r_config.enabled = rule_data
                elif isinstance(rule_data, dict):
                    if 'severity' in rule_data and rule_data['severity'] in Severity.__members__:
                        r_config.severity = Severity[rule_data['severity']]
                    if 'enabled' in rule_data:
                        r_config.enabled = bool(rule_data['enabled'])
                
                rules[rule_id] = r_config

        exclude = data.get('exclude', [])
        if not isinstance(exclude, list):
            exclude = []

        return cls(rules=rules, exclude=exclude)

    def is_rule_enabled(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            return self.rules[rule_id].enabled
        return True

    def get_rule_severity(self, rule_id: str, default_severity: Severity) -> Severity:
        if rule_id in self.rules and self.rules[rule_id].severity:
            return self.rules[rule_id].severity
        return default_severity

    def is_path_excluded(self, path: str) -> bool:
        # Check against exclude patterns
        # We need to handle relative paths carefully
        # Simple glob matching
        import fnmatch
        for pattern in self.exclude:
            # Check if path matches pattern
            if fnmatch.fnmatch(path, pattern):
                return True
            # Also check if it matches a directory pattern ending in /**
            # Logic: if pattern is "tests/**", we want to match "tests/foo.py"
            # standard fnmatch might not handle ** recursive logic exactly like gitignore
            # but simple prefix check is often good enough for basics if pattern ends in /
            pass
        return False
