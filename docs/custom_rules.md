# Custom Rules Guide

Bina allows you to extend its analysis capabilities by writing your own Python-based rules. Custom rules have full access to the Python AST and can be easily integrated into your project.

## Creating a Custom Rule

1. Create a directory for your rules (e.g., `custom_rules/`).
2. Create a Python file for your rule (e.g., `custom_rules/my_rule.py`).
3. Define a class that inherits from `bina.core.models.BaseRule`.

### Example: No Print Rule

This rule flags any usage of the `print()` function.

```python
import ast
from bina.core.models import BaseRule, Severity

class NoPrintRule(BaseRule):
    id = "C001"
    name = "No Print"
    description = "Checks for print() calls."
    severity = Severity.LOW

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.report(
                message="Avoid using print() in production code.",
                node=node,
                suggestion="Use a logging library instead."
            )
        # Always call generic_visit to continue traversing the tree
        self.generic_visit(node)
```

## How it Works

- **`id`**: A unique identifier for your rule (e.g., starting with 'C' for custom).
- **`visit_*` methods**: Inherited from `ast.NodeVisitor`. You can implement `visit_FunctionDef`, `visit_Assign`, `visit_Call`, etc., to target specific code structures.
- **`self.report(message, node, suggestion=None)`**: Call this method to report a finding. The `node` is used to extract the line and column information.
- **`self.generic_visit(node)`**: Crucial for ensuring the visitor continues to children of the current node.

## Configuring Custom Rules

Add the `custom_rules` section to your `bina.yaml`:

```yaml
custom_rules:
  paths:
    - "./custom_rules"
  enable:
    - C001
```

## Running with Custom Rules

Simply run `bina check` as usual. If `bina.yaml` is present, it will load the custom rules automatically.

```bash
bina check . --config bina.yaml
```
