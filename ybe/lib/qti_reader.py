__author__ = 'Robbert Harms'
__date__ = '2020-04-18'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import io
import os
import zipfile
from lxml import etree

from ybe.lib.ybe_contents import YbeFile, YbeFileInfo, MultipleChoice, MultipleResponse, OpenQuestion, TextHTML, Text, \
    MultipleChoiceAnswer, MultipleResponseAnswer


def read_qti_zip(zip_file):
    """Parse the data from the provided QTI zip file and return an :class:`ybe.lib.ybe_contents.YbeFile` object.

    Since there are some differences in the data stored by the QTI format and the Ybe format, round-trip conversion
    may not be lossless.

    Args:
        zip_file (str): the filename of the zip file with QTI data to load

    Returns:
        ybe.lib.ybe_contents.YbeFile: an .ybe file with the content from the QTI zip file.
    """
    if isinstance(zip_file, str):
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

    return _load_qti_manifest(load_func)


def read_qti_dir(dir_name):
    """Parse the data from an extracted QTI zip file and return an :class:`ybe.lib.ybe_contents.YbeFile` object.

    Since there are some differences in the data stored by the QTI format and the Ybe format, round-trip conversion
    may not be lossless.

    Args:
        dir_name (str): the path to the directory with QTI data to load

    Returns:
        ybe.lib.ybe_contents.YbeFile: an .ybe file with the content from the QTI zip file.
    """
    if not os.path.isdir(dir_name):
        raise ValueError(f'The provided path "{dir_name}" is not a directory.')

    def load_func(filename):
        with open(os.path.join(dir_name, filename), 'rb') as f:
            return f.read()

    return _load_qti_manifest(load_func)


def _load_qti_manifest(file_load_func):
    """Load the QTI data from a file source.

    Args:
        file_load_func (Callable[str, bytes]): callable, which, given a filename returns the (binary) content
            of that file.

    Returns:
        ybe.lib.ybe_contents.YbeFile: loaded from the QTI data.
    """
    ims_manifest = etree.fromstring(file_load_func('imsmanifest.xml'))
    ims_manifest_nsmap = ims_manifest.nsmap
    if None in ims_manifest_nsmap:
        del ims_manifest_nsmap[None]

    title = ims_manifest.xpath('.//imsmd:title', namespaces=ims_manifest_nsmap)[0][0].text
    datetime = ims_manifest.xpath('.//imsmd:dateTime', namespaces=ims_manifest_nsmap)[0].text

    resource_nodes = list(ims_manifest.xpath("//*[local-name() = 'resources']"))[0]

    resources = []
    for resource_node in resource_nodes:
        resource_info = {
            'type': resource_node.get('type'),
            'identifier': resource_node.get('identifier')
        }

        for item in resource_node:
            if item.tag.endswith('file'):
                resource_info['file'] = item.get('href')
            if item.tag.endswith('dependency'):
                resource_info['dependency'] = item.get('identifierref')

        resources.append(resource_info)

    questions = []
    for resource in resources:
        if resource['type'] == 'imsqti_xmlv1p2':
            questions_tree = etree.fromstring(file_load_func(resource['file']))
            questions.extend(_load_qti_questions(questions_tree))

    return YbeFile(questions=questions,
                   file_info=YbeFileInfo(title=title, creation_date=datetime))


def _load_qti_questions(xml):
    """Load questions from a QTI questions file.

    Args:
        xml (etree): the questions file loaded as an etree.

    Returns:
        List [ybe.lib.ybe_contents.Question]: the questions from the provided XML diagram
    """
    question_nodes = list(xml[0][1])

    question_types = {
        'multiple_choice_question': _load_multiple_choice,
        'multiple_answers_question': _load_multiple_response,
        'essay_question': _load_open_question
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

    Note that in QTI 1.2 you can only specify a point for the question, not for the answers.
    That is, you can not award different points for the different answers.

    For Ybe conversion, the points are set to the answer marked correct.

    Args:
        question_node (etree): an question item node

    Returns:
         ybe.lib.ybe_contents.MultipleChoice: multiple choice question
    """
    meta_data = _qtimetadata_to_dict(question_node[0][0])
    text = _load_text(question_node[1][0])
    points = float(meta_data['points_possible'])

    correct_answer = None
    for resprocessing_node in question_node[2]:
        if resprocessing_node.tag.endswith('respcondition'):
            for item in resprocessing_node:
                if item.tag.endswith('setvar'):
                    correct_answer = resprocessing_node[0][0].text

    answers = []
    for response_label in question_node[1][1][0]:
        answer_points = 0
        if response_label.get('ident') == correct_answer:
            answer_points = points
        answers.append(MultipleChoiceAnswer(text=_load_text(response_label[0]), points=answer_points))

    return MultipleChoice(id=question_node.get('ident'), text=text, answers=answers)


def _load_multiple_response(question_node):
    """Load a multiple response question from the given XML tree.

    Note that in QTI 1.2 you can only specify a point for the question, not for the answers.
    That is, you can not award different points for the different answers.

    For Ybe conversion, the points are uniformly distributed over the answers marked correct.

    Args:
       question_node (etree): an question item node

    Returns:
        ybe.lib.ybe_contents.MultipleChoice: multiple choice question
    """
    meta_data = _qtimetadata_to_dict(question_node[0][0])
    text = _load_text(question_node[1][0])
    points = float(meta_data['points_possible'])

    answers = []
    for response_label in question_node[1][1][0]:
        answer_points = 0
        # if response_label.get('ident') == correct_answer:
        #     answer_points = points
        # todo

        answers.append(MultipleResponseAnswer(text=_load_text(response_label[0]), points=answer_points))

    return MultipleResponse(id=question_node.get('ident'), text=text, answers=answers)


def _load_open_question(question_node):
    """Load a multiple choice question from the given XML tree.

    Args:
        question_node (etree): an question item node

    Returns:
         ybe.lib.ybe_contents.MultipleChoice: multiple choice question
    """
    meta_data = _qtimetadata_to_dict(question_node[0][0])
    text = _load_text(question_node[1][0])
    return OpenQuestion(id=question_node.get('ident'), text=text, points=float(meta_data['points_possible']))


def _load_text(material_node):
    """Load the text from a node marked ``material``.

    Args:
        material_node (etree): an question item node

    Returns:
         ybe.lib.ybe_contents.TextBlock: a text node subclass
    """
    mattext = material_node[0]
    texttype = mattext.get('texttype')

    if texttype == 'text/html':
        text = TextHTML(mattext.text)
    elif texttype == 'text/plain':
        text = Text(mattext.text)
    else:
        raise ValueError('No suitable text type found.')

    return text
