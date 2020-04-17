__author__ = 'Robbert Harms'
__date__ = '2020-04-16'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import yaml

from ybe.lib.errors import YbeLoadingError
from ybe.lib.ybe_contents import YbeFile, YbeFileInfo, MultipleChoice, OpenQuestion, QuestionMetaData, \
    GeneralQuestionMetaData, LifecycleQuestionMetaData, ClassificationQuestionMetaData, OpenQuestionOptions, \
    RegularText, LatexText


def load_ybe_string(ybe_str):
    """Load the data from the provided Ybe formatted string and return an :class:`ybe.lib.ybe_contents.YbeFile` object.

    Args:
        ybe_str (str): an .ybe formatted string to load

    Returns:
        ybe.lib.ybe_contents.YbeFile: the contents of the .ybe file.

    Raises:
        ybe.lib.errors.YbeLoadingError: if the file could not be loaded due to syntax errors
    """
    items = list(yaml.safe_load_all(ybe_str))

    if len(items) == 0:
        return YbeFile()

    if 'ybe_version' not in items[0]:
        raise YbeLoadingError('Missing "ybe_version" specifier in the header.')

    file_info = YbeFileInfo(**items[0].get('info', {}))
    return YbeFile(questions=_load_questions(items[1:]), file_info=file_info)


def _load_questions(node):
    """Load a list of questions.

    Args:
        node (List[dict]): list of question information

    Returns:
        List[Question]: list of question objects, parsed from the provided information
    """
    results = []
    for ind, question in enumerate(node):
        try:
            results.append(_load_question(question))
        except YbeLoadingError as ex:
            raise YbeLoadingError('Question number {} could not be loaded.'.format(ind + 1)) from ex
    return results


def _load_question(node):
    """Load the information of a single question.

    This infers the question type from the keyword ``type`` and loads the appropriate class.

    Args:
        node (dict): the question information

    Returns:
        ybe.lib.ybe_contents.Question: the loaded question object, parsed from the provided information

    Raises:
        ybe.lib.errors.YbeLoadingError: if the information could not be loaded due to syntax errors
    """
    question_types = {
        'multiple_choice': _load_multiple_choice,
        'open': _load_open_question
    }

    if 'type' not in node:
        raise YbeLoadingError('The provided question does not include a ``type`` identifier.')

    question_type = node['type']
    question_class = question_types.get(question_type, None)

    if question_class is None:
        raise YbeLoadingError('The requested question type {} was not recognized.'.format(question_type))

    return question_class(node)


def _load_multiple_choice(node):
    """Load the information of a single question.

    Args:
        node (dict): the question information

    Returns:
        ybe.lib.ybe_contents.MultipleChoice: the loaded question object, parsed from the provided information
    """
    text = _load_question_text(node)
    meta_data = _load_question_meta_data(node.get('meta_data', {}))
    return MultipleChoice(id=node.get('id'), text=text, meta_data=meta_data)


def _load_open_question(node):
    """Load the information of a single question.

    Args:
        node (dict): the question information

    Returns:
        ybe.lib.ybe_contents.OpenQuestion: the loaded question object, parsed from the provided information
    """
    text = _load_question_text(node)
    meta_data = _load_question_meta_data(node.get('meta_data', {}))
    options = OpenQuestionOptions(**node.get('options', {}))
    return OpenQuestion(id=node.get('id'), text=text, options=options, meta_data=meta_data)


def _load_question_text(node):
    """Load the text of a question.

    Args:
        node (dict): the information of the question to get the right text object for

    Returns:
        ybe.lib.ybe_contents.QuestionText: the correct implementation of the question text
    """
    if 'text_latex' in node:
        return LatexText(node.get('text_latex'))
    return RegularText(node.get('text'))


def _load_question_meta_data(node):
    """Load the meta data of a question.

    Args:
        node (dict): the information of the meta data

    Returns:
        ybe.lib.ybe_contents.QuestionMetaData: the meta data as an object.
    """
    return QuestionMetaData(
        general=GeneralQuestionMetaData(**node.get('general', {})),
        lifecycle=LifecycleQuestionMetaData(**node.get('lifecycle', {})),
        classification=ClassificationQuestionMetaData(**node.get('classification', {}))
    )
