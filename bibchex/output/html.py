import datetime

from jinja2 import Environment, select_autoescape, PackageLoader

from .common_output import CommonOutput

jinja_env = Environment(
    loader=PackageLoader('bibchex', 'data'),
    autoescape=select_autoescape(['html', 'xml'])
)
html_template = jinja_env.get_template('output.html')


class HTMLOutput(CommonOutput):
    def __init__(self, *args):
        super().__init__(*args)

        self._group()

    def _should_output_entry(self, entry):
        return entry.get_id() in self._grouped_problems or \
            entry.get_id() in self._grouped_diffs

    def _generate_per_entry_structure(self, entry):
        es = {'entry': entry,
              'key': entry.get_id(),
              'title': entry.data.get('title', "NO TITLE?"),
              'differences': [],
              'problems': []}

        for problem in self._grouped_problems.get(entry.get_id(), []):
            es['problems'].append({
                'problem_type': problem.problem_type,
                'source': problem.source,
                'message': problem.message,
                'details': problem.details
            })

        for diff in self._grouped_diffs.get(entry.get_id(), []):
            es['differences'].append({
                'field': diff.field,
                'source': diff.source,
                'suggestion': diff.suggestion,
                'old': entry.data.get(diff.field, "")
            })

        return es

    def write(self, filename):
        entry_data = [self._generate_per_entry_structure(
            entry) for entry in self._entries
                      if self._should_output_entry(entry)]

        data = {
            'total_entries': len(self._entries),
            'entries': entry_data,
            'global_problems': self._global_problems,
            'now': datetime.datetime.now(),
            'input_file': self._input_filename
        }

        content = html_template.render(**data)
        with open(filename, 'w') as outfile:
            outfile.write(content)
