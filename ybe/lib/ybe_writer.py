__author__ = 'Robbert Harms'
__date__ = '2020-04-16'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import os
from io import StringIO
from ruamel.yaml import YAML
from ruamel.yaml import scalarstring
from ruamel.yaml.comments import CommentedSeq

from ybe.__version__ import __version__
from ybe.lib.errors import YbeVisitingError
from ybe.lib.ybe_contents import YbeNodeVisitor


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
    content = visitor.visit(ybe_exam)

    yaml = YAML(typ='rt')
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


class YbeConversionVisitor(YbeNodeVisitor):

    def __init__(self, minimal=False):
        """Converts an YbeExam into a Python dictionary.

        Args:
            minimal (boolean): if set to True we only print the configured options.
                By default this flag is False, meaning we print all the available options, if needed with null placeholders.
        """
        self.minimal = minimal

    def visit(self, node):
        method = f'_visit_{node.__class__.__name__}'
        if not hasattr(self, method):
            raise YbeVisitingError(f'Unknown node encountered of type {type(node)}.')
        return getattr(self, method)(node)

    def _visit_YbeExam(self, node):
        content = {'ybe_version': __version__}

        if len(info := self.visit(node.info)) or not self.minimal:
            content['info'] = info

        content['questions'] = [self.visit(question) for question in node.questions]
        return content

    def _visit_YbeInfo(self, node):
        info = {}

        for item in ['title', 'description', 'document_version', 'date']:
            if (value := getattr(node, item)) is not None or not self.minimal:
                info[item] = value

        if len(value := node.authors) or not self.minimal:
            info['authors'] = value

        return info

    def _visit_MultipleChoice(self, node):
        """Convert the given :class:`ybe.lib.ybe_contents.MultipleChoice` into a dictionary.

        Args:
            node (ybe.lib.ybe_contents.MultipleChoice): the question to convert

        Returns:
            dict: the question as a dictionary
        """
        data = {'id': node.id}

        if node.points is not None or not self.minimal:
            data['points'] = node.points

        data.update(self.visit(node.text))
        data['answers'] = [{'answer': self.visit(el)} for el in node.answers]

        if len(meta_data := self.visit(node.meta_data)) or not self.minimal:
            data['meta_data'] = meta_data

        return {'multiple_choice': data}

    def _visit_MultipleResponse(self, node):
        """Convert the given :class:`ybe.lib.ybe_contents.MultipleResponse` into a dictionary.

        Args:
            node (ybe.lib.ybe_contents.MultipleResponse): the question to convert

        Returns:
            dict: the question as a dictionary
        """
        data = {'id': node.id}

        if node.points is not None or not self.minimal:
            data['points'] = node.points

        data.update(self.visit(node.text))
        data['answers'] = [{'answer': self.visit(el)} for el in node.answers]

        if len(meta_data := self.visit(node.meta_data)) or not self.minimal:
            data['meta_data'] = meta_data

        return {'multiple_response': data}

    def _visit_OpenQuestion(self, node):
        """Convert the given :class:`ybe.lib.ybe_contents.OpenQuestion` into a dictionary.

        Args:
            node (ybe.lib.ybe_contents.OpenQuestion): the question to convert

        Returns:
            dict: the question as a dictionary
        """
        data = {'id': node.id}

        if node.points is not None or not self.minimal:
            data['points'] = node.points

        data.update(self.visit(node.text))

        if len(options := self.visit(node.options)) or not self.minimal:
            data['options'] = options

        if len(meta_data := self.visit(node.meta_data)) or not self.minimal:
            data['meta_data'] = meta_data

        return {'open': data}

    def _visit_TextOnlyQuestion(self, node):
        """Convert the given :class:`ybe.lib.ybe_contents.OpenQuestion` into a dictionary.

        Args:
            node (ybe.lib.ybe_contents.OpenQuestion): the question to convert

        Returns:
            dict: the question as a dictionary
        """
        data = {'id': node.id}
        data.update(self.visit(node.text))
        if len(meta_data := self.visit(node.meta_data)) or not self.minimal:
            data['meta_data'] = meta_data
        return {'text_only': data}

    def _visit_Text(self, node):
        return {'text': self._yaml_text_block(node.text)}

    def _visit_TextHTML(self, node):
        return {'text_html': self._yaml_text_block(node.text)}

    def _visit_TextMarkdown(self, node):
        return {'text_markdown': self._yaml_text_block(node.text)}

    def _visit_MultipleChoiceAnswer(self, node):
        """Convert a single multiple choice answer

        Args:
            node (ybe.lib.ybe_contents.MultipleChoiceAnswer): the multiple choice answers to convert to text.

        Returns:
            dict: the converted answer
        """
        data = {}
        data.update(self.visit(node.text))

        if node.correct or not self.minimal:
            data['correct'] = node.correct

        return data

    def _visit_MultipleResponseAnswer(self, node):
        """Convert a single multiple response answer

        Args:
            node (ybe.lib.ybe_contents.MultipleResponseAnswer): the multiple response answers to convert to text.

        Returns:
            dict: the converted answer
        """
        data = {}
        data.update(self.visit(node.text))

        if node.correct or not self.minimal:
            data['correct'] = node.correct

        return data

    def _visit_OpenQuestionOptions(self, node):
        data = node.__dict__
        if self.minimal:
            return {k: v for k, v in data.items() if v != node.get_default_value(k)}
        return node.__dict__

    def _visit_QuestionMetaData(self, node):
        """Convert the meta data object into a dictionary.

        Args:
            node (ybe.lib.ybe_contents.QuestionMetaData): the text object to convert to a dict text element

        Returns:
            dict: the converted node
        """
        data = node.__dict__
        if self.minimal:
            return {k: self.visit(v) for k, v in data.items() if v != node.get_default_value(k)}
        return {k: self.visit(v) for k, v in node.__dict__.items()}

    def _visit_GeneralQuestionMetaData(self, node):
        data = node.__dict__
        data['keywords'] = self._yaml_inline_list(data['keywords'])
        if self.minimal:
            return {k: v for k, v in data.items() if v != node.get_default_value(k)}
        return data

    def _visit_AnalyticsQuestionMetaData(self, node):
        return node.analytics

    @staticmethod
    def _yaml_text_block(text):
        if '\n' in text:
            return scalarstring.PreservedScalarString(text)
        return text

    @staticmethod
    def _yaml_inline_list(l):
        """Return a list wrapped in a ruamal yaml block, such that the list will be displayed inline.

        Args:
            l (list): the list to wrap

        Returns:
            CommentedSeq: the commented list with the flow style set to True
        """
        wrapped = CommentedSeq(l)
        wrapped.fa.set_flow_style()
        return wrapped
