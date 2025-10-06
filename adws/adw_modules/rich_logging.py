"""Rich console logging utilities for ADW workflows.

Provides beautiful, structured logging for better readability in terminal and GitHub Actions.
"""

from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
import json

# Global console instance
console = Console()


class ADWLogger:
    """Rich logging utilities for ADW workflows."""

    # Agent color schemes
    AGENT_COLORS = {
        "PLANNER": "blue",
        "BUILDER": "green",
        "REVIEWER": "yellow",
        "TESTER": "cyan",
        "CLASSIFIER": "magenta",
        "DOCUMENTER": "purple",
        "DEFAULT": "white",
    }

    # Tool emojis
    TOOL_EMOJIS = {
        "Write": "📝",
        "Read": "📖",
        "Edit": "✏️",
        "Bash": "💻",
        "Glob": "🔍",
        "Grep": "🔎",
        "TodoWrite": "📋",
        "WebFetch": "🌐",
        "Task": "🤖",
    }

    # Status emojis
    STATUS_EMOJIS = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "start": "🚀",
        "complete": "🎉",
        "thinking": "🤔",
    }

    @staticmethod
    def workflow_start(workflow_name: str, adw_id: str, issue_number: Optional[int] = None):
        """Log workflow start."""
        content = f"**ADW ID**: {adw_id}"
        if issue_number:
            content += f"\n**Issue**: #{issue_number}"

        console.print(
            Panel(
                content,
                title=f"{ADWLogger.STATUS_EMOJIS['start']} Starting Workflow: [bold cyan]{workflow_name}[/bold cyan]",
                border_style="cyan",
                expand=True,
            )
        )

    @staticmethod
    def workflow_complete(workflow_name: str, adw_id: str, success: bool = True):
        """Log workflow completion."""
        emoji = ADWLogger.STATUS_EMOJIS["complete"] if success else ADWLogger.STATUS_EMOJIS["error"]
        status = "Completed Successfully" if success else "Failed"
        border_color = "green" if success else "red"

        console.print(
            Panel(
                f"**ADW ID**: {adw_id}",
                title=f"{emoji} Workflow {status}: [bold]{workflow_name}[/bold]",
                border_style=border_color,
                expand=True,
            )
        )

    @staticmethod
    def slash_command_start(command: str, args: List[str], adw_id: str, model: str = "sonnet"):
        """Log slash command execution start."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Command", command)
        table.add_row("ADW ID", adw_id)
        table.add_row("Model", model)
        if args:
            table.add_row("Args", ", ".join(args))

        console.print(
            Panel(
                table,
                title=f"{ADWLogger.STATUS_EMOJIS['start']} Executing Slash Command",
                border_style="cyan",
                expand=True,
            )
        )

    @staticmethod
    def slash_command_complete(command: str, success: bool, duration_seconds: Optional[float] = None):
        """Log slash command completion."""
        emoji = ADWLogger.STATUS_EMOJIS["success"] if success else ADWLogger.STATUS_EMOJIS["error"]
        status = "Success" if success else "Failed"
        border_color = "green" if success else "red"

        content = f"**Command**: {command}\n**Status**: {status}"
        if duration_seconds:
            content += f"\n**Duration**: {duration_seconds:.2f}s"

        console.print(
            Panel(
                content,
                title=f"{emoji} Command Completed",
                border_style=border_color,
                expand=True,
            )
        )

    @staticmethod
    def agent_response(agent_name: str, message: str):
        """Log agent response message."""
        agent_upper = agent_name.upper()
        color = ADWLogger.AGENT_COLORS.get(agent_upper, ADWLogger.AGENT_COLORS["DEFAULT"])

        console.print(
            Panel(
                message,
                title=f"[bold {color}]{agent_name} Response[/bold {color}]",
                border_style=color,
                expand=True,
            )
        )

    @staticmethod
    def tool_call(tool_name: str, file_path: Optional[str] = None, details: Optional[str] = None):
        """Log tool call."""
        emoji = ADWLogger.TOOL_EMOJIS.get(tool_name, "🔧")

        if file_path:
            message = f"{emoji} **{tool_name}**: `{file_path}`"
        elif details:
            message = f"{emoji} **{tool_name}**: {details}"
        else:
            message = f"{emoji} **{tool_name}**"

        console.print(message)

    @staticmethod
    def state_update(adw_id: str, field: str, value: Any):
        """Log state update."""
        console.print(
            f"{ADWLogger.STATUS_EMOJIS['info']} State Update [{adw_id}]: "
            f"[cyan]{field}[/cyan] = [yellow]{value}[/yellow]"
        )

    @staticmethod
    def git_operation(operation: str, details: str):
        """Log git operation."""
        console.print(
            f"🔀 **Git {operation}**: {details}"
        )

    @staticmethod
    def port_allocation(adw_id: str, backend_port: int, frontend_port: int):
        """Log port allocation."""
        table = Table(show_header=True, box=None)
        table.add_column("Service", style="cyan")
        table.add_column("Port", style="green")

        table.add_row("Backend", str(backend_port))
        table.add_row("Frontend", str(frontend_port))

        console.print(
            Panel(
                table,
                title=f"🔌 Port Allocation: {adw_id}",
                border_style="dim",
            )
        )

    @staticmethod
    def worktree_created(adw_id: str, path: str, branch: str):
        """Log git worktree creation."""
        console.print(
            Panel(
                f"**Path**: `{path}`\n**Branch**: `{branch}`",
                title=f"🌳 Git Worktree Created: {adw_id}",
                border_style="green",
            )
        )

    @staticmethod
    def model_selection(command: str, model_set: str, model: str):
        """Log model selection."""
        console.print(
            f"🎯 Model Selection: [cyan]{command}[/cyan] → "
            f"[yellow]{model_set}[/yellow] set → [green]{model}[/green]"
        )

    @staticmethod
    def error(message: str, exception: Optional[Exception] = None):
        """Log error."""
        content = f"**Error**: {message}"
        if exception:
            content += f"\n**Exception**: {str(exception)}"

        console.print(
            Panel(
                content,
                title=f"{ADWLogger.STATUS_EMOJIS['error']} Error",
                border_style="red",
                expand=True,
            )
        )

    @staticmethod
    def warning(message: str):
        """Log warning."""
        console.print(
            f"{ADWLogger.STATUS_EMOJIS['warning']} [yellow]Warning: {message}[/yellow]"
        )

    @staticmethod
    def info(message: str):
        """Log info."""
        console.print(
            f"{ADWLogger.STATUS_EMOJIS['info']} [dim]{message}[/dim]"
        )

    @staticmethod
    def config_table(title: str, config: Dict[str, Any]):
        """Display configuration as a table."""
        table = Table(show_header=True, title=title)
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        for key, value in config.items():
            # Format value based on type
            if isinstance(value, (list, dict)):
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)

            table.add_row(key, value_str)

        console.print(table)

    @staticmethod
    def code_block(code: str, language: str = "python", title: Optional[str] = None):
        """Display code block with syntax highlighting."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)

        if title:
            console.print(
                Panel(
                    syntax,
                    title=title,
                    border_style="dim",
                    expand=True,
                )
            )
        else:
            console.print(syntax)

    @staticmethod
    def thinking(message: str, max_length: int = 100):
        """Log agent thinking."""
        display_text = message[:max_length] + "..." if len(message) > max_length else message
        console.print(
            f"{ADWLogger.STATUS_EMOJIS['thinking']} [italic magenta]{display_text}[/italic magenta]"
        )

    @staticmethod
    def kpi_summary(kpis: Dict[str, Any]):
        """Display KPI summary table."""
        table = Table(title="📊 Agentic KPIs", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        for metric, value in kpis.items():
            table.add_row(metric.replace("_", " ").title(), str(value))

        console.print(table)

    @staticmethod
    def separator(text: Optional[str] = None):
        """Print a separator line."""
        if text:
            console.print(f"\n[bold]{'─' * 20} {text} {'─' * 20}[/bold]\n")
        else:
            console.print(f"\n[dim]{'─' * 60}[/dim]\n")

    @staticmethod
    def progress_context(description: str):
        """Create a progress spinner context manager."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        )


# Convenience functions for common patterns

def log_workflow_start(workflow_name: str, adw_id: str, issue_number: Optional[int] = None):
    """Convenience function for workflow start."""
    ADWLogger.workflow_start(workflow_name, adw_id, issue_number)


def log_workflow_complete(workflow_name: str, adw_id: str, success: bool = True):
    """Convenience function for workflow completion."""
    ADWLogger.workflow_complete(workflow_name, adw_id, success)


def log_command(command: str, args: List[str], adw_id: str, model: str = "sonnet"):
    """Convenience function for command logging."""
    ADWLogger.slash_command_start(command, args, adw_id, model)


def log_error(message: str, exception: Optional[Exception] = None):
    """Convenience function for error logging."""
    ADWLogger.error(message, exception)


def log_info(message: str):
    """Convenience function for info logging."""
    ADWLogger.info(message)
