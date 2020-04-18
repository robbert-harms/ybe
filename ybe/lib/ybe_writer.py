__author__ = 'Robbert Harms'
__date__ = '2020-04-16'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from io import StringIO
from ruamel.yaml import YAML
from ruamel.yaml import scalarstring
from ruamel.yaml.comments import CommentedSeq

from ybe.__version__ import __version__
from ybe.lib.ybe_contents import OpenQuestion, MultipleChoice, Text, TextLatex


def write_ybe_string(ybe_file, minimal=False):
    """Dump the provided YbeFile as a .ybe formatted string.

    Args:
        ybe_file (ybe.lib.ybe_contents.YbeFile): the ybe file contents to dump
        minimal (boolean): if set to True we only print the configured options.
            By default this flag is False, meaning we print all the available options, if needed with null placeholders.

    Returns:
        str: an .ybe (Yaml) formatted string
    """

    a = CommentedSeq(ybe_file.file_info.authors)
    a.fa.set_flow_style()

    content = {
        'ybe_version': __version__,
        'info': {
            'title': ybe_file.file_info.title,
            'description': ybe_file.file_info.description,
            'authors': ybe_file.file_info.authors,
            'document_version': ybe_file.file_info.document_version,
            'creation_date': ybe_file.file_info.creation_date,
        },
        'questions': _convert_questions(ybe_file.questions)
    }

    yaml = YAML(typ='rt')
    yaml.default_flow_style = False
    yaml.allow_unicode = True
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

            if any(new_line.startswith(el) for el in ['info', 'questions:', '- multiple_choice:', '- open:'])\
                    and not previous_new_line.startswith('\nquestions:'):
                new_line = '\n' + new_line

            previous_new_line = new_line
            ret_val += new_line
        return ret_val

    yaml.dump(content, result := StringIO(), transform=beautify_line_spacings)
    return result.getvalue()


def _convert_questions(node):
    """Convert the given list of :class:`ybe.lib.ybe_contents.Question` items to a dictionary.

    Args:
        node (List[ybe.lib.ybe_contents.Question]): the questions to convert

    Returns:
        List[dict]: the questions as a dictionary
    """
    return [_convert_question(el) for el in node]


def _convert_question(node):
    """Convert the given :class:`ybe.lib.ybe_contents.Question` into a dictionary.

    Args:
        node (ybe.lib.ybe_contents.Question): the question to convert

    Returns:
        dict: the question as a dictionary
    """
    question_types = {
        MultipleChoice: ('multiple_choice', _convert_multiple_choice),
        OpenQuestion: ('open', _convert_open_question)
    }

    key, converter = question_types.get(node.__class__, None)
    return {key: converter(node)}


def _convert_multiple_choice(node):
    """Convert the given :class:`ybe.lib.ybe_contents.MultipleChoice` into a dictionary.

    Args:
        node (ybe.lib.ybe_contents.MultipleChoice): the question to convert

    Returns:
        dict: the question as a dictionary
    """
    data = {'id': node.id}
    data.update(_convert_text_from_node(node.text))
    data.update({
        'answers': _convert_multiple_choice_answers(node.answers),
        'meta_data': _convert_meta_data(node.meta_data)})
    return data


def _convert_open_question(node):
    """Convert the given :class:`ybe.lib.ybe_contents.OpenQuestion` into a dictionary.

    Args:
        node (ybe.lib.ybe_contents.OpenQuestion): the question to convert

    Returns:
        dict: the question as a dictionary
    """
    data = {'id': node.id}
    data.update(_convert_text_from_node(node.text))
    data.update({
        'options': node.options.__dict__,
        'meta_data': _convert_meta_data(node.meta_data)})
    return data


def _convert_multiple_choice_answers(node):
    """Convert the multiple choice answers

    Args:
        node (List[ybe.lib.ybe_contents.MultipleChoiceAnswer]): the multiple choice answers to convert to text.

    Returns:
        List[dict]: the converted answers
    """
    dicts = []
    for item in node:
        data = {}
        data.update(_convert_text_from_node(item.text))
        data['points'] = item.points
        if item.correct:
            data['correct'] = item.correct
        dicts.append({'answer': data})
    return dicts


def _convert_text_from_node(node):
    """Convert the question text.

    Args:
        node (ybe.lib.ybe_contents.TextBlock): the text object to convert to a dict text element

    Returns:
        dict: the converted node
    """
    def format_text(text):
        if '\n' in text:
            return scalarstring.PreservedScalarString(text)
        return text

    text_modes = {
        Text: lambda el: {'text': format_text(el)},
        TextLatex: lambda el: {'text_latex': format_text(el)},
    }
    return text_modes[node.__class__](node.text)


def _convert_meta_data(node):
    """Convert the meta data object into a dictionary.

    Args:
        node (ybe.lib.ybe_contents.QuestionMetaData): the text object to convert to a dict text element

    Returns:
        dict: the converted node
    """
    classification = node.classification.__dict__
    classification['related_concepts'] = _inline_list(classification['related_concepts'])

    general = node.general.__dict__
    general['keywords'] = _inline_list(general['keywords'])

    return {'general': general,
            'lifecycle': node.lifecycle.__dict__,
            'classification': classification,
            'analytics': node.analytics.analytics}


def _inline_list(l):
    """Return a list wrapped in a ruamal yaml block, such that the list will be displayed inline.

    Args:
        l (list): the list to wrap

    Returns:
        CommentedSeq: the commented list with the flow style set to True
    """
    wrapped = CommentedSeq(l)
    wrapped.fa.set_flow_style()
    return wrapped
