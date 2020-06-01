__author__ = 'Robbert Harms'
__date__ = '2020-04-16'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import collections
import os
from copy import copy

from ruamel import yaml

from ybe.lib.errors import YbeLoadingError, YbeMultipleLoadingErrors
from ybe.lib.ybe_contents import YbeExam, YbeInfo, MultipleChoice, OpenQuestion, QuestionMetaData, \
    GeneralQuestionMetaData, OpenQuestionOptions, \
    Text, AnalyticsQuestionMetaData, MultipleChoiceAnswer, TextMarkdown, TextHTML, MultipleResponse, \
    MultipleResponseAnswer, DirectoryContext, TextOnlyQuestion


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
    items = yaml.safe_load(ybe_str)

    if not len(items):
        return YbeExam()

    if 'ybe_version' not in items:
        raise YbeLoadingError('Missing "ybe_version" specifier.')

    return YbeExam(questions=_load_questions(items.get('questions', [])), info=YbeInfo(**items.get('info', {})))


def _load_questions(node):
    """Load a list of questions.

    Args:
        node (List[dict]): list of question information, the key of each dict should be the question type,
            the value should be the content.

    Returns:
        List[Question]: list of question objects, parsed from the provided information
    """
    results = []
    exceptions = []
    for ind, question in enumerate(node):
        try:
            results.append(_load_question(question))
        except YbeLoadingError as ex:
            ex.question_ind = ind
            ex.question_id = list(question.values())[0].get('id')
            exceptions.append(ex)
            continue

    question_ids = [question.id for question in results]
    if len(question_ids) != len(set(question_ids)):
        duplicates = [item for item, count in collections.Counter(question_ids).items() if count > 1]
        exceptions.append(YbeLoadingError(f'There were multiple questions with the same id "{duplicates}"'))

    if len(exceptions):
        str(YbeMultipleLoadingErrors(exceptions))
        raise YbeMultipleLoadingErrors(exceptions)

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
        'multiple_response': _load_multiple_response,
        'open': _load_open_question,
        'text_only': _load_text_only_question
    }

    question_type, question_content = list(node.items())[0]
    question_loader = question_types.get(question_type, None)

    if question_loader is None:
        raise YbeLoadingError('The requested question type {} was not recognized.'.format(question_type))

    return question_loader(question_content)


def _load_question_basics(node, points_must_be_set=True):
    """Load the basic information of an Ybe question.

    Args:
        node (dict): the question information
        points_must_be_set (boolean): if points must be set as a field for this question.

    Returns:
        dict: basic information for a Ybe question.
    """
    exceptions = []

    try:
        text = _load_text_from_node(node)
    except YbeLoadingError as ex:
        exceptions.append(ex)

    try:
        meta_data = _load_question_meta_data(node.get('meta_data', {}))
    except YbeLoadingError as ex:
        exceptions.append(ex)

    try:
        points = _load_points(node.get('points'), must_be_set=points_must_be_set)
    except YbeLoadingError as ex:
        exceptions.append(ex)

    if len(exceptions):
        raise YbeMultipleLoadingErrors(exceptions)

    return {'id': node.get('id'), 'text': text, 'meta_data': meta_data, 'points': points}


def _load_multiple_choice(node):
    """Load the information of a multiple choice question.

    Args:
        node (dict): the question information

    Returns:
        ybe.lib.ybe_contents.MultipleChoice: the loaded question object, parsed from the provided information
    """
    exceptions = []

    try:
        basic_info = _load_question_basics(node)
    except YbeLoadingError as ex:
        exceptions.append(ex)

    try:
        answers = _load_multiple_choice_answers(node.get('answers', []))
    except YbeLoadingError as ex:
        exceptions.append(ex)

    if len(exceptions):
        raise YbeMultipleLoadingErrors(exceptions)

    return MultipleChoice(answers=answers, **basic_info)


def _load_multiple_response(node):
    """Load the information of a multiple response question.

    Args:
        node (dict): the question information

    Returns:
        ybe.lib.ybe_contents.MultipleResponse: the loaded question object, parsed from the provided information
    """
    exceptions = []

    try:
        basic_info = _load_question_basics(node)
    except YbeLoadingError as ex:
        exceptions.append(ex)

    try:
        answers = _load_multiple_response_answers(node.get('answers', []))
    except YbeLoadingError as ex:
        exceptions.append(ex)

    if len(exceptions):
        raise YbeMultipleLoadingErrors(exceptions)

    return MultipleResponse(answers=answers, **basic_info)


def _load_open_question(node):
    """Load the information of an open question.

    Args:
        node (dict): the question information

    Returns:
        ybe.lib.ybe_contents.OpenQuestion: the loaded question object, parsed from the provided information
    """
    exceptions = []

    try:
        basic_info = _load_question_basics(node)
    except YbeLoadingError as ex:
        exceptions.append(ex)

    try:
        options = OpenQuestionOptions(**node.get('options', {}))
    except YbeLoadingError as ex:
        exceptions.append(ex)

    if len(exceptions):
        raise YbeMultipleLoadingErrors(exceptions)

    return OpenQuestion(options=options, **basic_info)


def _load_text_only_question(node):
    """Load the information of text only question.

    Args:
        node (dict): the question information

    Returns:
        ybe.lib.ybe_contents.TextOnlyQuestion: the loaded question object, parsed from the provided information
    """
    exceptions = []

    try:
        basic_info = _load_question_basics(node, points_must_be_set=False)
    except YbeLoadingError as ex:
        exceptions.append(ex)

    if len(exceptions):
        raise YbeMultipleLoadingErrors(exceptions)

    return TextOnlyQuestion(**basic_info)


def _load_multiple_choice_answers(node):
    """Load all the answers of a multiple choice question.

    Args:
        node (List[dict]): the list of answer items

    Returns:
        List[ybe.lib.ybe_contents.MultipleChoiceAnswer]: the multiple choice answers
    """
    exceptions = []

    answers = []
    for ind, item in enumerate(node):
        content = item['answer']
        answers.append(MultipleChoiceAnswer(
            text=_load_text_from_node(content),
            correct=content.get('correct', False)
        ))

    if not (s := sum(answer.correct for answer in answers)) == 1:
        exceptions.append(YbeLoadingError(f'A multiple choice question must have exactly '
                                          f'1 answer marked as correct, {s} marked.'))

    if len(exceptions):
        raise YbeMultipleLoadingErrors(exceptions)

    return answers


def _load_multiple_response_answers(node):
    """Load all the answers of a multiple response question.

    Args:
        node (List[dict]): the list of answer items

    Returns:
        List[ybe.lib.ybe_contents.MultipleResponseAnswer]: the multiple reponse answers
    """
    exceptions = []

    answers = []
    for ind, item in enumerate(node):
        content = item['answer']

        answers.append(MultipleResponseAnswer(
            text=_load_text_from_node(content),
            correct=content.get('correct', False)
        ))

    if not (s := sum(answer.correct for answer in answers)) > 0:
        exceptions.append(YbeLoadingError(f'A multiple response question must have at least '
                                          f'1 answer marked as correct, {s} marked.'))

    if len(exceptions):
        raise YbeMultipleLoadingErrors(exceptions)

    return answers


def _load_points(value, must_be_set=False):
    """Load the points from the provided value.

    Args:
        value (object): the content of a ``points`` node.
        must_be_set: if True, the value must be set, if False, None is allowed

    Returns:
        int or float: the point value

    Raises:
        YbeLoadingError: if the value was not a float or int
    """
    if value is None:
        if must_be_set:
            raise YbeLoadingError(f'No points set, while points is a required field.')
        return None

    try:
        points = float(value)
    except ValueError:
        raise YbeLoadingError(f'Points should be a float, "{value}" given.')

    if points.is_integer():
        return int(points)

    return points


def _load_text_from_node(node):
    """Load the text of a question.

    Args:
        node (dict): the information of the question to get the right text object for

    Returns:
        ybe.lib.ybe_contents.TextNode: the correct implementation of the question text
    """
    text_modes = {
        'text': Text,
        'text_markdown': TextMarkdown,
        'text_html': TextHTML
    }

    found_text_blocks = []
    found_text_modes = []
    for key, cls in text_modes.items():
        if key in node:
            found_text_blocks.append(cls(text=node[key]))
            found_text_modes.append(key)

    if len(found_text_blocks) == 0:
        raise YbeLoadingError('No text block defined in question.')
    elif len(found_text_blocks) > 1:
        raise YbeLoadingError(f'Multiple text blocks found {found_text_modes} in question.')
    return found_text_blocks[0]


def _load_question_meta_data(node):
    """Load the meta data of a question.

    Args:
        node (dict): the information of the meta data

    Returns:
        ybe.lib.ybe_contents.QuestionMetaData: the meta data as an object.
    """
    exceptions = []

    try:
        general = _load_question_meta_data_general(node.get('general', {}))
    except YbeLoadingError as ex:
        exceptions.append(ex)

    try:
        analytics = _load_question_meta_data_analytics(node.get('analytics', []))
    except YbeLoadingError as ex:
        exceptions.append(ex)

    if len(exceptions):
        raise YbeMultipleLoadingErrors(exceptions)

    return QuestionMetaData(general=general, analytics=analytics)


def _load_question_meta_data_general(node):
    """Load the analytics information of a question.

    Args:
        node (dict): the content of the meta data general information node

    Returns:
        ybe.lib.ybe_contents.GeneralQuestionMetaData: the question's general meta data
    """
    data = copy(node)

    if data.get('keywords') is not None and not isinstance(data.get('keywords'), (list, tuple)):
        data['keywords'] = [data['keywords']]

    if data.get('authors') is not None and not isinstance(data.get('authors'), (list, tuple)):
        data['authors'] = [data['authors']]

    if data.get('chapters') is not None and not isinstance(data.get('chapters'), (list, tuple)):
        data['chapters'] = [data['chapters']]

    exceptions = []

    skill_type = data.get('skill_type')
    skill_types = GeneralQuestionMetaData.available_skill_types
    if skill_type is not None and skill_type not in skill_types:
        exceptions.append(YbeLoadingError(f'The value for ``meta_data.general.skill_type`` should be one of '
                                          f'"{skill_types}", while "{skill_type}" was given.'))

    difficulty = node.get('difficulty')
    if (not isinstance(difficulty, int) or difficulty not in range(0, 11)) and difficulty is not None:
        exceptions.append(YbeLoadingError(f'The value for ``meta_data.general.difficulty`` should be an '
                                          f'integer between [1-10], "{difficulty}" was given.'))

    if len(exceptions):
        raise YbeMultipleLoadingErrors(exceptions)

    return GeneralQuestionMetaData(**data)


def _load_question_meta_data_analytics(node):
    """Load the analytics information of a question.

    Args:
        node (list): list of statistics per exam

    Returns:
        ybe.lib.ybe_contents.AnalyticsQuestionMetaData: the question analytics
    """
    return AnalyticsQuestionMetaData(node)
