__author__ = 'Robbert Harms'
__date__ = '2020-04-16'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import os
from dataclasses import fields
from io import StringIO
from typing import get_type_hints

from ruamel.yaml import YAML
from ruamel.yaml import scalarstring

from ybe.__version__ import __version__
from ybe.lib.data_types import TextHTML, TextMarkdown, TextNoMarkup, TextData
from ybe.lib.ybe_nodes import YbeNode, Text, Question, MultipleChoice, MultipleResponse, OpenQuestion, TextOnlyQuestion, \
    MultipleResponseAnswer, MultipleChoiceAnswer, AnalyticsQuestionMetaData


def write_ybe_file(ybe_exam, fname, minimal=False):
    """Dump the provided Ybe file object to the indicated file.

    Args:
        ybe_exam (ybe.lib.ybe_contents.YbeExam): the ybe file object to dump
        fname (str): the filename to dump to
        minimal (boolean): if set to True we only print the configured options.
            By default this flag is False, meaning we print all the available options, if needed with null placeholders.
    """
    if not os.path.exists(dir := os.path.dirname(fname)):
        os.makedirs(dir)

    with open(fname, 'w') as f:
        f.write(write_ybe_string(ybe_exam, minimal=minimal))


def write_ybe_string(ybe_exam, minimal=False):
    """Dump the provided YbeExam as a .ybe formatted string.

    Args:
        ybe_exam (ybe.lib.ybe_contents.YbeExam): the ybe file contents to dump
        minimal (boolean): if set to True we only print the configured options.
            By default this flag is False, meaning we print all the available options, if needed with null placeholders.

    Returns:
        str: an .ybe (Yaml) formatted string
    """
    visitor = YbeConversionVisitor(minimal=minimal)
    content = {'ybe_version': __version__}
    content.update(visitor.convert(ybe_exam))

    yaml = YAML(typ='rt')
    yaml.register_class(TextHTML)
    yaml.register_class(TextMarkdown)
    yaml.default_flow_style = False
    yaml.allow_unicode = True
    yaml.width = float('inf')
    yaml.indent(mapping=4, offset=4, sequence=4)

    def beautify_line_spacings(s):
        ret_val = ''
        previous_new_line = ''
        in_questions_block = False
        for line in s.splitlines(True):
            new_line = line

            if in_questions_block:
                if line.startswith('    '):
                    new_line = line[4:]
                elif line.startswith('\n'):
                    pass
                else:
                    in_questions_block = False
            else:
                if line.startswith('questions:'):
                    in_questions_block = True

            if any(new_line.startswith(el) for el in ['info', 'questions:', '- multiple_choice:', '- open:',
                                                      '- multiple_response:', '- text_only:'])\
                    and not previous_new_line.startswith('\nquestions:'):
                new_line = '\n' + new_line

            previous_new_line = new_line
            ret_val += new_line
        return ret_val

    yaml.dump(content, result := StringIO(), transform=beautify_line_spacings)
    return result.getvalue()


class YbeConversionVisitor:

    def __init__(self, minimal=False):
        """Converts an YbeExam into a Python dictionary.

        Args:
            minimal (boolean): if set to True we only print the configured options.
                By default this flag is False, meaning we print all the available options, if needed with null placeholders.
        """
        self.minimal = minimal

    def convert(self, node):
        method = f'_convert_{node.__class__.__name__}'
        if hasattr(self, method):
            return getattr(self, method)(node)
        return self._defaultconvert(node)

    def _defaultconvert(self, node):
        results = {}

        field_types = get_type_hints(type(node))

        for field in fields(node):
            if not field.init:
                continue

            value = getattr(node, field.name)

            if self.minimal and value == node.get_default_value(field.name):
                continue

            if field_types[field.name] == Text:
                result = None
                if value is not None:
                    result = self._convert_value(value.text)
            else:
                result = self._convert_value(value)

            results[field.name] = result
        return results

    def _convert_value(self, value):
        if isinstance(value, Question):
            question_types = {
                MultipleChoice: 'multiple_choice',
                MultipleResponse: 'multiple_response',
                OpenQuestion: 'open',
                TextOnlyQuestion: 'text_only'
            }
            return {question_types[value.__class__]: self.convert(value)}

        if isinstance(value, MultipleResponseAnswer):
            return {'answer': self.convert(value)}

        if isinstance(value, MultipleChoiceAnswer):
            return {'answer': self.convert(value)}

        if isinstance(value, AnalyticsQuestionMetaData):
            return value.analytics

        if isinstance(value, YbeNode):
            return self.convert(value)

        if isinstance(value, TextData):
            if isinstance(value, TextNoMarkup):
                if '\n' in value.text:
                    return scalarstring.PreservedScalarString(value.text)
                return value.text
            return value

        if isinstance(value, list):
            return [self._convert_value(el) for el in value]

        return value
