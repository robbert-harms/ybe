__author__ = 'Robbert Harms'
__date__ = '2020-04-18'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import io
import os
import zipfile
from pathlib import Path

from lxml import etree
from bs4 import BeautifulSoup
from datetime import datetime

from ybe.lib.ybe_contents import YbeExam, YbeInfo, MultipleChoice, MultipleResponse, OpenQuestion, TextHTML, Text, \
    MultipleChoiceAnswer, MultipleResponseAnswer, ZipArchiveContext, DirectoryContext, TextOnlyQuestion


def read_qti_zip(zip_file):
    """Parse the data from the provided QTI zip file and return an :class:`ybe.lib.ybe_contents.YbeExam` object.

    Since there are some differences in the data stored by the QTI format and the Ybe format, round-trip conversion
    may not be lossless.

    Args:
        zip_file (str): the filename of the zip file with QTI data to load

    Returns:
        ybe.lib.ybe_contents.YbeExam: an .ybe exam loaded with the content from the QTI zip file.
    """
    path = None
    if isinstance(zip_file, (Path, str)):
        path = os.path.abspath(zip_file)
        archive = zipfile.ZipFile(zip_file, 'r')
    elif isinstance(zip_file, (bytes, bytearray)):
        archive = zipfile.ZipFile(io.BytesIO(zip_file), 'r')
    else:
        archive = zip_file

    if not len(archive.filelist):
        raise ValueError('The zip file is empty.')

    if 'imsmanifest.xml' not in archive.namelist():
        raise ValueError('No imsmanifest.xml found in zip file.')

    def load_func(filename):
        return archive.read(filename)

    ybe_exam = _load_qti_manifest(load_func)
    ybe_exam.resource_context = ZipArchiveContext(path)
    return ybe_exam


def read_qti_dir(dir_name):
    """Parse the data from an extracted QTI zip file and return an :class:`ybe.lib.ybe_contents.YbeExam` object.

    Since there are some differences in the data stored by the QTI format and the Ybe format, round-trip conversion
    may not be lossless.

    Args:
        dir_name (str): the path to the directory with QTI data to load

    Returns:
        ybe.lib.ybe_contents.YbeExam: an .ybe exam loaded with the content from the QTI zip file.
    """
    if not os.path.isdir(dir_name):
        raise ValueError(f'The provided path "{dir_name}" is not a directory.')

    def load_func(filename):
        with open(os.path.join(dir_name, filename), 'rb') as f:
            return f.read()

    ybe_exam = _load_qti_manifest(load_func)
    ybe_exam.resource_context = DirectoryContext(os.path.abspath(dir_name))
    return ybe_exam


def _load_qti_manifest(file_load_func):
    """Load the QTI data from a file source.

    Args:
        file_load_func (Callable[str, bytes]): callable, which, given a filename returns the (binary) content
            of that file.

    Returns:
        ybe.lib.ybe_contents.YbeExam: loaded from the QTI data.
    """
    ims_manifest = etree.fromstring(file_load_func('imsmanifest.xml'))
    ims_manifest_nsmap = ims_manifest.nsmap
    if None in ims_manifest_nsmap:
        del ims_manifest_nsmap[None]

    ims_datetime = ims_manifest.xpath('.//imsmd:dateTime', namespaces=ims_manifest_nsmap)[0].text

    resource_nodes = list(ims_manifest.xpath("//*[local-name() = 'resources']"))[0]

    resources = []
    for resource_node in resource_nodes:
        resource_info = {
            'type': resource_node.get('type'),
            'identifier': resource_node.get('identifier'),
            'href': resource_node.get('href', '')
        }

        for item in resource_node:
            if item.tag.endswith('file'):
                resource_info['file'] = item.get('href')
            if item.tag.endswith('dependency'):
                resource_info['dependency'] = item.get('identifierref')

        resources.append(resource_info)

    questions_resources = list(filter(lambda el: el['type'] == 'imsqti_xmlv1p2', resources))
    meta_resources = list(filter(lambda el: el['href'].endswith('assessment_meta.xml'), resources))

    meta_data = _load_assessment_meta(etree.fromstring(file_load_func(meta_resources[0]['file'])))

    questions = []
    for questions_resource in questions_resources:
        questions.extend(_load_qti_questions(etree.fromstring(file_load_func(questions_resource['file']))))

    return YbeExam(questions=questions,
                   info=YbeInfo(title=meta_data['title'],
                                date=datetime.strptime(ims_datetime, '%Y-%m-%d').now().date()))


def _load_assessment_meta(xml):
    """Parse the assessment meta file and return the title and description.

    Args:
        xml (etree): reference to the questions file

    Returns:
        dict: information parserd from the assessment_meta.xml file
    """
    return {'title': xml[0].text,
            'description': xml[1].text}


def _load_qti_questions(xml):
    """Load questions from a QTI questions file.

    Args:
        xml (etree): the questions file loaded as an etree.

    Returns:
        List [ybe.lib.ybe_contents.Question]: the questions from the provided XML diagram
    """
    section = xml[0][1]
    previous = section
    while section.tag.endswith('section') and len(list(section)):
        previous = section
        section = section[0]

    section = previous
    question_nodes = [el for el in list(section) if el.tag.endswith('item')]

    question_types = {
        'multiple_choice_question': _load_multiple_choice,
        'multiple_answers_question': _load_multiple_response,
        'essay_question': _load_open_question,
        'text_only_question': _load_text_only_question
    }

    ybe_questions = []
    for question_node in question_nodes:
        meta_data = _qtimetadata_to_dict(question_node[0][0])

        if meta_data['question_type'] in question_types:
            ybe_questions.append(question_types[meta_data['question_type']](question_node))

    return ybe_questions


def _qtimetadata_to_dict(qtimetadata):
    """Load a ``qtimetadata`` node as a dictionary.

    Given an XML tree with as root ``qtimetadata``, this converts all the ``qtimetadatafield`` to key value pairs,
    with as key the content of ``fieldlabel`` and as value the content of ``fieldentry``.

    Args:
        qtimetadata (etree): an XML tree starting at the ``qtimetadata`` node

    Returns:
        dict: mapping ``fieldlabel`` to ``fieldentry``.
    """
    result = {}
    for datafield in qtimetadata:
        label = None
        value = None
        for element in datafield:
            if element.tag.endswith('fieldlabel'):
                label = element.text
            if element.tag.endswith('fieldentry'):
                value = element.text

        result[label] = value
    return result


def _load_multiple_choice(question_node):
    """Load a multiple choice question from the given XML tree.

    Args:
        question_node (etree): an question item node

    Returns:
         ybe.lib.ybe_contents.MultipleChoice: multiple choice question
    """
    meta_data = _qtimetadata_to_dict(question_node[0][0])
    text = _load_text(question_node[1][0])

    correct_answer = None
    for resprocessing_node in question_node[2]:
        if resprocessing_node.tag.endswith('respcondition'):
            for item in resprocessing_node:
                if item.tag.endswith('setvar'):
                    correct_answer = resprocessing_node[0][0].text

    answers = []
    for response_label in question_node[1][1][0]:
        answers.append(MultipleChoiceAnswer(text=_load_text(response_label[0]),
                                            correct=(response_label.get('ident') == correct_answer)))

    return MultipleChoice(id=question_node.get('ident'), text=text, answers=answers,
                          points=float(meta_data['points_possible']))


def _load_multiple_response(question_node):
    """Load a multiple response question from the given XML tree.

    Args:
       question_node (etree): an question item node

    Returns:
        ybe.lib.ybe_contents.MultipleChoice: multiple choice question
    """
    meta_data = _qtimetadata_to_dict(question_node[0][0])
    text = _load_text(question_node[1][0])

    correct_answers = []
    and_node = question_node[2][1][0][0]
    for condition_node in and_node:
        if condition_node.tag.endswith('varequal'):
            correct_answers.append(condition_node.text)

    answers = []
    for response_label in question_node[1][1][0]:
        answers.append(MultipleResponseAnswer(text=_load_text(response_label[0]),
                       correct=(response_label.get('ident') in correct_answers)))

    return MultipleResponse(id=question_node.get('ident'), text=text, answers=answers,
                            points=float(meta_data['points_possible']))


def _load_open_question(question_node):
    """Load an open question from the given XML tree.

    Args:
        question_node (etree): an question item node

    Returns:
         ybe.lib.ybe_contents.OpenQuestion: loaded question
    """
    meta_data = _qtimetadata_to_dict(question_node[0][0])
    text = _load_text(question_node[1][0])
    return OpenQuestion(id=question_node.get('ident'), text=text, points=float(meta_data['points_possible']))


def _load_text_only_question(question_node):
    """Load a text only question from the given XML tree.

    Args:
        question_node (etree): an question item node

    Returns:
         ybe.lib.ybe_contents.TextOnlyQuestion: loaded question
    """
    meta_data = _qtimetadata_to_dict(question_node[0][0])
    text = _load_text(question_node[1][0])
    return TextOnlyQuestion(id=question_node.get('ident'), text=text, points=float(meta_data['points_possible']))


def _load_text(material_node):
    """Load the text from a node marked ``material``.

    Args:
        material_node (etree): an question item node

    Returns:
         ybe.lib.ybe_contents.TextNode: a text node subclass
    """
    mattext = material_node[0]
    texttype = mattext.get('texttype')

    if texttype == 'text/html':
        parsed_html = BeautifulSoup(mattext.text, 'lxml')

        def only_local(src):
            return src.startswith('%24IMS-CC-FILEBASE%24/') or src.startswith('$IMS-CC-FILEBASE$/')

        for img in parsed_html.find_all('img', src=only_local):
            src = img.get('src')
            if src.startswith('%24IMS-CC-FILEBASE%24/'):
                src = src[len('%24IMS-CC-FILEBASE%24/'):]
            elif src.startswith('$IMS-CC-FILEBASE$/'):
                src = src[len('$IMS-CC-FILEBASE$/'):]

            img['src'] = src[:src.find('?')]

        def equations(class_):
            if not class_:
                return False
            return 'equation_image' in class_

        for img in parsed_html.find_all('img', class_=equations):
            equation = img['data-equation-content']
            eq_span = parsed_html.new_tag('span', attrs={'class': 'math inline'})
            eq_span.string = f'\\({equation}\\)'
            img.replaceWith(eq_span)

        html_without_html_and_body_tags = "".join([str(x) for x in parsed_html.body.children])
        text = TextHTML(html_without_html_and_body_tags)
    elif texttype == 'text/plain':
        text = Text(mattext.text)
    else:
        raise ValueError('No suitable text type found.')

    return text
