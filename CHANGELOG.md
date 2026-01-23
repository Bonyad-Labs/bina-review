# Changelog

All notable changes to this project will be documented in this file.

## [v0.3.3] - 2026-01-23

### 🚀 Improved Logical Analysis & Multi-Path Support
- **Multi-Path Support**: The `bina check` command now accepts multiple files and directories in a single command (e.g., `bina check src/ scripts/`).
- **Enhanced Unchecked None (L003)**: Significantly improved accuracy by supporting:
    - Truthy checks (`if x:`) as valid None guards.
    - Awareness of short-circuiting logic (e.g., `if x and x.attr`).
    - Fixed false positive when walking nested control flow blocks.
- **Smarter Unique/Sorted Promise (L002)**: Now recognizes logical uniqueness in ID generators that use string concatenation or f-strings with multiple variables (e.g., `f"{name}_{id}"`).
- **Comprehensive Documentation**: Updated `README.md` with multi-path usage examples and real-world scan results from **FastAPI** and **Requests**.
- **GitHub Action Update**: The `path` input in the GitHub Action now supports space-separated multiple paths.

## [v0.3.2] - 2026-01-19

### 🚀 Version 0.3.2: SARIF Output Support
- **SARIF Integration**: Added support for exporting analysis results in SARIF v2.1.0 format.
- **GitHub Code Scanning**: Findings can now be consumed by GitHub's security features.
- **New Reporter**: Implemented `SarifReporter` for schema-compliant JSON generation.
- **CLI & Config**: New `--sarif` flag and `output.sarif` configuration options.

## [v0.3.1] - 2026-01-19

### 🚀 Version 0.3.1: Rule Profiles & Categories
- **Rule Categories**: All built-in rules now declare a category (e.g., `correctness`, `security`, `performance`).
- **Rule Profiles**: Enable rules via high-level profiles like `strict`, `security`, or `performance`.
- **Custom Profiles**: Support for defining team-specific profiles in `bina.yaml`.
- **Precedence Logic**: Implemented granular configuration precedence where individual rule overrides take priority over profile settings.
- **CLI Support**: New `--profile` flag to override configuration on the fly.
- **Future Planning**: Added `FUTURE_IMPROVEMENTS.md` to track strict validation requirements.

## [v0.3.0] - 2026-01-19

### 🚀 Version 3: Custom Rules API & Open Source
- **Custom Rules API**: Implement dynamic loading of Python-based rules. Users can now extend Bina without modifying the core codebase.
- **Unified Rule Model**: Refactored all built-in rules into a class-based `BaseRule` architecture, providing a clean and extensible interface for custom rule developers.
- **Dynamic Rule Discovery**: Added `RuleLoader` to automatically discover and instantiate rules from user-defined directories.
- **Improved Engine Architecture**: Updated the analysis engine and worker processes to safely load and execute custom rules in parallel environments.
- **Official Licensing**: Added Apache License 2.0 to the project.

### 🛠 Architecture
- **Class-based Rules**: Migration of all legacy function-based rules to the `BaseRule` AST visitor model.
- **Dynamic Module Management**: Robust `sys.path` handling in `RuleLoader` for safe multiprocessing with dynamically loaded modules.

## [v0.2.0] - 2026-01-19

### 🚀 Version 2: Production Ready & Team Adoptable

- **Project Configuration (`bina.yaml`)**: Robust support for project-level configuration. Enable/disable rules, override severities, and exclude specific paths using glob patterns.
- **Baseline Mode**: Facilitate gradual adoption by ignoring existing technical debt. Generate a baseline report with `--generate-baseline` and focus only on NEW issues in subsequent runs.
- **Lightweight Control-Flow Awareness**: Significantly reduced false positives in `L003` (Unchecked None) and `L001` (Infinite Loop) by recognizing guard clauses, early returns, and loop breaks.
- **High-Performance Analysis**: Parallel file processing using `multiprocessing` ensures fast execution even on larger codebases.
- **Enhanced GitHub Integration**: Improved PR feedback with summary comments instead of excessive annotations. Rule findings are now grouped and presented clearly in the PR timeline.

### 🛠 Architecture
- **RuleContext API**: Refactored internal rule engine to pass a rich `RuleContext` (AST, Filename, Config) to rules, enabling more sophisticated analysis.
- **Modular Integrations**: Clean separation of GitHub-specific logic into `bina.integrations`.

## [v0.1.0] - 2026-01-18

### 🚀 Features

- **GitHub Action Support**: Official GitHub Action (`bonyad-labs/bina-review`) for easy integration into CI/CD pipelines.
- **Rich Output**: Enhanced CLI and GitHub Action logs with beautifully formatted tables using `rich`.
- **Actionable Suggestions**: Validation findings now include a "Suggestion" column providing specific advice on how to fix the issue.
- **Core Rules**: Includes 7 deterministic rules focusing on logical correctness and best practices:
    - `B001`: Mutable default arguments.
    - `B002`: Silent exception swallowing.
    - `B003`: Resource usage without context manager.
    - `L001`: Potential infinite loops.
    - `L002`: Functions claiming sorted/unique output without enforcement.
    - `L003`: Unchecked None dereference.
    - `N001`: Misleading function names (e.g., `is_` without boolean return).

### 🐛 Bug Fixes

- **Directory Scanning**: Fixed an issue where scanning the current directory (`.`) caused files to be skipped due to hidden file filtering logic.
- **Action Installation**: Fixed `pip install` command in `action.yml` to correctly reference the action path.
