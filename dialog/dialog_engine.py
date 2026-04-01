import re
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple


class EngineState(str, Enum):
    BOOT = "BOOT"
    IDLE = "IDLE"
    IN_SCOPE = "IN_SCOPE"
    EXEC_ACTIONS = "EXEC_ACTIONS"


@dataclass
class Rule:
    depth: int
    pattern_raw: str
    output_raw: str
    line_no: int
    children: List["Rule"] = field(default_factory=list)


@dataclass
class EngineReply:
    text: str
    actions: List[str]
    matched: bool
    interrupt: bool = False
    state: str = "IDLE"


class DialogEngine:
    INTERRUPTS = {"stop", "cancel", "reset", "quit"}
    MAX_NESTING = 6
    MAX_UNMATCHED_IN_SCOPE = 4

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.state = EngineState.BOOT

        self.definitions: Dict[str, List[str]] = {}
        self.top_rules: List[Rule] = []
        self.variables: Dict[str, str] = {}

        self.scope_stack: List[Rule] = []
        self.unmatched_in_scope = 0

        self.set_state(EngineState.IDLE)

    def set_state(self, new_state: EngineState, scope_depth: Optional[int] = None):
        if new_state == EngineState.IN_SCOPE and scope_depth is not None:
            print(f"[STATE] -> IN_SCOPE({scope_depth})", flush=True)
        else:
            print(f"[STATE] -> {new_state}", flush=True)
        self.state = new_state

    def reset_scope(self):
        self.scope_stack.clear()
        self.unmatched_in_scope = 0
        self.set_state(EngineState.IDLE)

    def load_script(self, path: str):
        self.definitions.clear()
        self.top_rules.clear()
        self.scope_stack.clear()
        self.variables.clear()
        self.unmatched_in_scope = 0

        pending_stack: List[Rule] = []

        with open(path, "r", encoding="utf-8") as f:
            for line_no, raw in enumerate(f, start=1):
                line = self._strip_comments(raw).strip()
                if not line:
                    continue

                if line.startswith("~"):
                    try:
                        name, items = self._parse_definition(line)
                        self.definitions[name] = items
                        print(f"[LOAD] definition ~{name} = {items}", flush=True)
                    except ValueError as e:
                        self._log_parse_error(path, line_no, str(e), fatal=False)
                    continue

                try:
                    rule = self._parse_rule_line(line, line_no)
                except ValueError as e:
                    self._log_parse_error(path, line_no, str(e), fatal=False)
                    continue

                if rule.depth >= self.MAX_NESTING:
                    self._log_parse_error(path, line_no, "nesting deeper than 6", fatal=False)
                    continue

                while pending_stack and pending_stack[-1].depth >= rule.depth:
                    pending_stack.pop()

                if rule.depth == 0:
                    self.top_rules.append(rule)
                else:
                    if not pending_stack:
                        self._log_parse_error(path, line_no, "nested rule without parent", fatal=False)
                        continue
                    pending_stack[-1].children.append(rule)

                pending_stack.append(rule)
                print(
                    f"[LOAD] rule depth={rule.depth} line={line_no} pattern={rule.pattern_raw!r}",
                    flush=True,
                )

        if not self.top_rules:
            raise ValueError("Fatal: no valid top-level u: rules")

        self.set_state(EngineState.IDLE)

    def _strip_comments(self, s: str) -> str:
        return s.split("#", 1)[0]

    def _parse_definition(self, line: str) -> Tuple[str, List[str]]:
        m = re.match(r"^\s*~([A-Za-z_]\w*)\s*:\s*(.+?)\s*$", line)
        if not m:
            raise ValueError("bad definition syntax")
        name = m.group(1)
        items_expr = m.group(2)
        items = self._parse_choice_block(items_expr)
        if not items:
            raise ValueError("definition has no items")
        return name, items

    def _parse_rule_line(self, line: str, line_no: int) -> Rule:
        m = re.match(r"^\s*u(\d*)\s*:\s*(.*?)\s*:\s*(.+?)\s*$", line)
        if not m:
            raise ValueError("bad rule syntax")
        depth_str, pattern, output = m.groups()
        depth = int(depth_str) if depth_str else 0
        return Rule(depth=depth, pattern_raw=pattern, output_raw=output, line_no=line_no)

    def _log_parse_error(self, filename: str, line_no: int, category: str, fatal: bool):
        level = "FATAL" if fatal else "NON-FATAL"
        print(f"[PARSE {level}] {filename}:{line_no} :: {category}", flush=True)

    def process(self, user_text: str) -> EngineReply:
        normalized = self._normalize(user_text)

        if normalized in self.INTERRUPTS:
            print("[INTERRUPT] global stop/reset/quit/cancel", flush=True)
            self.reset_scope()
            return EngineReply(
                text="Stopping now.",
                actions=[],
                matched=True,
                interrupt=True,
                state=self.state.value,
            )

        candidates = self._get_active_rules()

        for rule in candidates:
            captures = {}
            if self._match_pattern(rule.pattern_raw, normalized, captures):
                print(f"[MATCH] line={rule.line_no} pattern={rule.pattern_raw!r}", flush=True)

                self._bind_captures_from_output(rule.output_raw, captures)
                text, actions = self._render_output(rule.output_raw)

                if rule.depth == 0:
                    self.scope_stack = [rule]
                else:
                    self.scope_stack = self.scope_stack[:rule.depth]
                    self.scope_stack.append(rule)

                if len(self.scope_stack) > self.MAX_NESTING:
                    print("[SAFE] max nesting exceeded, resetting", flush=True)
                    self.reset_scope()
                    return EngineReply("Resetting safely.", [], False, state=self.state.value)

                self.unmatched_in_scope = 0

                if rule.children:
                    self.set_state(EngineState.IN_SCOPE, len(self.scope_stack))
                else:
                    self.set_state(EngineState.IDLE)

                return EngineReply(
                    text=text,
                    actions=actions,
                    matched=True,
                    state=self.state.value,
                )

        print("[MATCH] no rule matched", flush=True)
        if self.scope_stack:
            self.unmatched_in_scope += 1
            print(f"[SAFE] unmatched_in_scope={self.unmatched_in_scope}", flush=True)
            if self.unmatched_in_scope >= self.MAX_UNMATCHED_IN_SCOPE:
                print("[SAFE] too many unmatched inputs in scope, resetting", flush=True)
                self.reset_scope()
                return EngineReply(
                    text="Let's start over.",
                    actions=[],
                    matched=False,
                    state=self.state.value,
                )

        return EngineReply(
            text="I don't understand.",
            actions=[],
            matched=False,
            state=self.state.value,
        )

    def _get_active_rules(self) -> List[Rule]:
        if not self.scope_stack:
            return self.top_rules

        current = self.scope_stack[-1]
        if current.children:
            return current.children

        return self.top_rules

    def _normalize(self, text: str) -> str:
        text = text.lower()
        text = text.replace("’", "'")
        text = re.sub(r"[.,!?']", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _match_pattern(self, pattern: str, user_text: str, captures: Dict[str, str]) -> bool:
        expanded = self._expand_definitions_in_pattern(pattern)
        regex = self._pattern_to_regex(expanded)
        m = re.fullmatch(regex, user_text, flags=re.IGNORECASE)
        if not m:
            return False

        if "capture" in m.groupdict():
            captures["wildcard"] = m.group("capture").strip()
        return True

    def _expand_definitions_in_pattern(self, pattern: str) -> str:
        for name, items in self.definitions.items():
            pattern = pattern.replace(
                f"~{name}",
                "[" + " ".join(self._quote_if_needed(x) for x in items) + "]",
            )
        return pattern

    def _quote_if_needed(self, s: str) -> str:
        return f'"{s}"' if " " in s else s

    def _pattern_to_regex(self, pattern: str) -> str:
        pattern = pattern.strip()

        if pattern.startswith("(") and pattern.endswith(")"):
            pattern = pattern[1:-1].strip()

        def repl_choice(m):
            items = self._tokenize_choices(m.group(1))
            alts = [re.escape(self._normalize(x)) for x in items]
            return "(?:" + "|".join(alts) + ")"

        pattern = re.sub(r"\[([^\]]+)\]", repl_choice, pattern)
        pattern = self._normalize(pattern)
        pattern = pattern.replace("_", r"(?P<capture>.+)")
        pattern = re.sub(r"\s+", r"\\s+", pattern)

        return pattern

    def _render_output(self, output_raw: str) -> Tuple[str, List[str]]:
        actions = re.findall(r"<([A-Za-z_]\w*)>", output_raw)
        spoken = re.sub(r"<[A-Za-z_]\w*>", "", output_raw).strip()

        for name, items in self.definitions.items():
            spoken = spoken.replace(f"~{name}", self.rng.choice(items))

        spoken = self._resolve_output_choices(spoken)

        def var_sub(m):
            key = m.group(1)
            return self.variables.get(key, "I don't know")

        spoken = re.sub(r"\$([A-Za-z_]\w*)", var_sub, spoken)
        spoken = re.sub(r"\s+", " ", spoken).strip()
        return spoken, actions

    def _resolve_output_choices(self, text: str) -> str:
        while True:
            m = re.search(r"\[([^\]]+)\]", text)
            if not m:
                break
            items = self._tokenize_choices(m.group(1))
            choice = self.rng.choice(items) if items else ""
            text = text[:m.start()] + choice + text[m.end():]
        return text

    def _bind_captures_from_output(self, output_raw: str, captures: Dict[str, str]):
        if "wildcard" not in captures:
            return

        vars_in_output = re.findall(r"\$([A-Za-z_]\w*)", output_raw)
        if vars_in_output:
            self.variables[vars_in_output[0]] = captures["wildcard"]
            print(f"[VARS] {vars_in_output[0]} = {captures['wildcard']!r}", flush=True)

    def _parse_choice_block(self, expr: str) -> List[str]:
        expr = expr.strip()
        if not (expr.startswith("[") and expr.endswith("]")):
            raise ValueError("choice block must use [ ... ]")
        return self._tokenize_choices(expr[1:-1])

    def _tokenize_choices(self, s: str) -> List[str]:
        out = []
        for m in re.finditer(r'"([^"]+)"|([^\s]+)', s):
            item = m.group(1) if m.group(1) is not None else m.group(2)
            if item:
                out.append(item)
        return out