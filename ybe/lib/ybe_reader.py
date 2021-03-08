__author__ = 'Robbert Harms'
__date__ = '2020-04-16'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import os
from typing import List

import dacite
from ruamel.yaml import YAML

from ybe.lib.data_types import TextHTML, TextMarkdown, DirectoryContext, TextData, TextPlain
from ybe.lib.errors import YbeLoadingError
from ybe.lib.ybe_nodes import YbeExam, MultipleChoice, OpenQuestion, MultipleResponse, TextOnly, AnswerOption, Question, \
    AnalyticsQuestionUsage, QuestionUsedInExam


def read_ybe_file(fname):
    """Load the data from the provided .ybe file and return an :class:`ybe.lib.ybe_contents.YbeExam` object.

    Args:
        fname (str): the filename of the .ybe file to load

    Returns:
        ybe.lib.ybe_contents.YbeExam: the contents of the .ybe file.

    Raises:
        ybe.lib.errors.YbeLoadingError: if the file could not be loaded due to syntax errors
    """
    with open(fname, 'r', encoding='utf-8') as f:
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
    yaml = YAML(typ='safe')
    yaml.register_class(TextHTML)
    yaml.register_class(TextMarkdown)
    data = yaml.load(ybe_str)

    if not len(data):
        return YbeExam()

    if 'ybe_version' not in data:
        raise YbeLoadingError('Missing "ybe_version" specifier.')

    def _convert_text(input_data):
        if isinstance(input_data, TextData):
            return input_data
        return TextPlain(input_data)

    def _convert_answer_options(input_data):
        result = []
        for item in input_data:
            if 'answer' in item:
                result.append(dacite.from_dict(
                    AnswerOption, item['answer'], config=dacite.Config(type_hooks={TextData: _convert_text})))
        return result

    def _convert_analytics(input_data):
        analytic_types = {
            'exam': QuestionUsedInExam,
        }
        result = []
        for usage in input_data:
            usage_type, usage_value = list(usage.items())[0]
            result.append(dacite.from_dict(
                analytic_types[usage_type], usage_value,
                config=dacite.Config(type_hooks={TextData: _convert_text})))
        return result

    def _convert_questions(input_data):
        question_types = {
            'multiple_choice': MultipleChoice,
            'multiple_response': MultipleResponse,
            'open': OpenQuestion,
            'text_only': TextOnly
        }
        result = []
        for question in input_data:
            q_type, q_value = list(question.items())[0]
            result.append(dacite.from_dict(
                question_types[q_type], q_value,
                config=dacite.Config(type_hooks={
                    TextData: _convert_text,
                    List[AnswerOption]: _convert_answer_options,
                    List[AnalyticsQuestionUsage]: _convert_analytics
                })))
        return result

    return dacite.from_dict(
        YbeExam, data,
        config=dacite.Config(type_hooks={
            List[Question]: _convert_questions,
            TextData: _convert_text
        }))
