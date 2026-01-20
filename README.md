# Bina Static Analysis (بینا)


[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![CI](https://github.com/Bonyad-Labs/bina-review/actions/workflows/bina-check.yml/badge.svg)](https://github.com/Bonyad-Labs/bina-review/actions/workflows/bina-check.yml)
[![Release](https://img.shields.io/github/v/release/Bonyad-Labs/bina-review)](https://github.com/Bonyad-Labs/bina-review/releases)
[![Marketplace](https://img.shields.io/badge/GitHub%20Marketplace-Bina%20Static%20Analysis-blue?logo=github)](https://github.com/marketplace/actions/bina-static-analysis)


**Deterministic, rule-based static analysis for Python — with profiles, baselines, and GitHub-native feedback.**
Bina focuses on **logical correctness, edge cases, and misleading patterns** without using AI, heuristics, or probabilistic models.  
The goal is **predictable, explainable results** that teams can adopt gradually.

---

## 🚀 Quick Start (GitHub Actions)

Add Bina to your repository in **under 1 minute**:

```yaml
name: Bina Static Analysis
on: [pull_request, push]

jobs:
  bina-analysis:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      security-events: write
    steps:
      - uses: actions/checkout@v3
      - name: Run Bina Static Analysis
        uses: bonyad-labs/bina-review@v1
        with:
          path: .
          fail_on_high: true
```

## Why Bina?
Bina differs from other static analysis tools by prioritizing developer trust and predictability:
- **Deterministic**: No AI or heuristics. Results are predictable and can be reproduced locally.
- **Baseline Mode**: Ideal for legacy codebases. Focus only on new issues by ignoring existing technical debt.
- **Custom Rule Engine**: Write your own rules in pure Python using a familiar Class-based API.
- **Gradual Adoption**: Designed for CI environments where stability is more important than catching every possible false-positive.

## Features
- **Deterministic**: No AI, no guessing.
- **Fast**: AST-based analysis and multiprocessing.
- **Rule Profiles & Categories**: Group rules by category and enable them using high-level profiles.
- **SARIF Support**: Export results in v2.1.0 format for GitHub Code Scanning.

## GitHub Action Inputs

| Input | Description | Default |
| --- | --- | --- |
| `path` | Path to the directory or file to scan. | `.` |
| `fail_on_high` | If `true`, the action fails if any HIGH severity issues are found. | `true` |
| `config_path` | Path to the `bina.yaml` configuration file. | `bina.yaml` |
| `baseline_path` | Path to the baseline report file. | `bina-report-baseline.json` |

## 🛠 Local Usage

Run Bina on your local machine using the CLI:

```bash
# Install the tool
pip install bina-review

# Scan a directory
bina check .

# Scan with a specific profile
bina check . --profile strict
```

## SARIF Output

Bina can export analysis results in the SARIF v2.1.0 format. This is useful for integration with GitHub Code Scanning or other static analysis platforms.

### Configuration (`bina.yaml`)

```yaml
output:
  sarif: true
  sarif_path: results.sarif
```

## Rule Profiles

Bina allows you to enable sets of rules using **profiles**. You can choose from built-in profiles or define your own.

### Built-in Profiles

| Profile | Categories Included |
|---|---|
| `default` | `correctness`, `security`, `maintainability` |
| `strict` | All categories |
| `security` | `correctness`, `security` |
| `performance` | `performance` |

## 📚 Documentation

- 📖 [Rule documentation and examples](docs/rules.md)
- 🧩 [Custom rule authoring guide](docs/custom_rules.md)
- ⚙️ [Configuration reference](docs/configuration.md)

👉 See the `/docs` directory for more details.

## Stability & Versioning

Bina follows semantic versioning.
- Minor versions may add new rules
- Patch versions never change rule behavior

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

Copyright © 2025-2026 Bonyad-Labs
