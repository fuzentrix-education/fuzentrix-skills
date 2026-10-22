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
    draft = _draft()
    status = str(draft.get("status", "draft"))
    label = "DRAFT policy (skill default)" if status == "draft" else f"the skill's copy of the LMS rules, {status}"
    return dict(draft, _source=label)


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
    rules.setdefault("values", {})
    rules.setdefault("protocols", ["http", "https"])
    return rules


def style_props(rules: dict, tag: str) -> list:
    """The style properties the LMS keeps on this tag ('*' = any). 'style' is a list for every tag, or per tag."""
    style = rules.get("style") or []
    if isinstance(style, dict):
        return list(style.get(tag) or []) + list(style.get("*") or [])
    return list(style)


def attr_allowed(rules: dict, tag: str, attr: str) -> bool:
    a = rules.get("attributes") or {}
    return attr in (a.get(tag) or []) or attr in (a.get("*") or [])


def protocols(rules: dict, attr: str) -> list:
    p = rules.get("protocols") or []
    return list(p.get(attr) or []) if isinstance(p, dict) else list(p)


def allows(policy: dict, name: str, tag: str) -> bool:
    return tag in context(policy, name)["tags"]


def placeholder(policy: dict, image_id: str, file: str = "") -> str:
    """What an image's src holds until the image is uploaded to the LMS."""
    images = policy.get("images") or {}
    template = images.get("src") or images.get("placeholder") or "{{FZ_IMAGE:{id}}}"
    return template.replace("{id}", image_id).replace("{file}", file or f"{image_id}.png")


def code_form(policy: dict, rules: dict = None) -> str:
    """'language_class' (<pre><code class="language-…">) or 'bare' (<pre><code>): the policy's form, made bare
    wherever the context doesn't keep a class on <code>."""
    form = (policy.get("code") or {}).get("block", "language_class")
    if rules is not None and not attr_allowed(rules, "code", "class"):
        return "bare"
    return form


def code_block(policy: dict, code_html: str, language: str = "", rules: dict = None) -> str:
    """A code block in the policy's canonical form. code_html is already escaped."""
    c = policy.get("code") or {}
    if code_form(policy, rules) == "bare":
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
        images = policy.get("images") or {}
        self.placeholder = None
        if not images.get("src"):  # an older policy: a placeholder that is not a URL
            ph = images.get("placeholder", "{{FZ_IMAGE:{id}}}")
            self.placeholder = re.compile("^" + re.escape(ph).replace(re.escape("{id}"), r"[A-Za-z0-9_.\-]+") + "$")

    def _problem(self, text):
        if text not in self.problems:
            self.problems.append(text)

    def handle_starttag(self, tag, attrs):
        r = self.rules
        if tag not in r["tags"]:
            self._problem(f"<{tag}> is not allowed here (the LMS removes it). Allowed: {', '.join(r['tags'])}.")
        values = r["values"]
        for name, value in attrs:
            value = value or ""
            if not attr_allowed(r, tag, name):
                self._problem(f"<{tag} {name}=…> is not allowed here.")
                continue
            if name == "class":
                patterns = list(r["classes"].get(tag, [])) + list(r["classes"].get("*", []))
                for token in value.split():
                    if not any(fnmatch.fnmatch(token, p) for p in patterns):
                        self._problem(f"class '{token}' on <{tag}> is not allowed here.")
            elif name == "style":
                props = style_props(r, tag)
                for decl in filter(None, (d.strip() for d in value.split(";"))):
                    prop, _, val = (x.strip().lower() for x in decl.partition(":"))
                    if "*" not in props and prop not in props:
                        self._problem(f"style property '{prop}' on <{tag}> is not allowed here (allowed: {', '.join(props) or 'none'}).")
                    elif prop in values and val not in values[prop]:
                        self._problem(f"{prop}: {val} on <{tag}> is not allowed (allowed: {', '.join(values[prop])}).")
            elif name in ("href", "src") and not (tag == "img" and self.placeholder):
                scheme = value.split(":", 1)[0].lower() if ":" in value else ""
                allowed_schemes = protocols(r, name)
                if scheme not in allowed_schemes:
                    self._problem(f"{name} '{value}' must start with {' or '.join(p + ':' for p in allowed_schemes)}.")
            elif tag == "img" and name == "src" and not self.placeholder.match(value):
                self._problem(f"image src '{value}' must be an image placeholder like "
                              f"{placeholder(self.policy, 'cs-01')} (the image is attached when uploading).")
            elif name in values:
                tokens = value.split() if name == "rel" else [value]
                bad = [t for t in tokens if t not in values[name]]
                if bad:
                    self._problem(f"{name}=\"{value}\" on <{tag}> is not allowed (allowed: {', '.join(values[name])}).")
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
        if code_form(self.policy, self.rules) == "language_class":
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
        for key in ("style", "protocols"):
            if key in rules and not isinstance(rules[key], (list, dict)):
                problems.append(f"contexts.{name}.{key} must be a list, or a mapping per tag (style) or per attribute (protocols).")
        if "remove" in rules and not isinstance(rules["remove"], list):
            problems.append(f"contexts.{name}.remove must be a list.")
        if "values" in rules and not isinstance(rules["values"], dict):
            problems.append(f"contexts.{name}.values must map an attribute or style property to its allowed values.")
        if "max_bytes" in rules and not isinstance(rules["max_bytes"], int):
            problems.append(f"contexts.{name}.max_bytes must be a whole number.")
    missing = [c for c in CONTEXTS if c not in value["contexts"]]
    if missing:
        problems.append(f"contexts must include {', '.join(missing)}.")
    images = value.get("images") or {}
    if images.get("src"):
        if "{file}" not in images["src"] and "{id}" not in images["src"]:
            problems.append("images.src must contain {file} (or {id}), where each image's name goes.")
    elif "{id}" not in images.get("placeholder", "{{FZ_IMAGE:{id}}}"):
        problems.append("images.placeholder must contain {id}, where each image's id goes.")
    return problems
