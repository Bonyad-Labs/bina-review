# Bina Rules Documentation

Bina includes several built-in rules categorized by their impact on code quality.

## Logic (Correctness)

### L001: Infinite Loop
**Severity**: HIGH
Detects `while True` or `while 1` loops that do not have a clear exit condition (`break`, `return`, or `raise`).

**Bad:**
```python
while True:
    print("Staying alive...")
```

**Good:**
```python
while True:
    if condition():
        break
```

### L002: Sorted/Unique Promise
**Severity**: LOW
Detects functions that imply they return sorted or unique data based on their name (e.g., `get_sorted_items`) but don't seem to use sorting or uniqueness logic (like `sorted()`, `.sort()`, or `set()`).

### L003: Unchecked None Dereference
**Severity**: HIGH
A control-flow aware rule that detects potential `None` dereferences. It tracks variables assigned to `None` and warns if they are accessed via attribute or subscript without a prior `is not None` check.

---

## Best Practices (Maintainability/Performance)

### B001: Mutable Default Argument
**Severity**: MEDIUM
Detects use of mutable objects (list, dict, set) as default arguments in function definitions. 

**Bad:**
```python
def add_item(item, items=[]):
    items.append(item)
    return items
```

### B002: Silent Exception Swallowing
**Severity**: HIGH
Detects `except:` or `except Exception:` blocks that contain only a `pass` or `...`, effectively hiding potential errors.

### B003: Resource Cleanup
**Severity**: MEDIUM
Warns when resources like files are opened using `open()` without a context manager (`with` statement), which can lead to leaked file handles.

---

## Style (Naming)

### N001: Misleading Name
**Severity**: LOW
Detects functions starting with `get_` that do not return any value.
