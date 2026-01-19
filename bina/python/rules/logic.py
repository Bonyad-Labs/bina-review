import ast
from typing import List, Set
from ...core.models import Finding, Severity, RuleContext
from ...core.registry import RuleRegistry

@RuleRegistry.register(
    id="L001",
    description="Potential infinite loop.",
    severity=Severity.HIGH,
    language="python"
)
def check_infinite_loop(context: RuleContext) -> List[Finding]:
    findings = []
    tree = context.tree
    filename = context.filename
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
                        column=node.col_offset,
                        suggestion="Add a break statement or a conditional exit."
                    ))
    return findings

@RuleRegistry.register(
    id="L002",
    description="Functions claiming sorted/unique output without enforcing it.",
    severity=Severity.LOW,
    language="python"
)
def check_sorted_unique_promise(context: RuleContext) -> List[Finding]:
    findings = []
    tree = context.tree
    filename = context.filename
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
                    if claims_unique and child.func.attr == "unique":
                         usage_found = True

            if not usage_found:
                 findings.append(Finding(
                    rule_id="L002",
                    message=f"Function '{node.name}' seems to promise {'sorted' if claims_sorted else 'unique'} results but logic was not found.",
                    severity=Severity.LOW,
                    file=filename,
                    line=node.lineno,
                    column=node.col_offset,
                    suggestion=f"Implement {'sorting' if claims_sorted else 'uniqueness'} logic explicitly."
                ))
    return findings

@RuleRegistry.register(
    id="L003",
    description="Unchecked None dereference (Control Flow Aware).",
    severity=Severity.HIGH,
    language="python"
)
def check_unchecked_none(context: RuleContext) -> List[Finding]:
    findings = []
    tree = context.tree
    filename = context.filename

    class ControlFlowVisitor(ast.NodeVisitor):
        def __init__(self):
            self.findings = []
            
        def visit_FunctionDef(self, node):
            # Scan top-level statements of the function
            # We track set of currently 'dangerous' variables (assigned None)
            dangerous_vars = set()
            self.scan_block(node.body, dangerous_vars)
            
        def scan_block(self, stmts, dangerous_vars):
            """
            Scan a block of statements sequentially, respecting control flow updates.
            dangerous_vars: set of variable names currently holding None
            """
            current_dangerous = set(dangerous_vars)
            
            for stmt in stmts:
                # 1. Update state based on assignments (x = None, x = ...)
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            # x = None
                            if isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                                current_dangerous.add(target.id)
                            else:
                                # x = something_else (safe)
                                if target.id in current_dangerous:
                                    current_dangerous.remove(target.id)
                elif isinstance(stmt, ast.AnnAssign):
                     if isinstance(stmt.target, ast.Name):
                         if isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                             current_dangerous.add(stmt.target.id)
                         elif stmt.value: # Assigned something else
                             if stmt.target.id in current_dangerous:
                                 current_dangerous.remove(stmt.target.id)
                
                # 2. Check for De-referencing "dangerous" vars
                self.check_dereference(stmt, current_dangerous)
                
                # 3. Handle Control Flow (If guards)
                if isinstance(stmt, ast.If):
                    guard_var, is_none_check = self.analyze_guard(stmt.test)
                    
                    if guard_var and guard_var in current_dangerous:
                        if is_none_check:
                            # `if x is None`:
                            # Inside body, x is still None (dangerous).
                            self.scan_block(stmt.body, current_dangerous)
                            
                            # If body terminates, then AFTER blocks, x is SAFE (Early Return).
                            if self.block_terminates(stmt.body):
                                current_dangerous.remove(guard_var)
                                
                            # Recurse into else: x is SAFE in else (implied `is not None`)
                            if stmt.orelse:
                                safe_in_else = set(current_dangerous)
                                if guard_var in safe_in_else:
                                    safe_in_else.remove(guard_var)
                                self.scan_block(stmt.orelse, safe_in_else)

                        else: 
                            # `if x is not None`:
                            # Inside body, x is SAFE.
                            safe_in_body = set(current_dangerous)
                            if guard_var in safe_in_body:
                                safe_in_body.remove(guard_var)
                            self.scan_block(stmt.body, safe_in_body)
                            
                            # Inside else, x is still dangerous
                            if stmt.orelse:
                                self.scan_block(stmt.orelse, current_dangerous)
                                
                            # After block? Usually doesn't change outer state unless assigned.
                            pass
                    else:
                        # Standard recursion for non-guard Ifs
                        self.scan_block(stmt.body, current_dangerous)
                        if stmt.orelse:
                            self.scan_block(stmt.orelse, current_dangerous)

                # For loops, While loops, etc. -> naive recursion
                elif isinstance(stmt, (ast.For, ast.While, ast.Try)):
                    self.scan_block(stmt.body, current_dangerous)
                    if stmt.orelse:
                        self.scan_block(stmt.orelse, current_dangerous)
        
        def analyze_guard(self, test_node):
            """Returns (variable_name, is_check_for_none_value)"""
            if isinstance(test_node, ast.Compare) and len(test_node.ops) == 1:
                op = test_node.ops[0]
                left = test_node.left
                right = test_node.comparators[0]
                
                if isinstance(right, ast.Constant) and right.value is None and isinstance(left, ast.Name):
                    if isinstance(op, ast.Is):
                        return (left.id, True)
                    elif isinstance(op, ast.IsNot):
                        return (left.id, False)
            return (None, None)

        def block_terminates(self, stmts):
            """Returns True if the block definitely returns, raises, or breaks/continues."""
            for stmt in stmts:
                if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                    return True
            return False

        def check_dereference(self, node, dangerous_vars):
             # We walk the subtree properly, but careful about context
             for child in ast.walk(node):
                 # Skip the If test itself if we are checking the If statement (handled by scan_block logic, but double check doesn't hurt if we filter correctly)
                 # Actually, ast.walk(node) includes node itself. 
                 # If node is 'If', child is 'If', then 'test', then 'body'...
                 # We want to check dereferences in statements.
                 # But we call check_dereference(stmt).
                 # If stmt is `if x.attr:`, we MUST catch x.attr.
                 # The only thing we shouldn't catch is `if x is None`.
                 # But `x` here is a Name, not Attribute/Subscript. So it's safe.
                 
                 if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name):
                     if child.value.id in dangerous_vars:
                         findings.append(Finding(
                            rule_id="L003",
                            message=f"Potential None dereference: '{child.value.id}' was assigned None.",
                            severity=Severity.HIGH,
                            file=filename,
                            line=child.lineno,
                            column=child.col_offset,
                            suggestion=f"Check if '{child.value.id}' is None before accessing attributes."
                        ))
                 elif isinstance(child, ast.Subscript) and isinstance(child.value, ast.Name):
                     if child.value.id in dangerous_vars:
                         findings.append(Finding(
                            rule_id="L003",
                            message=f"Potential None subscript: '{child.value.id}' was assigned None.",
                            severity=Severity.HIGH,
                            file=filename,
                            line=child.lineno,
                            column=child.col_offset,
                            suggestion=f"Check if '{child.value.id}' is None before subscripting."
                        ))

    visitor = ControlFlowVisitor()
    visitor.visit(tree)
    findings.extend(visitor.findings)
    return findings
