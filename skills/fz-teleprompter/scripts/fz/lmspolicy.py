"""The LMS HTML Policy: what the LMS keeps when HTML is pasted or imported, per context (quiz question, option
and explanation, coding problem, cheatsheet page). Every builder that writes LMS HTML checks its output here,
so nothing is stripped or rejected on upload. The rules come from the Configuration Pack (policy/lms-html.yaml),
or the skill's draft copy (defaults/lms-html.yaml) until the LMS team's rules are published."""
from __future__ import annotations

import fnmatch
import re
from html.parser import HTMLParser
from pathlib import Path

from . import kits
from .problems import Rejected

DEFAULT = Path(__file__).parent / "defaults" / "lms-html.yaml"
VOID = {"br", "hr", "img"}
CONTEXTS = ("quiz_question", "quiz_option", "quiz_explanation", "coding_problem", "cheatsheet_page")


def load(bundle=None) -> dict:
    """The policy: the bundle's Configuration Pack copy if it has one, else the draft. Marked with its source."""
    if bundle is not None:
        path = Path(bundle.root) / "_config_snapshot" / "policy" / "lms-html.yaml"
        if path.exists():
            return completed(kits.load_yaml(path.read_text(encoding="utf-8")), f"Configuration Pack {bundle.manifest.get('config', {}).get('version')}")
    return dict(_draft(), _source="DRAFT policy (skill default)")


def _draft() -> dict:
    return kits.load_yaml(DEFAULT.read_text(encoding="utf-8"))


def completed(policy: dict, source: str) -> dict:
    """A published policy, with the draft's code-block and image settings where it leaves them out."""
    draft = _draft()
    return dict(policy, code=policy.get("code") or draft["code"], images=policy.get("images") or draft["images"], _source=source)


def from_file(path) -> dict:
    return completed(kits.load_yaml(Path(path).read_text(encoding="utf-8")), str(path))


def context(policy: dict, name: str) -> dict:
    """One context's rules, with 'extends' and 'remove' applied."""
    contexts = policy.get("contexts") or {}
    if name not in contexts:
        raise Rejected(f"The LMS HTML Policy has no context '{name}' ({', '.join(contexts)}).")
    rules = dict(contexts[name])
    if rules.get("extends"):
        base = context(policy, rules["extends"])
        removed = set(rules.get("remove") or [])
        rules = dict(base, **{k: v for k, v in rules.items() if k not in ("extends", "remove")})
        rules["tags"] = [t for t in base["tags"] if t not in removed]
    rules.setdefault("attributes", {})
    rules.setdefault("classes", {})
    rules.setdefault("style", [])
    rules.setdefault("protocols", ["http", "https"])
    return rules


def allows(policy: dict, name: str, tag: str) -> bool:
    return tag in context(policy, name)["tags"]


def placeholder(policy: dict, image_id: str) -> str:
    return (policy.get("images") or {}).get("placeholder", "{{FZ_IMAGE:{id}}}").replace("{id}", image_id)


def code_block(policy: dict, code_html: str, language: str = "") -> str:
    """A code block in the policy's canonical form. code_html is already escaped."""
    c = policy.get("code") or {}
    if c.get("block", "language_class") == "bare":
        return f"<pre><code>{code_html}</code></pre>"
    lang = (language or "").lower()
    if lang not in (c.get("languages") or []):
        lang = c.get("default_language", "plaintext")
    return f'<pre><code class="language-{lang}">{code_html}</code></pre>'


class _Checker(HTMLParser):
    def __init__(self, policy: dict, rules: dict):
        super().__init__(convert_charrefs=True)
        self.policy, self.rules = policy, rules
        self.problems, self.stack, self.text = [], [], []
        self.pre_children = []  # per open <pre>: [tags directly inside, has stray text]
        ph = (policy.get("images") or {}).get("placeholder", "{{FZ_IMAGE:{id}}}")
        self.placeholder = re.compile("^" + re.escape(ph).replace(re.escape("{id}"), r"[A-Za-z0-9_.\-]+") + "$")

    def _problem(self, text):
        if text not in self.problems:
            self.problems.append(text)

    def handle_starttag(self, tag, attrs):
        r = self.rules
        if tag not in r["tags"]:
            self._problem(f"<{tag}> is not allowed here (the LMS removes it). Allowed: {', '.join(r['tags'])}.")
        allowed = set(r["attributes"].get(tag, [])) | set(r["attributes"].get("*", []))
        for name, value in attrs:
            value = value or ""
            if name not in allowed:
                self._problem(f"<{tag} {name}=…> is not allowed here.")
                continue
            if name == "class":
                patterns = list(r["classes"].get(tag, [])) + list(r["classes"].get("*", []))
                for token in value.split():
                    if not any(fnmatch.fnmatch(token, p) for p in patterns):
                        self._problem(f"class '{token}' on <{tag}> is not allowed here.")
            elif name == "style":
                for decl in filter(None, (d.strip() for d in value.split(";"))):
                    prop = decl.split(":", 1)[0].strip().lower()
                    if prop not in r["style"]:
                        self._problem(f"style property '{prop}' is not allowed here (allowed: {', '.join(r['style']) or 'none'}).")
            elif name == "href":
                scheme = value.split(":", 1)[0].lower() if ":" in value else ""
                if scheme not in r["protocols"]:
                    self._problem(f"link '{value}' must start with {' or '.join(p + '://' for p in r['protocols'])}.")
            elif tag == "img" and name == "src":
                if not self.placeholder.match(value):
                    self._problem(f"image src '{value}' must be an image placeholder like "
                                  f"{placeholder(self.policy, 'cs-01')} (the image is attached when uploading).")
        if tag == "img":
            self.text.append("[image]")  # an image is content too
        if tag == "img" and not dict(attrs).get("alt", "").strip():
            self._problem("every <img> needs alt text.")
        if self.pre_children and self.stack and self.stack[-1] == "pre":  # direct children of <pre> only
            self.pre_children[-1][0].append((tag, dict(attrs)))
        if tag == "pre":
            self.pre_children.append([[], False])
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self._problem(f"</{tag}> closes a tag that isn't open (the tags are wrongly nested).")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
            return
        self.stack.pop()
        if tag == "pre":
            children, stray = self.pre_children.pop()
            self._check_pre(children, stray)

    def _check_pre(self, children, stray):
        if [t for t, _ in children] != ["code"] or stray:
            self._problem("a code block must be exactly <pre><code>…</code></pre>.")
            return
        c = self.policy.get("code") or {}
        cls = children[0][1].get("class", "")
        if c.get("block", "language_class") == "language_class":
            m = re.fullmatch(r"language-([a-z0-9+#-]+)", cls or "")
            if not m or m.group(1) not in (c.get("languages") or []):
                self._problem(f"a code block needs class=\"language-…\" with one of: {', '.join(c.get('languages') or [])}.")
        elif cls:
            self._problem("code blocks here are plain <pre><code>, without a class.")

    def handle_data(self, data):
        self.text.append(data)
        if self.pre_children and self.stack and self.stack[-1] == "pre" and data.strip():
            self.pre_children[-1][1] = True

    def handle_comment(self, data):
        self._problem("HTML comments are not allowed (the LMS removes them).")


def check(html: str, policy: dict, name: str) -> list:
    """Every way this HTML breaks the policy's rules for one context."""
    rules = context(policy, name)
    c = _Checker(policy, rules)
    c.feed(html)
    c.close()
    problems = list(c.problems)
    if c.stack:
        problems.append(f"<{c.stack[-1]}> is never closed.")
    size = len(html.encode("utf-8"))
    if rules.get("max_bytes") and size > rules["max_bytes"]:
        problems.append(f"it is {size} bytes; the LMS takes at most {rules['max_bytes']} here. Shorten it or split it.")
    if not "".join(c.text).strip():
        problems.append("it has no visible text.")
    return problems


def check_policy(value) -> list:
    """Problems with an lms-html.yaml (for the Configuration Pack publisher)."""
    if not isinstance(value, dict) or not isinstance(value.get("contexts"), dict):
        return ["must have 'contexts': one set of rules per place HTML goes."]
    problems = []
    for name, rules in value["contexts"].items():
        if not isinstance(rules, dict):
            problems.append(f"contexts.{name} must be a mapping.")
            continue
        if rules.get("extends"):
            if rules["extends"] not in value["contexts"]:
                problems.append(f"contexts.{name} extends '{rules['extends']}', which is not a context.")
        elif not isinstance(rules.get("tags"), list) or not rules["tags"]:
            problems.append(f"contexts.{name} needs 'tags': the tags the LMS keeps.")
        for key in ("style", "protocols", "remove"):
            if key in rules and not isinstance(rules[key], list):
                problems.append(f"contexts.{name}.{key} must be a list.")
        if "max_bytes" in rules and not isinstance(rules["max_bytes"], int):
            problems.append(f"contexts.{name}.max_bytes must be a whole number.")
    missing = [c for c in CONTEXTS if c not in value["contexts"]]
    if missing:
        problems.append(f"contexts must include {', '.join(missing)}.")
    ph = (value.get("images") or {}).get("placeholder", "{{FZ_IMAGE:{id}}}")
    if "{id}" not in ph:
        problems.append("images.placeholder must contain {id}, where each image's id goes.")
    return problems
