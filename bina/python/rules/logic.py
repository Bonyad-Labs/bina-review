# Copyright 2025-2026 Bonyad-Labs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast
from typing import List, Set, Dict
from ...core.models import Finding, Severity, RuleContext, BaseRule

class InfiniteLoopRule(BaseRule):
    id = "L001"
    name = "Infinite Loop"
    description = "Potential infinite loop."
    severity = Severity.HIGH
    category = "correctness"

    def visit_While(self, node: ast.While):
        # Check for `while True` or `while 1`
        is_always_true = False
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            is_always_true = True
        elif isinstance(node.test, ast.Constant) and node.test.value == 1:
            is_always_true = True
        
        if is_always_true:
            # Scan body for `break`, `return`, `raise`, `yield`, or `yield from`
            has_exit = False
            for child in ast.walk(node):
                if isinstance(child, (ast.Break, ast.Return, ast.Raise, ast.Yield, ast.YieldFrom)):
                    has_exit = True
                    break
            
            if not has_exit:
                self.report(
                    message="Potential infinite loop. 'while True' loop has no 'break', 'return', 'raise', or 'yield'.",
                    node=node,
                    suggestion="Add a break statement, a yield, or a conditional exit."
                )

class SortedUniquePromiseRule(BaseRule):
    id = "L002"
    name = "Sorted/Unique Promise"
    description = "Functions claiming sorted/unique output without enforcing it."
    severity = Severity.LOW
    category = "correctness"

    def visit_FunctionDef(self, node: ast.FunctionDef):
        name = node.name.lower()
        claims_sorted = "sorted" in name
        claims_unique = "unique" in name
        
        if not (claims_sorted or claims_unique):
            return

        # Check body for usage of sort/uniqueness mechanisms
        usage_found = False
        for child in ast.walk(node):
            # 1. Standard library calls and common uniqueness indicators
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if claims_sorted and child.func.id in ("sorted", "sort"):
                    usage_found = True
                if claims_unique and child.func.id in ("set", "unique", "distinct", "uuid4", "sha256", "md5"):
                    usage_found = True
            elif isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                if claims_sorted and child.func.attr == "sort":
                    usage_found = True
                if claims_unique and child.func.attr in ("unique", "distinct"):
                    usage_found = True
            
            # 2. Logical uniqueness: ID generation via concatenation/formatting
            if claims_unique and not usage_found:
                if isinstance(child, ast.JoinedStr):
                    # Count variables/attributes being formatted into the string
                    vars_count = sum(1 for v in child.values if isinstance(v, ast.FormattedValue))
                    if vars_count >= 2:
                        usage_found = True
                elif isinstance(child, ast.BinOp) and isinstance(child.op, ast.Add):
                    # Check for chains of addition involving multiple variables/attributes
                    vars_in_concat = [n for n in ast.walk(child) if isinstance(n, (ast.Name, ast.Attribute))]
                    if len(vars_in_concat) >= 2:
                        usage_found = True

            if usage_found:
                break

        if not usage_found:
             self.report(
                message=f"Function '{node.name}' seems to promise {'sorted' if claims_sorted else 'unique'} results but logic was not found.",
                node=node,
                suggestion=f"Implement {'sorting' if claims_sorted else 'uniqueness'} logic explicitly."
            )

class UncheckedNoneRule(BaseRule):
    id = "L003"
    name = "Unchecked None Dereference"
    description = "Unchecked None dereference (Control Flow Aware)."
    severity = Severity.HIGH
    category = "correctness"

    def __init__(self):
        super().__init__()
        self.guards = {} # Mapping of func_name -> set of guarded argument indices

    def visit_Module(self, node: ast.Module):
        # Pass 1: Infer guards from all function definitions in the module
        self.guards = self.infer_guards(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Pass 2: Regular scan using inferred guards
        self.scan_block(node.body, set())

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.scan_block(node.body, set())

    def infer_guards(self, tree) -> Dict[str, Set[int]]:
        """
        Identify functions that raise or return when an argument is None.
        Returns a map of function name to indices of guarded arguments.
        """
        guards = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                arg_names = [arg.arg for arg in node.args.args]
                guarded_indices = set()
                
                # Simple check: does the function have `if arg is None: raise ...`?
                for stmt in node.body:
                    if isinstance(stmt, ast.If):
                        guard_var, is_none_check = self.analyze_guard(stmt.test)
                        if guard_var in arg_names and is_none_check:
                            # Check if the body terminates (raises or returns)
                            if self.block_terminates(stmt.body):
                                try:
                                    idx = arg_names.index(guard_var)
                                    guarded_indices.add(idx)
                                except ValueError:
                                    pass
                    elif isinstance(stmt, ast.Assert):
                         guard_var, is_none_check = self.analyze_guard(stmt.test)
                         if guard_var in arg_names and not is_none_check:
                             # assert x is not None
                             try:
                                idx = arg_names.index(guard_var)
                                guarded_indices.add(idx)
                             except ValueError:
                                pass
                
                if guarded_indices:
                    guards[node.name] = guarded_indices
        return guards

    def scan_block(self, stmts, dangerous_vars) -> Set[str]:
        """
        Scan a block of statements sequentially, respecting control flow updates.
        dangerous_vars: set of variable names currently holding None
        Returns the set of dangerous variables at the end of the block.
        """
        current_dangerous = set(dangerous_vars)
        
        for stmt in stmts:
            # 1. Update state based on assignments (x = None, x = ...)
            if isinstance(stmt, ast.Assign):
                # Check if it's an assignment to None
                is_to_none = isinstance(stmt.value, ast.Constant) and stmt.value.value is None
                
                for target in stmt.targets:
                    for name_id in self.get_rebound_names(target):
                        if is_to_none:
                            current_dangerous.add(name_id)
                        else:
                            # Safe reassignment
                            if name_id in current_dangerous:
                                current_dangerous.remove(name_id)
            elif isinstance(stmt, ast.AnnAssign):
                 if isinstance(stmt.target, ast.Name):
                     is_to_none = isinstance(stmt.value, ast.Constant) and stmt.value.value is None
                     if is_to_none:
                         current_dangerous.add(stmt.target.id)
                     elif stmt.value: # Assigned something else
                         if stmt.target.id in current_dangerous:
                             current_dangerous.remove(stmt.target.id)
            
            # 2. Handle Control Flow (If guards and standard recursion)
            elif isinstance(stmt, ast.If):
                # 2.1 Check the test expression for None dereferences
                self.check_dereference(stmt.test, current_dangerous)
                
                guard_var, is_none_check = self.analyze_guard(stmt.test)
                if guard_var and guard_var in current_dangerous:
                    if is_none_check:
                        # `if x is None`: Body is dangerous, orelse is safe
                        body_state = self.scan_block(stmt.body, current_dangerous)
                        
                        # Lazy Init Pattern: if x was dangerous, but it's safe at the end of `if x is None` block,
                        # then it's safe for the rest of path (since if we skip block, x was NOT None).
                        if guard_var not in body_state or self.block_terminates(stmt.body):
                             current_dangerous.remove(guard_var)

                        if stmt.orelse:
                            safe_in_else = set(current_dangerous)
                            if guard_var in safe_in_else:
                                safe_in_else.remove(guard_var)
                            else_state = self.scan_block(stmt.orelse, safe_in_else)
                            # After If/Else: Union of danger
                            current_dangerous.update(else_state)
                            current_dangerous.update(body_state)
                        else:
                            # No else: current_dangerous already updated via body_state check above
                            pass
                    else: 
                        # `if x is not None`: Body is safe, orelse is dangerous
                        safe_in_body = set(current_dangerous)
                        if guard_var in safe_in_body:
                            safe_in_body.remove(guard_var)
                        body_state = self.scan_block(stmt.body, safe_in_body)
                        
                        if stmt.orelse:
                            else_state = self.scan_block(stmt.orelse, current_dangerous)
                            # After If/Else: Union of danger
                            current_dangerous.update(body_state)
                            current_dangerous.update(else_state)
                        else:
                            # No else: if it's safe in body, it's still dangerous outside (skipped the block)
                            # UNLESS the body terminates, but that's a different check.
                            pass
                else:
                    # Generic If: pessimistic union
                    body_state = self.scan_block(stmt.body, current_dangerous)
                    else_state = self.scan_block(stmt.orelse, current_dangerous) if stmt.orelse else current_dangerous
                    
                    # Update state for the REST of the current block
                    current_dangerous = body_state.union(else_state)

            elif isinstance(stmt, ast.While):
                self.check_dereference(stmt.test, current_dangerous)
                self.scan_block(stmt.body, current_dangerous)
                # Note: We don't update current_dangerous from while body because it might not run

            elif isinstance(stmt, (ast.For, ast.AsyncFor)):
                self.check_dereference(stmt.iter, current_dangerous)
                # Inside the loop, the target variables are rebound (safe)
                body_dangerous = set(current_dangerous)
                for name_id in self.get_rebound_names(stmt.target):
                    if name_id in body_dangerous:
                        body_dangerous.remove(name_id)
                self.scan_block(stmt.body, body_dangerous)
                # Note: We don't update current_dangerous from while/for body 
                # because the loop might not run at all.

            elif isinstance(stmt, (ast.With, ast.AsyncWith)):
                # Check expressions in with_items
                for item in stmt.items:
                    self.check_dereference(item.context_expr, current_dangerous)
                    if item.optional_vars:
                         # with ... as f: (Safe reassignment)
                         for name_id in self.get_rebound_names(item.optional_vars):
                             if name_id in current_dangerous:
                                 current_dangerous.remove(name_id)
                
                # Scan the body and update state
                current_dangerous = self.scan_block(stmt.body, current_dangerous)

            elif isinstance(stmt, ast.Try):
                self.scan_block(stmt.body, current_dangerous)
                for handler in stmt.handlers:
                    self.scan_block(handler.body, current_dangerous)
                if stmt.orelse:
                    self.scan_block(stmt.orelse, current_dangerous)
                if stmt.finalbody:
                    self.scan_block(stmt.finalbody, current_dangerous)
            
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                # 3. Check for guard calls: self.check_response(response)
                func_node = stmt.value.func
                func_name = None
                if isinstance(func_node, ast.Name):
                    func_name = func_node.id
                elif isinstance(func_node, ast.Attribute):
                    func_name = func_node.attr
                
                if func_name in self.guards:
                    # Determine if this is a method call (e.g., self.foo() or obj.foo())
                    # In a method call, the first argument in the definition corresponds 
                    # to the object itself, so call arguments shift by 1.
                    is_method_call = isinstance(func_node, ast.Attribute)
                    
                    for param_idx in self.guards[func_name]:
                        call_arg_idx = param_idx - 1 if is_method_call else param_idx
                        
                        if 0 <= call_arg_idx < len(stmt.value.args):
                            arg = stmt.value.args[call_arg_idx]
                            if isinstance(arg, ast.Name) and arg.id in current_dangerous:
                                current_dangerous.remove(arg.id)
                
                # Still check for dereferences in arguments
                self.check_dereference(stmt, current_dangerous)
            elif isinstance(stmt, ast.Assert):
                # asset x is not None: remove x from dangerous
                guard_var, is_none_check = self.analyze_guard(stmt.test)
                if guard_var and guard_var in current_dangerous and not is_none_check:
                    current_dangerous.remove(guard_var)
                # Still check for dereferences in the assert expression itself
                self.check_dereference(stmt.test, current_dangerous)

            else:
                # 4. For all other statements, check for dereferences normally
                self.check_dereference(stmt, current_dangerous)
        
        return current_dangerous

    def get_rebound_names(self, node) -> Set[str]:
        """
        Recursively find all variable names being rebound in an assignment target.
        Handles unpacking (Tuple/List) and Starred targets.
        Crucially, it skips Attribute and Subscript bases because they are not being rebound.
        """
        names = set()
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                names.update(self.get_rebound_names(elt))
        elif isinstance(node, ast.Starred):
            names.update(self.get_rebound_names(node.value))
        # Note: Attribute and Subscript are intentionally omitted as they don't 'rebind' the base variable name
        return names
    
    def analyze_guard(self, test_node):
        """Returns (variable_name, is_check_for_none_value)"""
        # 1. Standard `is None` and `is not None`
        if isinstance(test_node, ast.Compare) and len(test_node.ops) == 1:
            op = test_node.ops[0]
            left = test_node.left
            right = test_node.comparators[0]
            
            if isinstance(right, ast.Constant) and right.value is None and isinstance(left, ast.Name):
                if isinstance(op, ast.Is):
                    return (left.id, True)
                elif isinstance(op, ast.IsNot):
                    return (left.id, False)
        
        # 2. Truthy checks: `if x:`
        if isinstance(test_node, ast.Name):
            return (test_node.id, False)
        
        # 3. Falsy checks: `if not x:`
        if isinstance(test_node, ast.UnaryOp) and isinstance(test_node.op, ast.Not):
            if isinstance(test_node.operand, ast.Name):
                return (test_node.operand.id, True)

        # 4. Built-in guards: `isinstance(x, T)` or `hasattr(x, 'attr')`
        if isinstance(test_node, ast.Call) and isinstance(test_node.func, ast.Name):
            if test_node.func.id in ("isinstance", "hasattr") and len(test_node.args) >= 1:
                arg = test_node.args[0]
                if isinstance(arg, ast.Name):
                    return (arg.id, False)

        return (None, None)

    def block_terminates(self, stmts):
        """Returns True if the block definitely returns, raises, or breaks/continues."""
        for stmt in stmts:
            if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                return True
        return False

    def check_dereference(self, node, dangerous_vars):
         # 1. Handle short-circuiting in boolean expressions
         if isinstance(node, ast.BoolOp):
             current = set(dangerous_vars)
             if isinstance(node.op, ast.And):
                 # `if x is not None and x.attr`: x is safe for later operands
                 for val in node.values:
                     self.check_dereference(val, current)
                     guard_var, is_none_check = self.analyze_guard(val)
                     if guard_var and guard_var in current and not is_none_check:
                         current.remove(guard_var)
                 return
             elif isinstance(node.op, ast.Or):
                 # `if x is None or x.attr`: if we reach x.attr, x was NOT None
                 for val in node.values:
                     self.check_dereference(val, current)
                     guard_var, is_none_check = self.analyze_guard(val)
                     if guard_var and guard_var in current and is_none_check:
                         current.remove(guard_var)
                 return

         # 2. Check current node
         if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
             if node.value.id in dangerous_vars:
                 # Exempt magic attributes like __class__ which are safe on None
                 if not (node.attr.startswith("__") and node.attr.endswith("__")):
                     self.report(
                        message=f"Potential None dereference: '{node.value.id}' was assigned None.",
                        node=node,
                        suggestion=f"Check if '{node.value.id}' is None before accessing attributes."
                    )
         elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
             if node.value.id in dangerous_vars:
                 self.report(
                    message=f"Potential None subscript: '{node.value.id}' was assigned None.",
                    node=node,
                    suggestion=f"Check if '{node.value.id}' is None before subscripting."
                )
         
         # 3. Recurse into children
         # Filter out fields that are handled by scan_block to avoid double-counting or entering blocks
         skip_fields = set()
         if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith, ast.Try)):
             skip_fields = {'body', 'orelse', 'finalbody', 'handlers'}
         
         for field, value in ast.iter_fields(node):
             if field in skip_fields:
                 continue
             if isinstance(value, list):
                 for item in value:
                     if isinstance(item, ast.AST):
                         self.check_dereference(item, dangerous_vars)
             elif isinstance(value, ast.AST):
                 self.check_dereference(value, dangerous_vars)
