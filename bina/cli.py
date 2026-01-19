import click
from rich.console import Console
from rich.table import Table
from .core.engine import Engine
from .core.registry import RuleRegistry

# Import rules to register them
import bina.python.rules

console = Console()

@click.group()
def main():
    """Bina: Static Analysis Tool."""
    pass

@main.command()
@click.argument("path")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def check(path, json_output):
    """Run static analysis on the given path."""
    engine = Engine()
    
    if not json_output:
        console.print(f"[bold blue]Bina[/bold blue] scanning: {path}...")

    findings = engine.scan_path(path)

    if json_output:
        import json
        from dataclasses import asdict
        
        output = [asdict(f) for f in findings]
        click.echo(json.dumps(output, indent=2))
    else:
        if not findings:
            console.print("[bold green]No issues found![/bold green]")
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

if __name__ == "__main__":
    main()
