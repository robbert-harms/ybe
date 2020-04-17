__author__ = 'Robbert Harms'
__date__ = '2020-04-16'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import collections

import yaml

from ybe.lib.errors import YbeLoadingError
from ybe.lib.ybe_contents import YbeFile, YbeFileInfo, MultipleChoice, OpenQuestion, QuestionMetaData, \
    GeneralQuestionMetaData, LifecycleQuestionMetaData, ClassificationQuestionMetaData, OpenQuestionOptions, \
    Text, TextLatex, QuestionAnalytics, MultipleChoiceAnswer


def load_ybe_string(ybe_str):
    """Load the data from the provided Ybe formatted string and return an :class:`ybe.lib.ybe_contents.YbeFile` object.

    Args:
        ybe_str (str): an .ybe formatted string to load

    Returns:
        ybe.lib.ybe_contents.YbeFile: the contents of the .ybe file.

    Raises:
        ybe.lib.errors.YbeLoadingError: if the file could not be loaded due to syntax errors
    """
    items = yaml.safe_load(ybe_str)

    if not len(items):
        return YbeFile()

    if 'ybe_version' not in items:
        raise YbeLoadingError('Missing "ybe_version" specifier.')

    return YbeFile(questions=_load_questions(items.get('questions', [])),
                   file_info=YbeFileInfo(**items.get('info', {})))


def _load_questions(node):
    """Load a list of questions.

    Args:
        node (List[dict]): list of question information, the key of each dict should be the question type,
            the value should be the content.

    Returns:
        List[Question]: list of question objects, parsed from the provided information
    """
    results = []
    for ind, question in enumerate(node):
        try:
            results.append(_load_question(question))
        except YbeLoadingError as ex:
            raise YbeLoadingError(f'Question number {ind + 1} could not be loaded.') from ex

    question_ids = [question.id for question in results]
    if len(question_ids) != len(set(question_ids)):
        duplicates = [item for item, count in collections.Counter(question_ids).items() if count > 1]
        raise YbeLoadingError(f'There were multiple questions with the same ``id``: {duplicates}')

    return results


def _load_question(node):
    """Load the information of a single question.

    This infers the question type from the keyword ``type`` and loads the appropriate class.

    Args:
        node (dict): list of question information, the key should be the question type, the value should be the content.

    Returns:
        ybe.lib.ybe_contents.Question: the loaded question object, parsed from the provided information

    Raises:
        ybe.lib.errors.YbeLoadingError: if the information could not be loaded due to syntax errors
    """
    question_types = {
        'multiple_choice': _load_multiple_choice,
        'open': _load_open_question
    }

    question_type, question_content = list(node.items())[0]
    question_loader = question_types.get(question_type, None)

    if question_loader is None:
        raise YbeLoadingError('The requested question type {} was not recognized.'.format(question_type))

    return question_loader(question_content)


def _load_multiple_choice(node):
    """Load the information of a single question.

    Args:
        node (dict): the question information

    Returns:
        ybe.lib.ybe_contents.MultipleChoice: the loaded question object, parsed from the provided information
    """
    text = _load_text_from_node(node)
    meta_data = _load_question_meta_data(node.get('meta_data', {}))
    analytics = _load_question_analytics(node.get('analytics', []))
    answers = _load_multiple_choice_answers(node.get('answers', []))
    return MultipleChoice(id=node.get('id'), text=text, answers=answers, meta_data=meta_data, analytics=analytics)


def _load_open_question(node):
    """Load the information of a single question.

    Args:
        node (dict): the question information

    Returns:
        ybe.lib.ybe_contents.OpenQuestion: the loaded question object, parsed from the provided information
    """
    text = _load_text_from_node(node)
    meta_data = _load_question_meta_data(node.get('meta_data', {}))
    analytics = _load_question_analytics(node.get('analytics', []))
    options = OpenQuestionOptions(**node.get('options', {}))
    return OpenQuestion(id=node.get('id'), text=text, options=options, meta_data=meta_data, analytics=analytics)


def _load_multiple_choice_answers(node):
    """Load all the answers of a multiple choice question.

    Args:
        node (List[dict]): the list of answer items

    Returns:
        List[ybe.lib.ybe_contents.MultipleChoiceAnswer]: the multiple choice answers
    """
    answers = []
    for item in node:
        content = item['answer']
        answers.append(MultipleChoiceAnswer(
            text=_load_text_from_node(content),
            points=content.get('points'),
            correct=content.get('correct')
        ))

    if not any(el.correct for el in answers):
        raise YbeLoadingError('At least one answer should be marked correct.')

    return answers


def _load_text_from_node(node):
    """Load the text of a question.

    Args:
        node (dict): the information of the question to get the right text object for

    Returns:
        ybe.lib.ybe_contents.TextBlock: the correct implementation of the question text
    """
    if 'text_latex' in node:
        return TextLatex(node.get('text_latex'))
    return Text(node.get('text'))


def _load_question_meta_data(node):
    """Load the meta data of a question.

    Args:
        node (dict): the information of the meta data

    Returns:
        ybe.lib.ybe_contents.QuestionMetaData: the meta data as an object.
    """
    related_concepts = node.get('classification', {}).get('related_concepts')
    if not (isinstance(related_concepts, list) or related_concepts is None):
        raise YbeLoadingError(f'The value for ``meta_data.classification.related_concepts`` should be a list, '
                              f'"{related_concepts}" given.')

    skill_level = node.get('classification', {}).get('skill_level')
    skill_levels = ClassificationQuestionMetaData.available_skill_levels
    if skill_level not in skill_levels:
        raise YbeLoadingError(f'The value for ``meta_data.classification.skill_level`` should be one of '
                              f'"{skill_levels}", while "{skill_level}" was given.')

    chapter = node.get('classification', {}).get('chapter')
    if not isinstance(chapter, int):
        raise YbeLoadingError(f'The value for ``meta_data.classification.chapter`` should be an integer, '
                              f'"{chapter}" was given.')

    difficulty = node.get('classification', {}).get('difficulty')
    if not isinstance(difficulty, int) or difficulty not in range(0, 11):
        raise YbeLoadingError(f'The value for ``meta_data.classification.difficulty`` should be an '
                              f'integer between [1-10], "{difficulty}" was given.')

    keywords = node.get('general', {}).get('keywords')
    if not (isinstance(keywords, list) or keywords is None):
        raise YbeLoadingError(f'The value for ``meta_data.general.keywords`` should be a list, '
                              f'"{keywords}" was given.')

    return QuestionMetaData(
        general=GeneralQuestionMetaData(**node.get('general', {})),
        lifecycle=LifecycleQuestionMetaData(**node.get('lifecycle', {})),
        classification=ClassificationQuestionMetaData(**node.get('classification', {}))
    )


def _load_question_analytics(node):
    """Load the analytics information of a question.

    Args:
        node (list): list of statistics per exam

    Returns:
        ybe.lib.ybe_contents.QuestionAnalytics: the question analytics
    """
    return QuestionAnalytics(node)
