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
from ybe.lib.ybe_nodes import MultipleChoice, MultipleResponse, OpenQuestion, TextOnly


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
        'title': _escape_attr(text_formatter.format(ybe_exam.info.title.to_html())),
        'description': _escape_attr(text_formatter.format(ybe_exam.info.description.to_html())),
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
        'title': _escape_attr(text_formatter.format(ybe_exam.info.title.to_html())),
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
        TextOnly: _convert_text_only_question
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

    feedback_items = _convert_feedback_items(question.feedback, text_formatter)

    answers = []
    for answer_id, answer in zip(answer_ids, question.answers):
        answers.append(_convert_multi_option_answer(answer_id, answer.text, text_formatter))
        if answer.hint:
            feedback_items.append(_convert_feedback(f'{answer_id}_fb', answer.hint, text_formatter))

    template_items = {
        'question_identifier': _escape_attr(question.id),
        'question_title': 'Question',
        'points_possible': question.points,
        'assessment_question_identifierref': uuid.uuid4().hex,
        'question_text': _escape_text(text_formatter.format(question.text.to_html())),
        'original_answer_ids': ','.join(answer_ids),
        'correct_answer_id': answer_ids[correct_answer_ind],
        'answers': '\n'.join(answers),
        'respconditions': '\n'.join(_create_multiple_choice_respconditions(question, answer_ids)),
        'feedback_items': '\n'.join(feedback_items)
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

    feedback_items = _convert_feedback_items(question.feedback, text_formatter)

    answers = []
    for answer_id, answer in zip(answer_ids, question.answers):
        answers.append(_convert_multi_option_answer(answer_id, answer.text, text_formatter))
        if answer.hint:
            feedback_items.append(_convert_feedback(f'{answer_id}_fb', answer.hint, text_formatter))

    template_items = {
        'question_identifier': _escape_attr(question.id),
        'question_title': 'Question',
        'points_possible': question.points,
        'assessment_question_identifierref': uuid.uuid4().hex,
        'question_text': _escape_text(text_formatter.format(question.text.to_html())),
        'original_answer_ids': ','.join(answer_ids),
        'answers': '\n'.join(answers),
        'respconditions': '\n'.join(_create_multiple_response_respconditions(question, answer_ids)),
        'feedback_items': '\n'.join(feedback_items)
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
    feedback_items = _convert_feedback_items(question.feedback, text_formatter, allowed_items=['general'])

    template_items = {
        'question_identifier': _escape_attr(question.id),
        'question_title': 'Question',
        'points_possible': question.points,
        'assessment_question_identifierref': uuid.uuid4().hex,
        'question_text': _escape_text(text_formatter.format(question.text.to_html())),
        'respconditions': '\n'.join(_create_open_question_respconditions(question)),
        'feedback_items': '\n'.join(feedback_items)
    }
    template = resources.read_text('ybe.data.qti_template', 'assessment_open_question.xml')
    return template.format(**template_items)


def _convert_text_only_question(question, text_formatter):
    """Convert an Ybe open question to a QTI XML string

    Args:
        question (TextOnly): text only question to convert
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
        'title': _escape_attr(text_formatter.format(ybe_exam.info.title.to_html())),
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


def _create_open_question_respconditions(question):
    """Create the response conditions for the open questions.

    Args:
        question (OpenQuestion): open question to create the response conditions for

    Returns:
        List[str]: the list with response conditions for this open question.
    """
    respconditions = []
    if question.feedback.general is not None:
        respconditions.append('''
            <respcondition continue="Yes">
                <conditionvar>
                    <other/>
                </conditionvar>
                <displayfeedback feedbacktype="Response" linkrefid="general_fb"/>
            </respcondition>
        ''')
    respconditions.append('''
        <respcondition continue="No">
            <conditionvar>
                <other/>
            </conditionvar>
        </respcondition>
    ''')
    return respconditions


def _create_multiple_choice_respconditions(question, answer_ids):
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
        respconditions.append('''
            <respcondition continue="Yes">
                <conditionvar>
                    <other/>
                </conditionvar>
                <displayfeedback feedbacktype="Response" linkrefid="general_fb"/>
            </respcondition>
        ''')

    for answer_id, answer in zip(answer_ids, question.answers):
        if answer.hint:
            respconditions.append(f'''
                <respcondition continue="Yes">
                    <conditionvar>
                        <varequal respident="response1">{answer_id}</varequal>
                    </conditionvar>
                    <displayfeedback feedbacktype="Response" linkrefid="{answer_id}_fb"/>
                </respcondition>
            ''')

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
        respconditions.append(f'''
            <respcondition continue="Yes">
                <conditionvar>
                    <other/>
                </conditionvar>
                <displayfeedback feedbacktype="Response" linkrefid="general_incorrect_fb"/>
            </respcondition>
        ''')

    return respconditions


def _create_multiple_response_respconditions(question, answer_ids):
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
            answer_conditions.append(f'''<not><varequal respident="response1">{answer_id}</varequal></not>''')

    respconditions = []

    if question.feedback.general:
        respconditions.append('''
            <respcondition continue="Yes">
                <conditionvar>
                    <other/>
                </conditionvar>
                <displayfeedback feedbacktype="Response" linkrefid="general_fb"/>
            </respcondition>
        ''')

    for answer_id, answer in zip(answer_ids, question.answers):
        if answer.hint:
            respconditions.append(f'''
                <respcondition continue="Yes">
                    <conditionvar>
                        <varequal respident="response1">{answer_id}</varequal>
                    </conditionvar>
                    <displayfeedback feedbacktype="Response" linkrefid="{answer_id}_fb"/>
                </respcondition>
            ''')

    display_feedback = ''
    if question.feedback.on_correct:
        display_feedback = '<displayfeedback feedbacktype="Response" linkrefid="correct_fb"/>'

    respconditions.append(f'''
        <respcondition continue="No">
            <conditionvar>
                <and>
                    {answer_conditions}
                </and>
            </conditionvar>
            <setvar action="Set" varname="SCORE">100</setvar>
            {display_feedback}
        </respcondition>
    ''')

    if question.feedback.on_incorrect:
        respconditions.append(f'''
            <respcondition continue="Yes">
                <conditionvar>
                    <other/>
                </conditionvar>
                <displayfeedback feedbacktype="Response" linkrefid="general_incorrect_fb"/>
            </respcondition>
        ''')

    return respconditions


def _convert_feedback_items(feedback, text_formatter, allowed_items=None):
    """Convert the feedback items of a question.

    Args:
        feedback (Feedback): the feedback data
        text_formatter (TextFormatter): specific actions to format the HTML text for use in the QTI.
        allowed_items (list): the list of allowed feedback items

    Returns:
        List[str]: list with QTI elements for the feedback
    """
    allowed_items = allowed_items or ['general', 'on_correct', 'on_incorrect']

    feedback_items = []
    if feedback.general and 'general' in allowed_items:
        feedback_items.append(_convert_feedback('general_fb', feedback.general, text_formatter))
    if feedback.on_correct and 'on_correct' in allowed_items:
        feedback_items.append(_convert_feedback('correct_fb', feedback.on_correct, text_formatter))
    if feedback.on_incorrect and 'on_incorrect' in allowed_items:
        feedback_items.append(_convert_feedback('general_incorrect_fb', feedback.on_incorrect, text_formatter))

    return feedback_items


def _convert_feedback(feedback_id, text, text_formatter):
    """Convert the feedback items of the provided question into QTI format.

    This will convert the general feedback

    Args:
        feedback_id (str): the id of the feedback
        text (TextData): the data element containing the text to write
        text_formatter (TextFormatter): specific actions to format the HTML text for use in the QTI.

    Returns:
        str: XML string with the question information
    """
    html = _escape_text(text_formatter.format(text.to_html())).strip()
    return f'''
        <itemfeedback ident="{feedback_id}">
            <flow_mat>
                <material>
                    <mattext texttype="text/html">{html}</mattext>
                </material>
            </flow_mat>
        </itemfeedback>
    '''.strip()


def _convert_multi_option_answer(answer_id, text, text_formatter):
    """Convert a multiple choice or multiple response text to QTI format.

    Args:
        answer_id (str): the id of the answer
        text (TextData): the data element containing the text to write.
        text_formatter (TextFormatter): specific actions to format the HTML text for use in the QTI.

    Returns:
        str: the QTI formatted text
    """
    html = _escape_text(text_formatter.format(text.to_html())).strip()
    return f'''
        <response_label ident="{answer_id}">
            <material>
              <mattext texttype="text/html">{html}</mattext>
            </material>
          </response_label>
    '''.strip()


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

