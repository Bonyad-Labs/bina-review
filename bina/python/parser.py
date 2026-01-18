import ast
from typing import List
from ..core.models import Finding
from ..core.registry import RuleRegistry

class PythonAnalyzer:
    @staticmethod
    def analyze(file_path: str) -> List[Finding]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            tree = ast.parse(code, filename=file_path)
            
            # Get Python rules
            rules = RuleRegistry.get_rules_for_language("python")
            findings = []

            for rule in rules:
                # Basic implementation: pass AST and filename to rule
                # Rules are expected to return List[Finding]
                try:
                    results = rule.check_fn(tree, file_path)
                    if results:
                        findings.extend(results)
                except Exception as e:
                    # Generic error handling to prevent one rule from crashing everything
                    # In a real tool we might log this or report as an error finding
                    print(f"Error running rule {rule.id} on {file_path}: {e}")
            
            return findings

        except SyntaxError as e:
            # We could report syntax errors as findings too
            return []
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []
