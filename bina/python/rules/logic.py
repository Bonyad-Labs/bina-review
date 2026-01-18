import ast
from typing import List
from ...core.models import Finding, Severity
from ...core.registry import RuleRegistry

@RuleRegistry.register(
    id="L001",
    description="Potential infinite loop.",
    severity=Severity.HIGH,
    language="python"
)
def check_infinite_loop(tree: ast.AST, filename: str) -> List[Finding]:
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            # Check for `while True` or `while 1`
            is_always_true = False
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                is_always_true = True
            elif isinstance(node.test, ast.Constant) and node.test.value == 1:
                is_always_true = True
            
            if is_always_true:
                # Scan body for `break` or `return` or `raise`
                has_exit = False
                for child in ast.walk(node):
                    if isinstance(child, (ast.Break, ast.Return, ast.Raise)):
                        has_exit = True
                        break
                
                if not has_exit:
                    findings.append(Finding(
                        rule_id="L001",
                        message="Potential infinite loop. 'while True' loop has no 'break', 'return', or 'raise'.",
                        severity=Severity.HIGH,
                        file=filename,
                        line=node.lineno,
                        column=node.col_offset
                    ))
    return findings

@RuleRegistry.register(
    id="L002",
    description="Functions claiming sorted/unique output without enforcing it.",
    severity=Severity.LOW,
    language="python"
)
def check_sorted_unique_promise(tree: ast.AST, filename: str) -> List[Finding]:
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name.lower()
            claims_sorted = "sorted" in name
            claims_unique = "unique" in name
            
            if not (claims_sorted or claims_unique):
                continue

            # Check body for usage of sort mechanisms
            usage_found = False
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                    if claims_sorted and child.func.id in ("sorted", "sort"):
                        usage_found = True
                    if claims_unique and child.func.id in ("set", "unique", "distinct"):
                        usage_found = True
                elif isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                    if claims_sorted and child.func.attr == "sort":
                        usage_found = True

            if not usage_found:
                 findings.append(Finding(
                    rule_id="L002",
                    message=f"Function '{node.name}' seems to promise {'sorted' if claims_sorted else 'unique'} results but logic was not found.",
                    severity=Severity.LOW,
                    file=filename,
                    line=node.lineno,
                    column=node.col_offset
                ))
    return findings

@RuleRegistry.register(
    id="L003",
    description="Unchecked None dereference (Simplified).",
    severity=Severity.HIGH,
    language="python"
)
def check_unchecked_none(tree: ast.AST, filename: str) -> List[Finding]:
    findings = []
    # Very basic static check: 
    # Look for assignment x = None, followed by x.attr in the same block without obvious checks.
    # This is highly simplified for V1.
    
    class NoneVisitor(ast.NodeVisitor):
        def __init__(self):
            self.findings = []
            
        def visit_FunctionDef(self, node):
            # Track variables assigned to None
            none_vars = set()
            
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    # Check if x = None
                    if isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                        for target in stmt.targets:
                            if isinstance(target, ast.Name):
                                none_vars.add(target.id)
                
                # Check for usage
                # If we see `x.attr`, flag it.
                # If we see `x = something`, clear it.
                # If we see `if x:`... this is hard to track in visitor order linearly.
                
                # Simplest check: Just find specific pattern `x = None; x.foo` nearby
                pass
            
            # Since simple linear scan is hard in visitor, we scan the body manually
            self.scan_block(node.body, list(none_vars))
            
        def scan_block(self, stmts, dangerous_vars):
            current_dangerous = set(dangerous_vars)
            
            for stmt in stmts:
                # 1. Update state based on assignments
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            if isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                                current_dangerous.add(target.id)
                            else:
                                if target.id in current_dangerous:
                                    current_dangerous.remove(target.id)
                
                # 2. Check for dereferences in this statement
                # We walk the statement looking for Attribute/Subscript access on dangerous vars
                for subnode in ast.walk(stmt):
                    if isinstance(subnode, ast.Attribute) and isinstance(subnode.value, ast.Name):
                        if subnode.value.id in current_dangerous:
                             self.findings.append(Finding(
                                rule_id="L003",
                                message=f"Potential None dereference: '{subnode.value.id}' was assigned None.",
                                severity=Severity.HIGH,
                                file=filename,
                                line=subnode.lineno,
                                column=subnode.col_offset
                            ))
                    elif isinstance(subnode, ast.Subscript) and isinstance(subnode.value, ast.Name):
                        if subnode.value.id in current_dangerous:
                             self.findings.append(Finding(
                                rule_id="L003",
                                message=f"Potential None subscript: '{subnode.value.id}' was assigned None.",
                                severity=Severity.HIGH,
                                file=filename,
                                line=subnode.lineno,
                                column=subnode.col_offset
                            ))
                
                # 3. Naive guard check
                # If statement is `if x:` or `if x is not None`, we ideally clear risk for the body.
                # But handling that recursively is complex.
                # For V1, we just won't support clearing inside blocks, only re-assignment.
                # This ensures we catch the most obvious "Forgot to initialize" errors.
                
    visitor = NoneVisitor()
    visitor.visit(tree)
    findings.extend(visitor.findings)
    return findings
