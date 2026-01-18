# Bina (بینا)

**Bina** is a deterministic, rule-based static analysis tool for Python.
It focuses on logical correctness, edge cases, and misleading patterns without using AI or heuristics.

## Features (v1)
- **Deterministic**: No AI, no guessing.
- **Fast**: AST-based analysis.
- **Rule-based**: easy to extend.

## Installation
```bash
poetry install
```

## Usage
```bash
poetry run bina check <path_to_file_or_dir>
```

## GitHub Action Usage

To use Bina in your own repository, add this to your `.github/workflows/main.yml`:

```yaml
steps:
  - uses: actions/checkout@v3
  
  - name: Run Bina Static Analysis
    uses: AhmadGhadiri/bina-review@v1
    with:
      path: .
      fail_on_high: true
```
