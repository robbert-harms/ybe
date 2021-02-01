"""Classes for converting an Ybe exam to different layouts like latex, markdown and docx/odt."""

__author__ = 'Robbert Harms'
__date__ = '2021-01-31'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


import os
import pathlib
import jinja2

from ybe.lib.utils import copy_ybe_resources
from ybe.lib.ybe_nodes import MultipleChoice, OpenQuestion, TextOnly, MultipleResponse


class YbeConverter:

    def convert(self, ybe_exam, out_fname, copy_resources=False):
        """Convert the provided ybe exam to a Latex file.

        Args:
            ybe_exam (ybe.lib.ybe_exam.YbeExam): the ybe file object to convert to a latex file.
            out_fname (str): the filename of the latex file to write
            copy_resources (boolean): if we copy the resources to the same directory as the latex file.
        """
        raise NotImplementedError()


class Jinja2Converter(YbeConverter):
    """Convert an Ybe to a single large document using a Jinja2 environment.

    This is meant to convert Ybe to files supporting single large documents, like Latex, Markdown and HTML.
    """

    def convert(self, ybe_exam, out_fname, copy_resources=False):
        if not os.path.exists(dir := os.path.dirname(out_fname)):
            os.makedirs(dir)

        out_file = self.get_jinja2_template().render(exam=ybe_exam)

        with open(out_fname, 'w') as f:
            f.write(out_file)

        if copy_resources:
            directory = pathlib.Path(out_fname).parent.absolute()
            copy_ybe_resources(ybe_exam, directory)

    def get_jinja2_template(self):
        """Get the template we will use to write the output file.

        Returns:
            jinja2.Template: the template to use for writing the output file.
        """
        raise NotImplementedError()

    def get_jinja2_environment(self):
        """Get the Jinja2 environment we use for writing the output file.

        Returns:
            jinja2.Environment: a configured environment
        """
        raise NotImplementedError()

    def get_jinja2_template_loader(self):
        """Get the Jinja2 loader for loading the template files.

        Returns:
            jinja2.PackageLoader: the loader for loading the template.
        """
        raise NotImplementedError()


class DefaultYbeLatexConverter(Jinja2Converter):
    """Create a Ybe to Latex conversion class.

    By inheriting this class, one can override template generation methods to create own templates.

    For example, for loading your own templates::

        class ConverterWithOwnTemplate(Jinja2YbeLatexConverter):

            def get_jinja2_template_loader():
                default_loader = super().get_jinja2_template_loader()
                return ChoiceLoader([FileSystemLoader('/tmp/my_template/'), default_loader]))
    """

    def get_jinja2_template(self):
        return self.get_jinja2_environment().get_template('exam.tex')

    def get_jinja2_environment(self):
        """The special Jinja2 environmet for Latex files.

        The Latex Jinja2 environment uses a different syntax for block and variable strings,
        such to be compatible with Latex.
        """
        default_kwargs = dict(
            block_start_string=r'\BLOCK{',
            block_end_string='}',
            variable_start_string=r'\VAR{',
            variable_end_string='}',
            comment_start_string=r'\#{',
            comment_end_string='}',
            line_statement_prefix='%-',
            line_comment_prefix='%#',
            trim_blocks=True,
            autoescape=False,
            lstrip_blocks=True,
            loader=self.get_jinja2_template_loader())

        env = jinja2.Environment(**default_kwargs)

        env.tests['multiple_choice'] = lambda question: isinstance(question, MultipleChoice)
        env.tests['open'] = lambda question: isinstance(question, OpenQuestion)
        env.tests['text_only'] = lambda question: isinstance(question, TextOnly)
        env.tests['multiple_response'] = lambda question: isinstance(question, MultipleResponse)

        return env

    def get_jinja2_template_loader(self):
        """Get the Jinja2 loader.

        Returns:
            jinja2.PackageLoader: the loader for loading the template.
        """
        return jinja2.PackageLoader('ybe', 'data/latex_templates/default')


class DefaultYbeMarkdownConverter(Jinja2Converter):
    """Converts Ybe to a single large Markdown file."""

    def get_jinja2_template(self):
        return self.get_jinja2_environment().get_template('exam.md')

    def get_jinja2_environment(self):
        default_kwargs = dict(
            trim_blocks=True,
            autoescape=False,
            lstrip_blocks=True,
            loader=self.get_jinja2_template_loader())

        env = jinja2.Environment(**default_kwargs)

        env.tests['multiple_choice'] = lambda question: isinstance(question, MultipleChoice)
        env.tests['open'] = lambda question: isinstance(question, OpenQuestion)
        env.tests['text_only'] = lambda question: isinstance(question, TextOnly)
        env.tests['multiple_response'] = lambda question: isinstance(question, MultipleResponse)

        return env

    def get_jinja2_template_loader(self):
        return jinja2.PackageLoader('ybe', 'data/markdown_templates/default')
