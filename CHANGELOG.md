# Changelog

All notable changes to this project will be documented in this file.

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
