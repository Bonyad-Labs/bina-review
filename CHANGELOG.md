# Changelog

All notable changes to this project will be documented in this file.

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

- **GitHub Action Support**: Official GitHub Action (`AhmadGhadiri/bina-review`) for easy integration into CI/CD pipelines.
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
