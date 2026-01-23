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
from typing import List, Set
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
            # Scan body for `break` or `return` or `raise`
            has_exit = False
            for child in ast.walk(node):
                if isinstance(child, (ast.Break, ast.Return, ast.Raise)):
                    has_exit = True
                    break
            
            if not has_exit:
                self.report(
                    message="Potential infinite loop. 'while True' loop has no 'break', 'return', or 'raise'.",
                    node=node,
                    suggestion="Add a break statement or a conditional exit."
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

    def visit_FunctionDef(self, node: ast.FunctionDef):
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
            
            # 2. Handle Control Flow (If guards and standard recursion)
            if isinstance(stmt, ast.If):
                # 2.1 Check the test expression for None dereferences
                self.check_dereference(stmt.test, current_dangerous)
                
                guard_var, is_none_check = self.analyze_guard(stmt.test)
                if guard_var and guard_var in current_dangerous:
                    if is_none_check:
                        # `if x is None`: Body is dangerous, orelse is safe
                        self.scan_block(stmt.body, current_dangerous)
                        if self.block_terminates(stmt.body):
                            current_dangerous.remove(guard_var)
                        if stmt.orelse:
                            safe_in_else = set(current_dangerous)
                            if guard_var in safe_in_else:
                                safe_in_else.remove(guard_var)
                            self.scan_block(stmt.orelse, safe_in_else)
                    else: 
                        # `if x is not None`: Body is safe, orelse is dangerous
                        safe_in_body = set(current_dangerous)
                        if guard_var in safe_in_body:
                            safe_in_body.remove(guard_var)
                        self.scan_block(stmt.body, safe_in_body)
                        if stmt.orelse:
                            self.scan_block(stmt.orelse, current_dangerous)
                else:
                    # Standard recursion
                    self.scan_block(stmt.body, current_dangerous)
                    if stmt.orelse:
                        self.scan_block(stmt.orelse, current_dangerous)

            elif isinstance(stmt, ast.While):
                self.check_dereference(stmt.test, current_dangerous)
                self.scan_block(stmt.body, current_dangerous)
                if stmt.orelse:
                    self.scan_block(stmt.orelse, current_dangerous)

            elif isinstance(stmt, ast.For):
                self.check_dereference(stmt.iter, current_dangerous)
                self.scan_block(stmt.body, current_dangerous)
                if stmt.orelse:
                    self.scan_block(stmt.orelse, current_dangerous)

            elif isinstance(stmt, ast.Try):
                # We simplified: just scan all blocks (body, handlers, orelse, finalbody)
                self.scan_block(stmt.body, current_dangerous)
                for handler in stmt.handlers:
                    self.scan_block(handler.body, current_dangerous)
                if stmt.orelse:
                    self.scan_block(stmt.orelse, current_dangerous)
                if stmt.finalbody:
                    self.scan_block(stmt.finalbody, current_dangerous)
            
            else:
                # 3. For all other statements, check for dereferences normally
                self.check_dereference(stmt, current_dangerous)
    
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

        return (None, None)

    def block_terminates(self, stmts):
        """Returns True if the block definitely returns, raises, or breaks/continues."""
        for stmt in stmts:
            if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                return True
        return False

    def check_dereference(self, node, dangerous_vars):
         # Handle short-circuiting in boolean expressions: `if x is not None and x.attr`
         if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
             current = set(dangerous_vars)
             for val in node.values:
                 self.check_dereference(val, current)
                 # After checking this segment, see if it provides a guard for the next ones
                 guard_var, is_none_check = self.analyze_guard(val)
                 if guard_var and guard_var in current and not is_none_check:
                     current.remove(guard_var)
             return

         # We walk the subtree properly, but careful about context.
         # We MUST NOT walk into handles of control flow nodes that we manage
         # via scan_block (body, orelse, finalbody).
         for child in ast.walk(node):
             # Skip blocks if we are looking at the control flow node itself
             if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)) and child == node:
                 continue
             
             if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name):
                 if child.value.id in dangerous_vars:
                     self.report(
                        message=f"Potential None dereference: '{child.value.id}' was assigned None.",
                        node=child,
                        suggestion=f"Check if '{child.value.id}' is None before accessing attributes."
                    )
             elif isinstance(child, ast.Subscript) and isinstance(child.value, ast.Name):
                 if child.value.id in dangerous_vars:
                     self.report(
                        message=f"Potential None subscript: '{child.value.id}' was assigned None.",
                        node=child,
                        suggestion=f"Check if '{child.value.id}' is None before subscripting."
                    )
