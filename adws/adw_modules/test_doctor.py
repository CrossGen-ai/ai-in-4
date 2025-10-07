"""
Test Doctor - Automated test failure diagnosis and pattern extraction.
"""

from pathlib import Path
from datetime import datetime
import json
import re
from typing import Dict, List, Optional

TESTING_KB_PATH = Path("app_docs/testing")
PATTERNS_PATH = TESTING_KB_PATH / "failure_patterns"
TRACKER_FILE = TESTING_KB_PATH / "pattern_frequency.json"


def update_pattern_tracker(pattern_matches: List[Dict]) -> None:
    """Update pattern frequency tracker."""
    tracker = load_tracker()

    for match in pattern_matches:
        pattern_id = match["pattern_id"]

        if pattern_id not in tracker:
            tracker[pattern_id] = {
                "count": 0,
                "first_seen": datetime.now().isoformat(),
                "last_seen": None,
                "status": "active"
            }

        tracker[pattern_id]["count"] += 1
        tracker[pattern_id]["last_seen"] = datetime.now().isoformat()

    save_tracker(tracker)
    update_readme_frequency_table(tracker)


def update_knowledge_base(new_patterns: List[Dict], logger) -> None:
    """Document new failure patterns."""
    for pattern_data in new_patterns:
        pattern_file = PATTERNS_PATH / f"{pattern_data['id']}.md"

        if pattern_file.exists():
            logger.info(f"Pattern {pattern_data['id']} already exists, updating...")
            append_occurrence(pattern_file, pattern_data)
        else:
            logger.info(f"Creating new pattern: {pattern_data['id']}")
            create_pattern_file(pattern_file, pattern_data)


def create_pattern_file(file_path: Path, data: Dict) -> None:
    """Create new pattern documentation."""
    content = f"""# {data['name']}

**Pattern ID:** `{data['id']}`
**Frequency:** 1 occurrence ({datetime.now().strftime('%Y-%m-%d')})
**Stack:** {data.get('stack', 'Unknown')}

## Error Signature

```
{data['error_signature']}
```

## Root Cause

{data['root_cause']}

## Common Triggers

{format_list(data.get('triggers', []))}

## Fix Pattern

### Before (Fails)
```python
{data['before_code']}
```

### After (Works)
```python
{data['after_code']}
```

## Prevention

{format_list(data.get('prevention_tips', []))}

## Related

{format_links(data.get('related_docs', []))}

## Occurrences

1. {data['first_occurrence']} ({datetime.now().strftime('%Y-%m-%d')}) - DISCOVERED
"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)


def append_occurrence(file_path: Path, data: Dict) -> None:
    """Add occurrence to existing pattern file."""
    content = file_path.read_text()

    # Update frequency count
    freq_match = re.search(r'\*\*Frequency:\*\* (\d+) occurrence', content)
    if freq_match:
        count = int(freq_match.group(1)) + 1
        content = re.sub(
            r'\*\*Frequency:\*\* \d+ occurrence.*',
            f"**Frequency:** {count} occurrences ({datetime.now().strftime('%Y-%m-%d')})",
            content
        )

    # Add to occurrences list
    occurrences_section = f"\n{len(content.split('## Occurrences')[1].split('\\n')) if '## Occurrences' in content else 1}. {data.get('occurrence', 'Unknown location')} ({datetime.now().strftime('%Y-%m-%d')}) - {data.get('status', 'FIXED')}\n"
    content = content.rstrip() + occurrences_section

    file_path.write_text(content)


def load_tracker() -> Dict:
    """Load pattern frequency tracker."""
    if TRACKER_FILE.exists():
        return json.loads(TRACKER_FILE.read_text())
    return {}


def save_tracker(tracker: Dict) -> None:
    """Save pattern frequency tracker."""
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_FILE.write_text(json.dumps(tracker, indent=2))


def update_readme_frequency_table(tracker: Dict) -> None:
    """Update frequency table in README.md."""
    readme_path = TESTING_KB_PATH / "README.md"
    if not readme_path.exists():
        return

    content = readme_path.read_text()

    # Build new table rows
    rows = []
    for pattern_id, data in sorted(tracker.items(), key=lambda x: x[1]['count'], reverse=True):
        last_seen = datetime.fromisoformat(data['last_seen']).strftime('%Y-%m-%d') if data.get('last_seen') else 'Unknown'
        rows.append(f"| {pattern_id} | {data['count']} | {last_seen} | {data['status'].title()} |")

    # Replace table content
    if '## Pattern Frequency Tracker' in content:
        pattern = r'(## Pattern Frequency Tracker.*?\|.*?\|.*?\|.*?\|.*?\n\|.*?\|.*?\|.*?\|.*?\|\n)((?:\|.*\n)*)'
        new_table_rows = '\n'.join(rows) if rows else '| - | - | - | - |'
        content = re.sub(pattern, f'\\1{new_table_rows}\n', content, flags=re.DOTALL)
        readme_path.write_text(content)


def format_list(items: List[str]) -> str:
    """Format list of items as markdown."""
    if not items:
        return "- (None specified)"
    return '\n'.join(f"- {item}" for item in items)


def format_links(links: List[str]) -> str:
    """Format links as markdown."""
    if not links:
        return "- (None)"
    return '\n'.join(f"- [{link}]({link})" for link in links)


def apply_fix(fix: Dict, working_dir: Optional[str] = None) -> None:
    """Apply fix to correct directory (main repo or worktree)."""
    file_path = fix["file_path"]

    if working_dir:
        # ISO mode - apply to worktree
        full_path = Path(working_dir) / file_path
    else:
        # Standard mode - apply to main repo
        full_path = Path(file_path)

    # This would contain the actual fix application logic
    # For now, just a placeholder
    pass
