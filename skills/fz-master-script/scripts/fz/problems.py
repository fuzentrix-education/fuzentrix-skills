"""The one problem-list format every builder uses to reject input."""
from __future__ import annotations


class Rejected(Exception):
    """Raised when input fails a check. Nothing is written when this is raised."""

    def __init__(self, problems):
        self.problems = [problems] if isinstance(problems, str) else list(problems)
        super().__init__("\n".join(self.problems))


class MissingPart(Rejected):
    """A step that belongs to another Fuzentrix skill: this skill doesn't ship its module."""


def part(name: str):
    """The module `name`, loaded when a step uses it. Each skill ships only the modules its own steps need, so a step
    from another skill says which module it lacks instead of crashing."""
    import importlib

    full = f"{__package__}.{name}"
    try:
        return importlib.import_module(full)
    except ModuleNotFoundError as e:
        if e.name != full:
            raise
        raise MissingPart(f"This step belongs to another Fuzentrix skill: this one doesn't include fz/{name}.py.") from None


class Lazy:
    """A stand-in for a module, loaded by part() on first use: `quiz = Lazy("quiz")`, then `quiz.build(...)`."""

    def __init__(self, name: str):
        self._name = name

    def __getattr__(self, attr):
        return getattr(part(self._name), attr)


def format_problems(problems) -> str:
    lines = [f"REJECTED: {len(problems)} problem(s). Nothing was written. Fix them and run the same command again."]
    lines += [f"{i}. {p}" for i, p in enumerate(problems, 1)]
    return "\n".join(lines)
