__author__ = 'Robbert Harms'
__date__ = '2020-04-18'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import os
import shutil
import tempfile
import uuid
from importlib import resources
from hashlib import md5
from xml.sax.saxutils import quoteattr, escape
from bs4 import BeautifulSoup
from urllib.parse import quote

from ybe.lib.utils import copy_ybe_resources
from ybe.lib.ybe_contents import MultipleChoice, MultipleResponse, OpenQuestion, TextOnlyQuestion


def write_qti_zip(ybe_exam, fname, text_formatter=None):
    """Write the provided Ybe object as a QTI zip.

    Args:
        ybe_exam (ybe.lib.ybe_exam.YbeExam): the ybe file object to dump
        fname (str): the filename to dump to
        text_formatter (TextFormatter): specific actions to format the HTML text for use in the QTI.
            If not specified, defaults to :class:`NoOpTextFormatter`.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        write_qti_dir(ybe_exam, tmp_dir, text_formatter=text_formatter)
        shutil.make_archive(fname.rstrip('.zip'), 'zip', tmp_dir)


def write_qti_dir(ybe_exam, dirname, text_formatter=None):
    """Write the provided Ybe object as a QTI zip.

    Args:
        ybe_exam (ybe.lib.ybe_exam.YbeExam): the ybe file object to dump
        dirname (str): the directory to write to
        text_formatter (TextFormatter): specific actions to format the HTML text for use in the QTI.
            If not specified, defaults to :class:`NoOpTextFormatter`.
    """
    text_formatter = text_formatter or NoOpTextFormatter()

    if not os.path.exists(dirname):
        os.makedirs(dirname)

    assessment_identifier = md5(str(ybe_exam).encode('utf-8')).hexdigest()
    dependency_identifier = uuid.uuid4().hex

    if not os.path.exists(d := os.path.join(dirname, assessment_identifier)):
        os.makedirs(d)

    _write_assessment_meta(ybe_exam, dirname, assessment_identifier, text_formatter)
    _write_questions_data(ybe_exam, dirname, assessment_identifier, text_formatter)
    _write_qti_manifest(ybe_exam, dirname, assessment_identifier, dependency_identifier, text_formatter)


class TextFormatter:
    """Strategy pattern for formatting the HTML text for use in the QTI XML files."""

    def format(self, text):
        """Format the provided string of HTML text.

        Args:
            text (str): the text to format according to this strategy

        Returns:
            str: the formatted HTML
        """
        raise NotImplementedError()


class NoOpTextFormatter(TextFormatter):
    """Applies no additional formatting to the HTML"""
    def format(self, text):
        return text


class ConvertCanvasEquations(TextFormatter):
    """Converts MathJax equations to a special format used by the online Canvas platform.

    This will replace ``<span class="math display">{equation}</span>`` and
    ``<span class="math inline">{equation}</span>`` to:

    .. code-block:: html

        <img alt="LaTeX: {equation}" class="equation_image" data-equation-content="{equation}"
            src="equation_images/{equation_html}" title="{equation}"/>
    """
    def format(self, text):
        if not text:
            return text

        parsed_html = BeautifulSoup(text, 'lxml')

        def equations(class_):
            if not class_:
                return False
            return 'math inline' in class_ or 'math display' in class_

        for span in parsed_html.find_all('span', class_=equations):
            eq = self._format_equation(span.string)
            eq_img = parsed_html.new_tag('img', attrs={
                'alt': f'alt=LaTeX: {eq}',
                'class': 'equation_image',
                'data-equation-content': eq,
                'src': f'/equation_images/{quote(quote(eq))}',
                'title': eq
            })
            span.replaceWith(eq_img)

        return "".join([str(x) for x in parsed_html.body.children])

    def _format_equation(self, text):
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


def _write_assessment_meta(ybe_exam, dirname, assessment_identifier, text_formatter):
    """Write the QTI data manifest.

    Args:
        ybe_exam (ybe.lib.ybe_contents.YbeExam): the ybe exam object to dump
        dirname (str): the directory to write the manifest (``imsmanifest.xml``) to.
        assessment_identifier (str): UUID of the assessment
        text_formatter (TextFormatter): specific actions to format the HTML text for use in the QTI.
    """
    template_items = {
        'title': _escape_attr(ybe_exam.info.title),
        'description': _escape_attr(text_formatter.format(ybe_exam.info.description or '')),
        'points_possible': float(ybe_exam.get_points_possible()),
        'assignment_identifier': uuid.uuid4().hex,
        'assessment_identifier': assessment_identifier,
        'assignment_group_identifier': uuid.uuid4().hex
    }
    template = resources.read_text('ybe.data.qti_template', 'assessment_meta.xml')
    assessment_meta = template.format(**template_items)

    with open(os.path.join(dirname, assessment_identifier, 'assessment_meta.xml'), 'w') as f:
        f.write(assessment_meta)


def _write_questions_data(ybe_exam, dirname, assessment_identifier, text_formatter):
    """Write the QTI assessment file with the questions.

    Args:
        ybe_exam (ybe.lib.ybe_contents.YbeExam): the ybe exam object to dump
        dirname (str): the directory to write the manifest (``imsmanifest.xml``) to.
        assessment_identifier (str): UUID of the assessment
        text_formatter (TextFormatter): specific actions to format the HTML text for use in the QTI.
    """
    template_items = {
        'title': _escape_attr(ybe_exam.info.title),
        'assessment_identifier': assessment_identifier,
        'questions': '\n'.join(_get_questions(ybe_exam, text_formatter)),
    }
    template = resources.read_text('ybe.data.qti_template', 'assessment.xml')
    assessment = template.format(**template_items)

    with open(os.path.join(dirname, assessment_identifier, assessment_identifier + '.xml'), 'w') as f:
        f.write(assessment)


def _get_questions(ybe_exam, text_formatter):
    """Get a list of XML snippits for each of the exams.

    Args:
        ybe_exam (ybe.lib.ybe_contents.YbeExam): the ybe exam object to dump
        text_formatter (TextFormatter): specific actions to format the HTML text for use in the QTI.

    Returns:
        List[str]: list of XML snippits for each of the questions
    """
    converters = {
        MultipleChoice: _convert_multiple_choice,
        MultipleResponse: _convert_multiple_response,
        OpenQuestion: _convert_open_question,
        TextOnlyQuestion: _convert_text_only_question
    }
    return [converters[question.__class__](question, text_formatter) for question in ybe_exam.questions]


def _convert_multiple_choice(question, text_formatter):
    """Convert an Ybe multiple choice question to a QTI XML string

    Args:
        question (MultipleChoice): multiple choice question to convert
        text_formatter (TextFormatter): specific actions to format the HTML text for use in the QTI.

    Returns:
        str: XML string with the question information
    """
    answer_ids = [uuid.uuid4().hex[0:6] for _ in question.answers]
    correct_answer_ind = [answer.correct for answer in question.answers].index(True)

    answers = []
    answer_template = '''
        <response_label ident="{answer_id}">
            <material>
                <mattext texttype="text/html">{text}</mattext>
            </material>
        </response_label>
    '''
    for answer_id, answer in zip(answer_ids, question.answers):
        html = _escape_text(text_formatter.format(answer.text.to_html())).strip()
        answers.append(answer_template.format(answer_id=answer_id, text=html).strip())

    template_items = {
        'question_identifier': _escape_attr(question.id),
        'question_title': 'Question',
        'points_possible': question.points,
        'assessment_question_identifierref': uuid.uuid4().hex,
        'question_text': _escape_text(text_formatter.format(question.text.to_html())),
        'original_answer_ids': ','.join(answer_ids),
        'correct_answer_id': answer_ids[correct_answer_ind],
        'answers': '\n'.join(answers)
    }
    template = resources.read_text('ybe.data.qti_template', 'assessment_multiple_choice.xml')
    return template.format(**template_items).strip()


def _convert_multiple_response(question, text_formatter):
    """Convert an Ybe multiple response question to a QTI XML string

    Args:
        question (MultipleResponse): multiple response question to convert
        text_formatter (TextFormatter): specific actions to format the HTML text for use in the QTI.

    Returns:
        str: XML string with the question information
    """
    answer_ids = [uuid.uuid4().hex[0:6] for _ in question.answers]

    answers = []
    answer_template = '''
        <response_label ident="{answer_id}">
            <material>
              <mattext texttype="text/html">{text}</mattext>
            </material>
          </response_label>
    '''
    for answer_id, answer in zip(answer_ids, question.answers):
        html = _escape_text(text_formatter.format(answer.text.to_html())).strip()
        answers.append(answer_template.format(answer_id=answer_id, text=html).strip())

    answer_conditions = []
    for answer_id, answer in zip(answer_ids, question.answers):
        if answer.correct:
            answer_conditions.append(f'<varequal respident="response1">{answer_id}</varequal>')
        else:
            answer_conditions.append(f'''<not><varequal respident="response1">{answer_id}</varequal></not>''')

    template_items = {
        'question_identifier': _escape_attr(question.id),
        'question_title': 'Question',
        'points_possible': question.points,
        'assessment_question_identifierref': uuid.uuid4().hex,
        'question_text': _escape_text(text_formatter.format(question.text.to_html())),
        'original_answer_ids': ','.join(answer_ids),
        'answer_conditions': '\n'.join(answer_conditions),
        'answers': '\n'.join(answers)
    }
    template = resources.read_text('ybe.data.qti_template', 'assessment_multiple_response.xml')
    return template.format(**template_items).strip()


def _convert_open_question(question, text_formatter):
    """Convert an Ybe open question to a QTI XML string

    Args:
        question (OpenQuestion): open question to convert
        text_formatter (TextFormatter): specific actions to format the HTML text for use in the QTI.

    Returns:
        str: XML string with the question information
    """
    template_items = {
        'question_identifier': _escape_attr(question.id),
        'question_title': 'Question',
        'points_possible': question.points,
        'assessment_question_identifierref': uuid.uuid4().hex,
        'question_text': _escape_text(text_formatter.format(question.text.to_html()))
    }
    template = resources.read_text('ybe.data.qti_template', 'assessment_open_question.xml')
    return template.format(**template_items)


def _convert_text_only_question(question, text_formatter):
    """Convert an Ybe open question to a QTI XML string

    Args:
        question (TextOnlyQuestion): text only question to convert
        text_formatter (TextFormatter): specific actions to format the HTML text for use in the QTI.

    Returns:
        str: XML string with the question information
    """
    template_items = {
        'question_identifier': _escape_attr(question.id),
        'question_title': 'Question',
        'assessment_question_identifierref': uuid.uuid4().hex,
        'question_text': _escape_text(text_formatter.format(question.text.to_html()))
    }
    template = resources.read_text('ybe.data.qti_template', 'assessment_text_only_question.xml')
    return template.format(**template_items)


def _write_qti_manifest(ybe_exam, dirname, assessment_identifier, dependency_identifier, text_formatter):
    """Write the QTI data manifest.

    Args:
        ybe_exam (ybe.lib.ybe_contents.YbeExam): the ybe exam object to dump
        dirname (str): the directory to write the manifest (``imsmanifest.xml``) to.
        assessment_identifier (str): UUID of the assessment
        dependency_identifier (str): UUID of the dependencies
        text_formatter (TextFormatter): specific actions to format the HTML text for use in the QTI.
    """
    template_items = {
        'manifest_identifier': uuid.uuid4().hex,
        'title': _escape_attr(ybe_exam.info.title),
        'date': ybe_exam.info.date.strftime('%Y-%m-%d'),
        'assessment_identifier': assessment_identifier,
        'dependency_identifier': dependency_identifier,
        'additional_resources': '\n'.join(_get_resources(ybe_exam, dirname)),
    }
    template = resources.read_text('ybe.data.qti_template', 'imsmanifest.xml')
    manifest_str = template.format(**template_items)

    with open(os.path.join(dirname, 'imsmanifest.xml'), 'w') as f:
        f.write(manifest_str)


def _get_resources(ybe_exam, dirname):
    """Copy the resources and return a list of XML strings to be added to the manifest.

    Args:
        ybe_exam (ybe.lib.ybe_contents.YbeExam): the ybe exam object to dump
        dirname (str): the directory we are writing the results to

    Returns:
        List[str]: list of XML snippits for the additional resources
    """
    resource_template = '''
        <resource identifier="{resource_id}" type="webcontent" href="{path}">
            <file href="{path}"/>
        </resource>
    '''
    resource_paths = copy_ybe_resources(ybe_exam, dirname)
    resource_rel_paths = [os.path.relpath(path, dirname) for path in resource_paths]

    additional_resources = []
    for path in resource_rel_paths:
        safe_path = _escape_attr(path)
        additional_resources.append(resource_template.format(
            resource_id=uuid.uuid4().hex, path=safe_path).strip())

    return additional_resources


def _escape_attr(value):
    """Prepare the provided value for use as an attribute in xml

    Args:
        value (str): the value we want to escape for use as an attribute value.

    Returns:
        str: the escaped value, without surrounding quotes
    """
    escaped = quoteattr(value, {'"': '&quot;'})
    return escaped[1:-1]


def _escape_text(value):
    """Prepare the provided value for use as a text value in XML

    Args:
        value (str): the value we want to escape for use as a text value

    Returns:
        str: the escaped value
    """
    return escape(value)

