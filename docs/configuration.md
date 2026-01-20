# Configuration Reference

Bina is configured via a `bina.yaml` file in your project root.

## Top-Level Options

### `profile`
Specifies the active rule profile. Default is `default`.
```yaml
profile: strict
```

### `exclude`
A list of path patterns to exclude from analysis. Supports glob patterns.
```yaml
exclude:
  - "tests/**"
  - "setup.py"
```

### `custom_rules`
A list of directories containing custom Python rules.
```yaml
custom_rules:
  - "./my_custom_rules"
```

### `rules`
Enable or disable specific rules manually. These overrides have higher precedence than the profile.
```yaml
rules:
  L001: OFF
  B001: ON
```

## Output Settings

### `output.sarif`
Enable or disable SARIF v2.1.0 output.
```yaml
output:
  sarif: true
```

### `output.sarif_path`
The path where the SARIF report will be saved.
```yaml
output:
  sarif_path: analysis-results.sarif
```

---

## Rule Profiles

Profiles allow you to enable groups of rules based on category.

| Profile | Included Categories |
| --- | --- |
| `default` | `correctness`, `security`, `maintainability` |
| `strict` | All categories |
| `security` | `correctness`, `security` |
| `performance` | `performance` |

### Custom Profiles
You can define your own profiles in `bina.yaml`:
```yaml
profiles:
  quality-gate:
    - correctness
    - architecture
```
