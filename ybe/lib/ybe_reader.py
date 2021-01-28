__author__ = 'Robbert Harms'
__date__ = '2020-04-16'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import os
from dataclasses import fields, is_dataclass, dataclass
from typing import get_type_hints, get_args, get_origin, Any, List

from ruamel import yaml

from ybe.lib.errors import YbeLoadingError
from ybe.lib.ybe_nodes import YbeExam, MultipleChoice, OpenQuestion, Text, MultipleChoiceAnswer, TextMarkdown, \
    TextHTML, MultipleResponse, DirectoryContext, TextOnlyQuestion, TextNode


def read_ybe_file(fname):
    """Load the data from the provided .ybe file and return an :class:`ybe.lib.ybe_contents.YbeExam` object.

    Args:
        fname (str): the filename of the .ybe file to load

    Returns:
        ybe.lib.ybe_contents.YbeExam: the contents of the .ybe file.

    Raises:
        ybe.lib.errors.YbeLoadingError: if the file could not be loaded due to syntax errors
    """
    with open(fname, "r") as f:
        ybe_exam = read_ybe_string(f.read())
        ybe_exam.resource_context = DirectoryContext(os.path.dirname(os.path.abspath(fname)))
        return ybe_exam


def read_ybe_string(ybe_str):
    """Load the data from the provided Ybe formatted string and return an :class:`ybe.lib.ybe_contents.YbeExam` object.

    Args:
        ybe_str (str): an .ybe formatted string to load

    Returns:
        ybe.lib.ybe_contents.YbeExam: the contents of the .ybe file.

    Raises:
        ybe.lib.errors.YbeLoadingError: if the file could not be loaded due to syntax errors
    """
    data = yaml.safe_load(ybe_str)

    if not len(data):
        return YbeExam()

    if 'ybe_version' not in data:
        raise YbeLoadingError('Missing "ybe_version" specifier.')

    return YbeLoader().load(YbeExam, data)


class YbeLoader:

    def __init__(self):
        """Load the datastructure from an Ybe file.

        This interprets the node to see which fields it requires, and then loads those fields from the provided data.
        """
        self._field_subtypes = {
            TextNode: {
                'text': Text,
                'text_markdown': TextMarkdown,
                'text_html': TextHTML
            }
        }

    def load(self, node, data):
        """Visit a node and try to load the provided data.

        Args:
            node (Type[YbeNode]): the YbeNode to load
            data (Any): the data to load as that node

        Returns:
            YbeNode: the YbeNode loaded with the provided data.
        """
        method = f'_load_node_{node.__name__}'
        if hasattr(self, method):
            return getattr(self, method)(node, data)

        inputs = {}
        for field in fields(node):
            if not field.init:
                continue
            parse_result = self._load_field(node, field, data)
            if isinstance(parse_result, ResultValue):
                inputs[field.name] = parse_result.value
        return node(**inputs)

    def _load_field(self, parent_node, field, data):
        method = f'_load_field_{parent_node.__name__}_{field.name}'
        if hasattr(self, method):
            return getattr(self, method)(parent_node, field, data)

        field_name = field.name
        field_type = get_type_hints(parent_node)[field_name]

        if is_dataclass(field_type):
            if field_type in self._field_subtypes:
                subtypes = self._field_subtypes[field_type]
                for sub_field_name, subtype in subtypes.items():
                    if sub_field_name in data:
                        return ResultValue(self.load(subtype, data[sub_field_name]))

            if field_name not in data:
                return ResultMissing()

            return ResultValue(self.load(field_type, data[field_name]))

        if not isinstance(data, (list, dict)):
            return ResultValue(data)

        if field_name not in data:
            return ResultMissing()

        value = data[field_name]

        if get_origin(field_type) == list and isinstance(value, list):
            list_root_node = get_args(field_type)[0]
            if is_dataclass(list_root_node):
                return ResultValue([self.load(list_root_node, el) for el in value])
        return ResultValue(value)

    def _load_node_AnalyticsQuestionMetaData(self, node, data):
        return node(data)

    def _load_field_YbeExam_questions(self, parent_node, field, data):
        if 'questions' in data:
            question_types = {
                'multiple_choice': MultipleChoice,
                'multiple_response': MultipleResponse,
                'open': OpenQuestion,
                'text_only': TextOnlyQuestion
            }
            result = []
            for question in data['questions']:
                q_type, q_value = list(question.items())[0]
                result.append(self.load(question_types[q_type], q_value))
            return ResultValue(result)
        return ResultMissing()

    def _load_field_MultipleChoice_answers(self, parent_node, field, data):
        if 'answers' in data:
            return ResultValue([self.load(MultipleChoiceAnswer, el['answer']) for el in data['answers']])
        return ResultMissing()

    def _load_field_MultipleResponse_answers(self, parent_node, field, data):
        if 'answers' in data:
            return ResultValue([self.load(MultipleChoiceAnswer, el['answer']) for el in data['answers']])
        return ResultMissing()


@dataclass
class ParseResult:
    """The parse result of parsing a field or node."""
    value: Any = None
    warnings: List[str] = None


@dataclass
class ResultMissing(ParseResult):
    """Sentinel value for missing values."""
    pass


@dataclass
class ResultValue(ParseResult):
    """Resulting parse value"""
    pass
