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

import click
from rich.console import Console
from rich.table import Table
from .core.engine import Engine
from .core.registry import RuleRegistry

# Import rules to register them
import bina.python.rules

console = Console(stderr=True)

@click.group()
def main():
    """Bina: Static Analysis Tool."""
    pass

@main.command()
@click.argument("paths", nargs=-1)
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.option("--config", "config_path", default="bina.yaml", help="Path to configuration file")
@click.option("--baseline", "baseline_path", default="bina-report-baseline.json", help="Path to baseline file")
@click.option("--generate-baseline", is_flag=True, help="Generate a new baseline from current findings")
@click.option("--show-baseline", is_flag=True, help="Show baseline issues in report")
@click.option("--profile", help="Rule profile to use (e.g., security, strict)")
@click.option("--sarif", "sarif_out", help="Output findings in SARIF format to the specified path")
def check(paths, json_output, config_path, baseline_path, generate_baseline, show_baseline, profile, sarif_out):
    """Run static analysis on the given paths."""
    from .core.config import Config
    from .core.baseline import BaselineManager

    # Default to current directory if no paths provided
    if not paths:
        paths = (".",)

    # Load Config
    config = Config.load(config_path)
    if profile:
        config.profile = profile
    if sarif_out:
        config.sarif_enabled = True
        config.sarif_path = sarif_out
    
    # Load Baseline Manager
    baseline_manager = BaselineManager(baseline_path)
    if not generate_baseline:
        baseline_manager.load()

    engine_manager = baseline_manager if (not show_baseline and not generate_baseline) else None
    engine = Engine(config=config, baseline_manager=engine_manager)
    
    if not json_output and not generate_baseline:
        paths_str = ", ".join(paths)
        console.print(f"[bold blue]Bina[/bold blue] scanning: {paths_str}...")

    all_findings = []
    for path in paths:
        all_findings.extend(engine.scan_path(path))
    
    findings = all_findings
    
    # SARIF Export
    if config.sarif_enabled:
        from .integrations.sarif_reporter import SarifReporter
        sarif_reporter = SarifReporter(config.sarif_path)
        sarif_reporter.save_report(findings)
        console.print(f"[bold green]SARIF report saved to {config.sarif_path}[/bold green]")

    if generate_baseline:
        baseline_manager.save(findings)
        if not json_output:
            console.print(f"[bold green]Baseline generated at {baseline_path} with {len(findings)} issues.[/bold green]")
        return

    if json_output:
        import json
        from dataclasses import asdict
        
        output = [asdict(f) for f in findings]
        click.echo(json.dumps(output, indent=2))
    else:
        if not findings:
            console.print("[bold green]No issues discovered![/bold green]")
            return

        table = Table(title="Analysis Findings")
        table.add_column("File", style="cyan")
        table.add_column("Rule", style="magenta")
        table.add_column("Severity", style="red")
        table.add_column("Message", style="white")
        table.add_column("Suggestion", style="green")

        for f in findings:
            table.add_row(
                f"{f.file}:{f.line}",
                f.rule_id,
                f.severity.value,
                f.message,
                f.suggestion or ""
            )
        
        console.print(table)
        
        # Exit with error code if issues found
        exit(1)

@main.command()
@click.argument("report_path")
@click.option("--baseline", "baseline_path", default="bina-report-baseline.json")
def ci_report(report_path, baseline_path):
    """Post CI report to GitHub PR."""
    import os
    import json
    from .integrations.github_reporter import GitHubReporter
    from .core.models import Finding, Severity # finding dict to object?
    from .core.baseline import BaselineManager

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
     # GITHUB_REF usually "refs/pull/ID/merge"
    ref = os.environ.get("GITHUB_REF")
    
    # Try to find PR number
    pr_number = None
    if ref and "pull" in ref:
        try:
            pr_number = int(ref.split("/")[2])
        except (ValueError, IndexError, AttributeError):
             pass
    
    # Allow explicit PR number override
    if os.environ.get("GITHUB_PR_NUMBER"):
        try:
             pr_number = int(os.environ.get("GITHUB_PR_NUMBER"))
        except ValueError:
             pass

    if not all([token, repo, pr_number]):
        console.print("[yellow]Skipping GitHub Report: Missing GITHUB_TOKEN, GITHUB_REPOSITORY, or PR_NUMBER context.[/yellow]")
        return

    # Load NEW findings
    try:
        with open(report_path, 'r') as f:
            data = json.load(f)
            # Convert back to Finding objects (simplified)
            # data is list of dicts. Finding is dataclass.
            # We need to map keys properly if dataclass fields match.
            # Warning: Severity enum might need conversion
            findings = []
            for item in data:
                # Severity conversion
                if 'severity' in item:
                    try: 
                        item['severity'] = Severity(item['severity']) 
                    except: 
                        item['severity'] = Severity.LOW # fallback
                
                # Filter out extra keys that match nothing in Finding?
                # Dataclass ctor will fail on extra keys? Yes.
                # So we manually construct
                finding = Finding(
                    rule_id=item['rule_id'],
                    message=item['message'],
                    severity=item['severity'],
                    file=item['file'],
                    line=item['line'],
                    column=item['column'],
                    suggestion=item.get('suggestion'),
                    code_snippet=item.get('code_snippet')
                )
                findings.append(finding)
    except Exception as e:
        console.print(f"[bold red]Error loading report:[/bold red] {e}")
        return

    # Load Baseline to count hidden issues
    bm = BaselineManager(baseline_path)
    bm.load()
    baseline_count = len(bm.baseline_fingerprints)
    
    # Create fake list for reporter length check (Reporter expects List[Finding] for baseline, but only uses len)
    # We pass a list of Nones or simple objects with length match
    baseline_findings_proxy = [None] * baseline_count

    reporter = GitHubReporter(token, repo, pr_number)
    reporter.post_summary(findings, baseline_findings_proxy)

@main.command()
@click.argument("report_path")
def view_report(report_path):
    """View a saved JSON report as a table."""
    import json
    try:
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        if not data:
            console.print("[bold green]No issues found in report.[/bold green]")
            return

        table = Table(title=f"Analysis Findings from {report_path}")
        table.add_column("File", style="cyan")
        table.add_column("Rule", style="magenta")
        table.add_column("Severity", style="red")
        table.add_column("Message", style="white")
        table.add_column("Suggestion", style="green")

        for f in data:
            table.add_row(
                f"{f['file']}:{f['line']}",
                f['rule_id'],
                f['severity'],
                f['message'],
                f.get('suggestion', "")
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error loading report:[/bold red] {e}")
        exit(1)

if __name__ == "__main__":
    main()
