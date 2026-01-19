import ast
from typing import List
from ...core.models import Finding, Severity, RuleContext
from ...core.registry import RuleRegistry

@RuleRegistry.register(
    id="B001",
    description="Mutable default argument detected.",
    severity=Severity.MEDIUM,
    language="python"
)
def check_mutable_defaults(context: RuleContext) -> List[Finding]:
    findings = []
    tree = context.tree
    filename = context.filename
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for default in node.args.defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    findings.append(Finding(
                        rule_id="B001",
                        message="Mutable default argument detected. Use None and initialize inside the function.",
                        severity=Severity.MEDIUM,
                        file=filename,
                        line=default.lineno,
                        column=default.col_offset,
                        suggestion="Change default to None and set it to [] inside the function."
                    ))
    return findings

@RuleRegistry.register(
    id="B002",
    description="Silent exception swallowing detected.",
    severity=Severity.HIGH,
    language="python"
)
def check_silent_exception(context: RuleContext) -> List[Finding]:
    findings = []
    tree = context.tree
    filename = context.filename
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            # Check for bare except or except Exception
            is_bare = node.type is None
            is_exception = False
            if isinstance(node.type, ast.Name) and node.type.id == "Exception":
                is_exception = True
            
            if is_bare or is_exception:
                # Check body for strict pass or ...
                if len(node.body) == 1:
                    stmt = node.body[0]
                    if isinstance(stmt, (ast.Pass, ast.Ellipsis)) or (
                        isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis
                    ):
                         findings.append(Finding(
                            rule_id="B002",
                            message="Silent exception swallowing. Log the error or handle it explicitly.",
                            severity=Severity.HIGH,
                            file=filename,
                            line=node.lineno,
                            column=node.col_offset,
                            suggestion="Add a logging statement or specific exception handling logic."
                        ))
    return findings

@RuleRegistry.register(
    id="B003",
    description="Resource usage without proper cleanup (open without with).",
    severity=Severity.MEDIUM,
    language="python"
)
def check_resource_cleanup(context: RuleContext) -> List[Finding]:
    findings = []
    tree = context.tree
    filename = context.filename
    
    # Simple heuristic: Look for `open()` calls that are NOT part of a With statement.
    # This matches usage like `f = open(...)`
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "open":
                # Check if this call is inside a With context header
                # This is tricky with simple walk. 
                # Better approach: Walk the tree, and if we see a With, ignoring the context exprs?
                # Actually, simpler: Any `open()` call is suspect unless it's in the items of a With node.
                
                # However, parent pointers aren't in standard AST.
                # We need to build a parent map or traverse carefully.
                pass
    
    # let's try a different traversal for this one
    class OpenVisitor(ast.NodeVisitor):
        def __init__(self):
            self.findings = []
            
        def visit_With(self, node):
            # 'open' calls in context manager expressions are safe
            # We explicitly do NOT visit the `items` (context expressions) looking for violations
            # BUT we must visit them to check for nested bad stuff? 
            # Actually, `with open(...)` is the *good* pattern.
            # So if `open` is in node.items, it is safe.
            # If `open` is in node.body, it is potentially unsafe (nested), so we visit body.
            
            for item in node.items:
                # We identify this node as safe, so the generic visit_Call won't flag it?
                # No, we can't tag nodes easily.
                
                # Hack: collect all `open` nodes that are in With items
                self._safe_open_nodes = getattr(self, '_safe_open_nodes', set())
                # Scan item.context_expr
                for subnode in ast.walk(item.context_expr):
                    if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Name) and subnode.func.id == "open":
                        self._safe_open_nodes.add(subnode)
            
            self.generic_visit(node)

        def visit_Call(self, node):
            if isinstance(node.func, ast.Name) and node.func.id == "open":
                # Check if this node is in the safe set
                safe_nodes = getattr(self, '_safe_open_nodes', set())
                if node not in safe_nodes:
                     self.findings.append(Finding(
                        rule_id="B003",
                        message="Resource usage without context manager. Use 'with open(...)' to ensure cleanup.",
                        severity=Severity.MEDIUM,
                        file=filename,
                        line=node.lineno,
                        column=node.col_offset,
                        suggestion="Wrap the open() call in a 'with' statement."
                    ))
            self.generic_visit(node)
            
    visitor = OpenVisitor()
    visitor.visit(tree)
    findings.extend(visitor.findings)
    return findings
