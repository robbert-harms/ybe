"""Classes for converting an Ybe exam to different layouts like latex, markdown and docx/odt."""

__author__ = 'Robbert Harms'
__date__ = '2021-01-31'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import os
import shutil
import tempfile
import uuid
from hashlib import md5
from bs4 import BeautifulSoup
from urllib.parse import quote
import pathlib

import jinja2
import pypandoc

from ybe.lib.data_types import TextPlain
from ybe.lib.utils import copy_ybe_resources
from ybe.lib.ybe_nodes import MultipleChoice, OpenQuestion, TextOnly, MultipleResponse


class YbeConverter:

    def convert(self, ybe_exam, out_fname, copy_resources=True):
        """Convert the provided ybe exam to a document.

        Args:
            ybe_exam (ybe.lib.ybe_exam.YbeExam): the ybe file object to convert
            out_fname (str): the filename of the file to write
            copy_resources (boolean): if we copy the resources to the same directory as the output file.
        """
        raise NotImplementedError()


class Jinja2Converter(YbeConverter):
    """Convert an Ybe to a single large document using a Jinja2 environment.

    This is meant to convert Ybe to files supporting single large documents, like Latex, Markdown and HTML.

    By inheriting this class, one can override template generation methods to create own templates.

    For example, for loading your own templates::

        class ConverterWithOwnTemplate(Jinja2Converter):
            def get_jinja2_template_loader():
                default_loader = super().get_jinja2_template_loader()
                return ChoiceLoader([FileSystemLoader('/tmp/my_template/'), default_loader]))
    """

    def convert(self, ybe_exam, out_fname, copy_resources=True):
        if not os.path.exists(dir := os.path.dirname(out_fname)):
            os.makedirs(dir)

        out_file = self.get_jinja2_template().render(exam=ybe_exam)

        with open(out_fname, 'w', encoding='utf-8') as f:
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


class YbeToLatex(Jinja2Converter):
    """Ybe to Latex conversion."""

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
        return jinja2.PackageLoader('ybe', 'data/conversion_templates/latex/default')


class YbeToMarkdown(Jinja2Converter):
    """Converts Ybe to a single Markdown file."""

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
        return jinja2.PackageLoader('ybe', 'data/conversion_templates/markdown/default')


class YbeToHTML(Jinja2Converter):
    """Converts Ybe to a single HTML file."""

    def get_jinja2_template(self):
        return self.get_jinja2_environment().get_template('exam.html')

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
        return jinja2.PackageLoader('ybe', 'data/conversion_templates/html/default')


class YbeToDocx(YbeConverter):

    def convert(self, ybe_exam, out_fname, copy_resources=True):
        if not os.path.exists(dir := os.path.dirname(out_fname)):
            os.makedirs(dir)

        md_converter = YbeToMarkdown()
        with tempfile.TemporaryDirectory() as path:
            md_converter.convert(ybe_exam, path + '/exam.md', copy_resources=True)
            pypandoc.convert_file(path + '/exam.md', 'docx',
                                  outputfile=out_fname, extra_args=['--resource-path', path])


class YbeToODT(YbeConverter):

    def convert(self, ybe_exam, out_fname, copy_resources=True):
        if not os.path.exists(dir := os.path.dirname(out_fname)):
            os.makedirs(dir)

        md_converter = YbeToMarkdown()
        with tempfile.TemporaryDirectory() as path:
            md_converter.convert(ybe_exam, path + '/exam.md', copy_resources=True)
            pypandoc.convert_file(path + '/exam.md', 'odt',
                                  outputfile=out_fname, extra_args=['--resource-path', path])


class YbeToQTI_v1p2(YbeConverter):

    def __init__(self, convert_canvas_equations=False):
        """Create the Ybe to QTI v1.2 converter.

        Args:
            convert_canvas_equations (boolean): Converts MathJax equations to a special format used
                by the online Canvas platform.

                This will replace ``<span class="math display">{equation}</span>`` and
                ``<span class="math inline">{equation}</span>`` to:

                .. code-block:: html

                    <img alt="LaTeX: {equation}" class="equation_image" data-equation-content="{equation}"
                        src="equation_images/{equation_html}" title="{equation}"/>
        """
        self._convert_canvas_equations = convert_canvas_equations

        default_kwargs = dict(
            trim_blocks=True,
            autoescape=True,
            lstrip_blocks=True,
            loader=jinja2.PackageLoader('ybe', 'data/conversion_templates/qti/v1p2'))

        env = jinja2.Environment(**default_kwargs)
        env.tests['multiple_choice'] = lambda question: isinstance(question, MultipleChoice)
        env.tests['open'] = lambda question: isinstance(question, OpenQuestion)
        env.tests['text_only'] = lambda question: isinstance(question, TextOnly)
        env.tests['multiple_response'] = lambda question: isinstance(question, MultipleResponse)

        env.globals['preprocess_html'] = self._preprocess_html
        env.globals['multiple_choice_question'] = self._convert_multiple_choice

        self.jinja2_env = env

    def convert(self, ybe_exam, out_fname, copy_resources=True):
        """Convert an Ybe to an QTI v1.2.

        Args:
            ybe_exam (YbeExam): the ybe to convert
            out_fname (str): if a directory we write a directory, if a zip we write it as a zip.
            copy_resources (bool): if we copy the resources or not.
        """
        if not os.path.exists(dir := os.path.dirname(out_fname)):
            os.makedirs(dir)

        if out_fname.endswith('.zip'):
            self._write_qti_zip(ybe_exam, out_fname)
        else:
            self._write_qti_dir(ybe_exam, out_fname)

    def _write_qti_zip(self, ybe_exam, fname):
        """Write the provided Ybe object as a QTI zip.

        Args:
            ybe_exam (ybe.lib.ybe_exam.YbeExam): the ybe file object to dump
            fname (str): the filename to dump to
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._write_qti_dir(ybe_exam, tmp_dir)

            if fname.endswith('.zip'):
                fname = fname[:-len('.zip')]
            shutil.make_archive(fname, 'zip', tmp_dir)

    def _write_qti_dir(self, ybe_exam, dirname):
        """Write the provided Ybe object as a QTI zip.

        Args:
            ybe_exam (ybe.lib.ybe_exam.YbeExam): the ybe file object to dump
            dirname (str): the directory to write to
        """
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        assessment_identifier = md5(str(ybe_exam).encode('utf-8')).hexdigest()
        dependency_identifier = uuid.uuid4().hex

        if not os.path.exists(d := os.path.join(dirname, assessment_identifier)):
            os.makedirs(d)

        self._write_qti_manifest(ybe_exam, dirname, assessment_identifier, dependency_identifier)
        self._write_assessment_meta(ybe_exam, dirname, assessment_identifier)
        self._write_questions_data(ybe_exam, dirname, assessment_identifier)

    def _preprocess_html(self, html_str):
        if self._convert_canvas_equations:
            return self.format_canvas_equations(html_str)
        return html_str

    def _write_qti_manifest(self, ybe_exam, dirname, assessment_identifier, dependency_identifier):
        """Write the QTI data manifest.

        Args:
            ybe_exam (ybe.lib.ybe_contents.YbeExam): the ybe exam object to dump
            dirname (str): the directory to write the manifest (``imsmanifest.xml``) to.
            assessment_identifier (str): UUID of the assessment
            dependency_identifier (str): UUID of the dependencies
        """
        resource_paths = copy_ybe_resources(ybe_exam, dirname)
        resources = {uuid.uuid4().hex: os.path.relpath(path, dirname) for path in resource_paths}

        template_items = {
            'manifest_identifier': uuid.uuid4().hex,
            'title': ybe_exam.info.title.to_plaintext(),
            'date': ybe_exam.info.date.strftime('%Y-%m-%d'),
            'assessment_identifier': assessment_identifier,
            'dependency_identifier': dependency_identifier,
            'resources': resources.items()
        }
        template = self.jinja2_env.get_template('imsmanifest.xml')
        with open(os.path.join(dirname, 'imsmanifest.xml'), 'w', encoding='utf-8') as f:
            f.write(template.render(**template_items))

    def _write_assessment_meta(self, ybe_exam, dirname, assessment_identifier):
        """Write the QTI data manifest.

        Args:
            ybe_exam (ybe.lib.ybe_contents.YbeExam): the ybe exam object to dump
            dirname (str): the directory to write the manifest (``imsmanifest.xml``) to.
            assessment_identifier (str): UUID of the assessment
        """
        if ybe_exam.info.description.is_plaintext():
            description = ybe_exam.info.description.to_plaintext()
        else:
            description = self._preprocess_html(ybe_exam.info.description.to_html())

        template_items = {
            'title': ybe_exam.info.title.to_plaintext(),
            'description': description,
            'points_possible': float(ybe_exam.get_points_possible()),
            'assignment_identifier': uuid.uuid4().hex,
            'assessment_identifier': assessment_identifier,
            'assignment_group_identifier': uuid.uuid4().hex
        }
        template = self.jinja2_env.get_template('assessment_meta.xml')
        with open(os.path.join(dirname, assessment_identifier, 'assessment_meta.xml'), 'w', encoding='utf-8') as f:
            f.write(template.render(**template_items))

    def _write_questions_data(self, ybe_exam, dirname, assessment_identifier):
        """Write the QTI assessment file with the questions.

        Args:
            ybe_exam (ybe.lib.ybe_contents.YbeExam): the ybe exam object to dump
            dirname (str): the directory to write the manifest (``imsmanifest.xml``) to.
            assessment_identifier (str): UUID of the assessment
        """
        converters = {
            MultipleChoice: self._convert_multiple_choice,
            MultipleResponse: self._convert_multiple_response,
            OpenQuestion: self._convert_open_question,
            TextOnly: self._convert_text_only_question
        }

        template_items = {
            'title': ybe_exam.info.title.to_plaintext(),
            'assessment_identifier': assessment_identifier,
            'converted_questions': [converters[question.__class__](question) for question in ybe_exam.questions]
        }
        template = self.jinja2_env.get_template('assessment.xml')
        with open(os.path.join(dirname, assessment_identifier,
                               assessment_identifier + '.xml'), 'w', encoding='utf-8') as f:
            f.write(template.render(**template_items))

    def _convert_multiple_choice(self, question):
        """Convert an Ybe multiple choice question to a QTI XML string

        Args:
            question (MultipleChoice): multiple choice question to convert

        Returns:
            str: XML string with the question information
        """
        answer_ids = [uuid.uuid4().hex[0:6] for _ in question.answers]

        template_items = {
            'question': question,
            'assessment_question_identifierref': uuid.uuid4().hex,
            'answer_ids': answer_ids,
            'respconditions': self._create_multiple_choice_respconditions(question, answer_ids),
        }
        template = self.jinja2_env.get_template('multiple_choice_question.xml')
        return template.render(**template_items)

    def _convert_multiple_response(self, question):
        """Convert an Ybe multiple response question to a QTI XML string

        Args:
            question (MultipleResponse): multiple response question to convert
            text_formatter (TextFormatter): specific actions to format the HTML text for use in the QTI.

        Returns:
            str: XML string with the question information
        """
        answer_ids = [uuid.uuid4().hex[0:6] for _ in question.answers]

        template_items = {
            'question': question,
            'assessment_question_identifierref': uuid.uuid4().hex,
            'answer_ids': answer_ids,
            'respconditions': self._create_multiple_response_respconditions(question, answer_ids),
        }
        template = self.jinja2_env.get_template('multiple_response_question.xml')
        return template.render(**template_items)

    def _convert_open_question(self, question):
        """Convert an Ybe open question to a QTI XML string

        Args:
            question (OpenQuestion): open question to convert

        Returns:
            str: XML string with the question information
        """
        template_items = {
            'question': question,
            'assessment_question_identifierref': uuid.uuid4().hex,
        }
        template = self.jinja2_env.get_template('open_question.xml')
        return template.render(**template_items)

    def _convert_text_only_question(self, question):
        """Convert an Ybe open question to a QTI XML string

        Args:
            question (TextOnly): text only question to convert

        Returns:
            str: XML string with the question information
        """
        template_items = {
            'question': question,
            'assessment_question_identifierref': uuid.uuid4().hex,
        }
        template = self.jinja2_env.get_template('text_only_question.xml')
        return template.render(**template_items)

    def _create_multiple_choice_respconditions(self, question, answer_ids):
        """Create the response conditions for the open questions.

        Args:
            question (MultipleChoice): question to create the response conditions for
            answer_ids (List[str]): the list with the id's of the answers

        Returns:
            List[str]: the list with response conditions for this question.
        """
        correct_answer_id = answer_ids[[answer.correct for answer in question.answers].index(True)]

        respconditions = []
        if question.feedback.general:
            respconditions.append(self.jinja2_env.get_template('respcondition_general.xml').render(
                display_feedback=True))

        for answer_id, answer in zip(answer_ids, question.answers):
            if answer.hint:
                respconditions.append(self.jinja2_env.get_template('respcondition_answer.xml').render(
                    answer_id=answer_id))

        display_feedback = ''
        if question.feedback.on_correct:
            display_feedback = '<displayfeedback feedbacktype="Response" linkrefid="correct_fb"/>'

        respconditions.append(f'''
            <respcondition continue="No">
                <conditionvar>
                    <varequal respident="response1">{correct_answer_id}</varequal>
                </conditionvar>
                <setvar action="Set" varname="SCORE">100</setvar>
                {display_feedback}
            </respcondition>
        ''')

        if question.feedback.on_incorrect:
            respconditions.append(self.jinja2_env.get_template('respcondition_general_incorrect.xml').render())

        return respconditions

    def _create_multiple_response_respconditions(self, question, answer_ids):
        """Create the response conditions for the open questions.

        Args:
            question (MultipleResponse): the multiple response question for which to generate the response conditions
            answer_ids (List[str]): the list with the id's of the answers

        Returns:
            List[str]: the list with response conditions for this question.
        """
        answer_conditions = []
        for answer_id, answer in zip(answer_ids, question.answers):
            if answer.correct:
                answer_conditions.append(f'<varequal respident="response1">{answer_id}</varequal>')
            else:
                answer_conditions.append(f'<not><varequal respident="response1">{answer_id}</varequal></not>')

        respconditions = []

        if question.feedback.general:
            respconditions.append(self.jinja2_env.get_template('respcondition_general.xml').render(
                display_feedback=True))

        for answer_id, answer in zip(answer_ids, question.answers):
            if answer.hint:
                respconditions.append(self.jinja2_env.get_template('respcondition_answer.xml').render(
                    answer_id=answer_id))

        display_feedback = ''
        if question.feedback.on_correct:
            display_feedback = '<displayfeedback feedbacktype="Response" linkrefid="correct_fb"/>'
        answer_conditions_str = '\n'.join(answer_conditions)
        respconditions.append(f'''
            <respcondition continue="No">
                <conditionvar>
                    <and>
                        {answer_conditions_str}
                    </and>
                </conditionvar>
                <setvar action="Set" varname="SCORE">100</setvar>
                {display_feedback}
            </respcondition>
        ''')

        if question.feedback.on_incorrect:
            respconditions.append(self.jinja2_env.get_template('respcondition_general_incorrect.xml').render())

        return respconditions

    @staticmethod
    def format_canvas_equations(text):
        if not text:
            return text

        parsed_html = BeautifulSoup(text, 'lxml')

        def format_equation(text):
            """Prepare the equation for use in Canvas

            Args:
                text (str): LaTeX equation string

            Returns:
                str: the equation string nicely converted for use in Canvas
            """
            if text.startswith('\\('):
                text = text[2:]
            elif text.startswith('\\['):
                text = text[2:]
            elif text.startswith('$'):
                text = text[1:]

            if text.endswith('\\)'):
                text = text[:-2]
            elif text.endswith('\\]'):
                text = text[:-2]
            elif text.endswith('$'):
                text = text[:-1]

            return text

        def equations(class_):
            if not class_:
                return False
            return 'math inline' in class_ or 'math display' in class_

        for span in parsed_html.find_all('span', class_=equations):
            eq = format_equation(span.string)
            eq_img = parsed_html.new_tag('img', attrs={
                'alt': f'alt=LaTeX: {eq}',
                'class': 'equation_image',
                'data-equation-content': eq,
                'src': f'/equation_images/{quote(quote(eq))}',
                'title': eq
            })
            span.replaceWith(eq_img)

        return "".join([str(x) for x in parsed_html.body.children])
