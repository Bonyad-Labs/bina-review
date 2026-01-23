# Bina Static Analysis (بینا)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![CI](https://github.com/Bonyad-Labs/bina-review/actions/workflows/bina-check.yml/badge.svg)](https://github.com/Bonyad-Labs/bina-review/actions/workflows/bina-check.yml)
[![Release](https://img.shields.io/github/v/release/Bonyad-Labs/bina-review)](https://github.com/Bonyad-Labs/bina-review/releases)
[![Marketplace](https://img.shields.io/badge/GitHub%20Marketplace-Bina%20Static%20Analysis-blue?logo=github)](https://github.com/marketplace/actions/bina-static-analysis)


**Deterministic, explainable static analysis for Python — catch real logic bugs without flaky CI failures.**  
Bina provides **deterministic, high-precision results** by analyzing AST patterns without AI, heuristics, or probabilistic models. Designed for teams that require **auditable and predictable** CI gates.

💡 Bina is designed to be **used alongside existing tools** (linters, security scanners, tests), not replace them.

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

### 🔍 What Bina Catches

- Silent logical errors (always-true / always-false conditions)
- Misleading boolean expressions
- Dead or unreachable code paths
- Incorrect exception handling patterns
- Risky control-flow constructs

### 🤔 Why not just use linters or AI tools?

- **Linters** focus on style, not logic
- **Security scanners** focus on known vulnerabilities
- **AI tools** are non-deterministic and hard to audit

Bina focuses on **logical correctness and developer trust**, making it ideal as a stable CI gate.

## Who is this for?
Bina is ideal for:
- Teams introducing static analysis gradually to large codebases.
- Projects requiring strictly deterministic and reproducible results.
- Organizations needing custom, logical rules for internal architectural standards.

Bina is **NOT**:
- A replacement for broad security scanners or fuzzers.
- An AI-based code reviewer.


## 🛡️ Core Principles

- **Deterministic & Auditable**: Every finding maps to a specific AST pattern. Results are reproducible locally and in CI — no AI, no heuristics, no noise.
- **Zero Technical Debt Friction**: Use **Baseline Mode** to ignore existing issues and focus only on new code changes. Adopt Bina gradually without rewriting your entire codebase.
- **Extensible API**: Define organization-specific security or architectural rules in pure Python using our class-based API. If you can write Python, you can write Bina rules.
- **Enterprise Speed**: Optimized AST-based analysis and multiprocessing ensure your CI/CD pipelines remain fast, regardless of project size.
- **GitHub Native**: Built-in support for **SARIF v2.1.0**, enabling deep integration with the GitHub Security tab and inline PR annotations.


## GitHub Action Inputs
> All inputs are optional unless stated otherwise.

| Input | Description | Default |
| --- | --- | --- |
| `path` | Path(s) to scan (space-separated for multiple paths). | `.` |
| `fail_on_high` | If `true`, the action fails if any HIGH severity issues are found. | `true` |
| `config_path` | Path to the `bina.yaml` configuration file. | `bina.yaml` |
| `baseline_path` | Path to the baseline report file. | `bina-report-baseline.json` |
| `token` | GitHub Token for posting PR comments. | `${{ github.token }}` |

## 🛠 Local Usage

Run Bina on your local machine using the CLI:

```bash
# Install the tool
pip install bina-review

# Scan one or more directories/files
bina check src/ scripts/ utils.py

# Scan with a specific profile
bina check . --profile strict
```

## 📚 Documentation

- 📖 [Rule documentation and examples](docs/rules.md)
- 🧩 [Custom rule authoring guide](docs/custom_rules.md)
- ⚙️ [Configuration reference](docs/configuration.md)

👉 See the `/docs` directory for more details.

## Stability & Versioning

Bina follows semantic versioning.
- Minor versions may add new rules.
- Patch versions never change existing rule behavior.

> [!IMPORTANT]
> **Production Ready**: Bina is designed to be a stable CI gate. Rules are optimized for **high precision** to ensure that developers are never blocked by flaky or probabilistic findings.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

Copyright © 2025-2026 Bonyad-Labs
