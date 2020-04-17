__author__ = 'Robbert Harms'
__date__ = '2020-04-16'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import yaml

from ybe.__version__ import __version__
from ybe.lib.ybe_contents import OpenQuestion, MultipleChoice, RegularText, LatexText


class folded_str(str):
    """Used to be able to represent a folded string block in the Yaml output (> operator)"""
    pass


class literal_str(str):
    """Used to be able to represent a literal string block in the Yaml output (| operator)"""
    pass


def write_ybe_string(ybe_file):
    """Dump the provided YbeFile as a .ybe formatted string.

    Args:
        ybe_file (ybe.lib.ybe_contents.YbeFile): the ybe file contents to dump

    Returns:
        str: an .ybe (Yaml) formatted string
    """
    header = {'ybe_version': __version__,
              'info': {
                  'title': ybe_file.file_info.title,
                  'description': ybe_file.file_info.description,
                  'authors': ybe_file.file_info.authors,
                  'document_version': ybe_file.file_info.description,
                  'creation_date': ybe_file.file_info.creation_date,
              }}

    return yaml.dump_all([header] + _convert_questions(ybe_file.questions),
                         sort_keys=False, indent=4, Dumper=get_ybe_dumping_formatter())


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
        MultipleChoice: _convert_multiple_choice,
        OpenQuestion: _convert_open_question
    }

    converter = question_types.get(node.__class__, None)
    return converter(node)


def _convert_multiple_choice(node):
    """Convert the given :class:`ybe.lib.ybe_contents.MultipleChoice` into a dictionary.

    Args:
        node (ybe.lib.ybe_contents.MultipleChoice): the question to convert

    Returns:
        dict: the question as a dictionary
    """
    data = {'type': 'multiple_choice',
            'id': node.id}
    data.update(_convert_question_text(node.text))
    data.update({
        'meta_data': _convert_meta_data(node.meta_data)})
    return data


def _convert_open_question(node):
    """Convert the given :class:`ybe.lib.ybe_contents.OpenQuestion` into a dictionary.

    Args:
        node (ybe.lib.ybe_contents.OpenQuestion): the question to convert

    Returns:
        dict: the question as a dictionary
    """
    data = {'type': 'open',
            'id': node.id}
    data.update(_convert_question_text(node.text))
    data.update({
        'meta_data': _convert_meta_data(node.meta_data),
        'options': node.options.__dict__})
    return data


def _convert_question_text(node):
    """Convert the question text.

    Args:
        node (ybe.lib.ybe_contents.QuestionText): the text object to convert to a dict text element

    Returns:
        dict: the converted node
    """
    text_modes = {
        RegularText: lambda el: {'text': literal_str(el)},
        LatexText: lambda el: {'text_latex': literal_str(el)},
    }
    return text_modes[node.__class__](node.text)


def _convert_meta_data(node):
    """Convert the meta data object into a dictionary.

    Args:
        node (ybe.lib.ybe_contents.QuestionMetaData): the text object to convert to a dict text element

    Returns:
        dict: the converted node
    """
    return {'general': node.general.__dict__,
            'lifecycle': node.lifecycle.__dict__,
            'classification': node.classification.__dict__}


def get_ybe_dumping_formatter():
    """Get the Yaml dumping formatter we want to use to dump the Yaml content."""
    class YbeStyleDumper(yaml.dumper.SafeDumper):
        ...

    def folded_str_representer(dumper, data):
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='>')

    def literal_str_representer(dumper, data):
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')

    YbeStyleDumper.add_representer(folded_str, folded_str_representer)
    YbeStyleDumper.add_representer(literal_str, literal_str_representer)

    return YbeStyleDumper
