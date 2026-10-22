"""Resolve settings: run override → Configuration Pack snapshot → minimal skill default."""
from __future__ import annotations

from .configpack import policy

# setting → (policy file in the Configuration Pack, minimal default)
SETTINGS = {
    "chunk_lines": ("features.yaml", 150),
    "line_length_words": ("teleprompter.yaml", 8),
    "words_per_minute": ("teleprompter.yaml", 140),
    "teleprompter_symbols": ("teleprompter.yaml", {"➔": "...", "→": "...", "✔": "", "✓": "", "•": ""}),
    "cheatsheet_banned_phrases": ("cheatsheet.yaml", []),
    "cheatsheet_require_mistakes": ("cheatsheet.yaml", True),
}
# settings whose policy key differs from the setting name
POLICY_KEYS = {"teleprompter_symbols": "symbols", "cheatsheet_banned_phrases": "banned_phrases",
               "cheatsheet_require_mistakes": "require_mistakes"}


def get(bundle, key: str):
    overrides = bundle.manifest.get("overrides", {})
    if key in overrides:
        return overrides[key]
    policy_file, default = SETTINGS[key]
    value = policy(bundle.root, policy_file).get(POLICY_KEYS.get(key, key), default)
    if isinstance(default, dict) and isinstance(value, dict) and value is not default:
        value = dict(default, **value)  # the pack adds to or changes the default symbol list
    return value
