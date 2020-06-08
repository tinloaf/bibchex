class CommonOutput(object):
    def __init__(self, entries, differences, problems, global_problems,
                 input_filename):
        self._entries = entries
        self._diffs = differences
        self._problems = problems
        self._global_problems = global_problems
        self._input_filename = input_filename
        self._grouped_diffs = {}
        self._grouped_problems = {}

    def _group(self):
        self._grouped_diffs = {}

        for diff in self._diffs:
            if diff.entry_id not in self._grouped_diffs:
                self._grouped_diffs[diff.entry_id] = [diff]
            else:
                self._grouped_diffs[diff.entry_id].append(diff)

        self._grouped_problems = {}

        for prob in self._problems:
            if prob.entry_id not in self._grouped_problems:
                self._grouped_problems[prob.entry_id] = [prob]
            else:
                self._grouped_problems[prob.entry_id].append(prob)
