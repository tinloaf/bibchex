import re

from bibchex.config import Config, ConfigurationError
from bibchex.data import Suggestion


class UnificationRule:
    def __init__(self, pattern, output):
        self.pattern = re.compile(pattern)
        self.output = output

        self.priority = 100
        self.final = False
        self.kind = Suggestion.KIND_RE
        self.repeat = False

        self.apply_to_re = True

    def _handle_priority(self, prio_str):
        self.priority = int(prio_str)

    def _handle_kind(self, kind_str):
        if kind_str.lower() == 'regex':
            self.kind = Suggestion.KIND_RE
        if kind_str.lower() == 'plain':
            self.kind = Suggestion.KIND_PLAIN

    def _handle_no_final(self):
        self.final = False

    def _handle_final(self):
        self.final = True

    def _handle_repeat(self):
        self.repeat = True

    def _handle_no_repeat(self):
        self.repeat = False

    def _handle_apply_to_re(self):
        self.apply_to_re = True

    def _handle_no_apply_to_re(self):
        self.apply_to_re = False

    def __str__(self):
        return f"UR['{self.pattern.pattern}' -> '{self.output}']"

    @classmethod
    def parse(cls, data):
        if not isinstance(data, list) or len(data) < 2:
            raise ConfigurationError(
                "Unification rules must be lists of at least length two.")

        rule = UnificationRule(data[0], data[1])

        for option in data[2:]:
            tokens = option.split(':')

            handler = getattr(rule, f"_handle_{tokens[0]}")
            if not handler:
                raise ConfigurationError(
                    f"Unknow unification rule option {tokens[0]}")
            handler(*tokens[1:])

        return rule


class Unifier:
    def __init__(self):
        self._cfg = Config()

    def _apply_rule(self, rule, data):
        m = rule.pattern.match(data)
        if m:
            return rule.output.format(**m.groupdict())
        return None

    # TODO cache this somehow?
    def _get_rules_for(self, field, entry):
        raw_rules = self._cfg.get(f"unify_{field}", entry, [])
        rules = [UnificationRule.parse(raw_rule) for raw_rule in raw_rules]
        rules.sort(key=lambda rule: rule.priority)

        return rules

    def unify_entry(self, entry):
        '''Returns change suggestions to unify the fields in the entry.'''
        suggestion = Suggestion('unifier', entry)
        for field in entry.data.keys():
            rules = self._get_rules_for(field, entry)
            modified = False

            current_value = entry.data[field]
            current_kind = Suggestion.KIND_PLAIN

            finalized = False
            for rule in rules:
                repeat_done = False
                while not repeat_done:
                    if (current_kind == Suggestion.KIND_RE
                            and not rule.apply_to_re):
                        break  # out of repeat-loop

                    repeat_done |= not rule.repeat

                    res = self._apply_rule(rule, current_value)
                    if res:
                        modified = True
                        current_value = res
                        current_kind = rule.kind
                        if rule.final:
                            finalized = True
                            break  # out of repeat-loop
                    else:
                        repeat_done = True
                if finalized:
                    break  # out of rule-loop

            if modified:
                suggestion.add_field(field, current_value, kind=current_kind)

        return suggestion

    def unify_suggestion(self, suggestion):
        '''Changes the suggestion from a data source to conform to
           the unified form.'''
        for (field, suggestions) in suggestion.data.items():
            rules = self._get_rules_for(field, suggestion.get_entry())
            modified = []

            for (d, kind) in suggestions:
                current_value = d
                current_kind = kind

                finalized = False
                for rule in rules:
                    repeat_done = False
                    while not repeat_done:
                        if (current_kind == Suggestion.KIND_RE
                                and not rule.apply_to_re):
                            break  # out of repeat-loop

                        repeat_done |= not rule.repeat

                        res = self._apply_rule(rule, current_value)
                        if res:
                            current_value = res
                            current_kind = rule.kind
                            if rule.final:
                                finalized = True
                                break  # out of repeat-loop
                        else:
                            repeat_done = True

                    if finalized:
                        break  # out of rule-loop

                modified.append((current_value, current_kind))

                suggestion.data[field] = modified
