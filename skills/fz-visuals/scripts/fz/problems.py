"""The one problem-list format every builder uses to reject input."""
from __future__ import annotations


class Rejected(Exception):
    """Raised when input fails a check. Nothing is written when this is raised."""

    def __init__(self, problems):
        self.problems = [problems] if isinstance(problems, str) else list(problems)
        super().__init__("\n".join(self.problems))


def format_problems(problems) -> str:
    lines = [f"REJECTED: {len(problems)} problem(s). Nothing was written. Fix them and run the same command again."]
    lines += [f"{i}. {p}" for i, p in enumerate(problems, 1)]
    return "\n".join(lines)
