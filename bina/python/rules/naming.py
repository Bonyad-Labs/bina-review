import ast
from typing import List
from ...core.models import Finding, Severity
from ...core.registry import RuleRegistry

@RuleRegistry.register(
    id="N001",
    description="Misleading function name.",
    severity=Severity.LOW,
    language="python"
)
def check_misleading_names(tree: ast.AST, filename: str) -> List[Finding]:
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name.lower()
            
            # 1. 'is_...' should return boolean
            if name.startswith("is_") or name.startswith("has_"):
                # Check for return statement
                has_return = False
                returns_bool = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Return):
                        has_return = True
                        if isinstance(child.value, (ast.Compare, ast.BoolOp)):
                            returns_bool = True
                        elif isinstance(child.value, ast.Constant) and isinstance(child.value.value, bool):
                            returns_bool = True
                
                # If it has returns, but none look boolean (heuristic)
                # This is tricky because `return x` might be bool.
                # So we only flag if NO return is found? 
                pass

            # 2. 'get_...' should return something
            if name.startswith("get_"):
                has_return = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and child.value is not None:
                        has_return = True
                        break
                
                # If function is empty (pass/ellipsis), ignore (abstract method)
                is_abstract = False
                if len(node.body) == 1 and isinstance(node.body[0], (ast.Pass, ast.Expr)):
                    is_abstract = True
                
                if not has_return and not is_abstract:
                     findings.append(Finding(
                        rule_id="N001",
                        message=f"Function '{node.name}' starts with 'get_' but does not return a value.",
                        severity=Severity.LOW,
                        file=filename,
                        line=node.lineno,
                        column=node.col_offset
                    ))

            # 3. 'set_...' should probably not return something? (Debatable, builder pattern)
            
    return findings
