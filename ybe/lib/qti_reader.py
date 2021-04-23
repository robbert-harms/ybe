__author__ = 'Robbert Harms'
__date__ = '2020-04-18'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import io
import os
import zipfile
from pathlib import Path

import bs4
from lxml import etree
from bs4 import BeautifulSoup
from datetime import datetime

from ybe.lib.data_types import TextHTML, TextPlain, ZipArchiveContext, DirectoryContext
from ybe.lib.ybe_nodes import YbeExam, YbeInfo, MultipleChoice, MultipleResponse, OpenQuestion, \
    TextOnly, Feedback, AnswerOption


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
    return QTIv1p2GenericToYbe().convert(file_load_func)


class QTIToYbe:

    def convert(self, file_load_func):
        """Convert the QTI obtainable from the file loading function to an Ybe.

        Args:
            file_load_func (Callable[str, bytes]): callable, which, given a filename returns the (binary) content
            of that file.

        Returns:
            ybe.lib.ybe_contents.YbeExam: loaded from the QTI data.
        """
        raise NotImplementedError()


class QTIv1p2GenericToYbe(QTIToYbe):

    def convert(self, file_load_func):
        ims_manifest = etree.fromstring(file_load_func('imsmanifest.xml'))
        ims_manifest_nsmap = ims_manifest.nsmap
        if None in ims_manifest_nsmap:
            del ims_manifest_nsmap[None]

        ims_datetime_nodes = ims_manifest.xpath('.//imsmd:dateTime', namespaces=ims_manifest_nsmap)
        if len(ims_datetime_nodes):
            ims_datetime = ims_manifest.xpath('.//imsmd:dateTime', namespaces=ims_manifest_nsmap)[0].text
            date = datetime.strptime(ims_datetime, '%Y-%m-%d').now().date()
        else:
            date = datetime.now()

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

        ybe_info = {}
        meta_resources = list(filter(lambda el: el['href'].endswith('assessment_meta.xml'), resources))
        if meta_resources:
            meta_data = self._load_assessment_meta(etree.fromstring(file_load_func(meta_resources[0]['file'])))
            ybe_info.update(meta_data)

        questions = []

        questions_resources = list(filter(lambda el: el['type'] == 'imsqti_xmlv1p2', resources))
        for questions_resource in questions_resources:
            questions.extend(self._load_qti_question_resource(etree.fromstring(
                file_load_func(questions_resource['file']))))

        return YbeExam(questions=questions, info=YbeInfo(date=date, **ybe_info))

    def _get_nodes_ending_with(self, node, postfix):
        """Get all the nodes ending with the provided postfix."""
        return [child for child in node if child.tag.endswith(postfix)]

    def _get_first_node_ending_with(self, node, postfix):
        """Get the first node ending with the provided postfix."""
        nodes = self._get_nodes_ending_with(node, postfix)
        if len(nodes):
            return nodes[0]
        return None

    def _load_assessment_meta(self, xml):
        """Parse the assessment meta file and return the title and description.

        Args:
            xml (etree): reference to the questions file

        Returns:
            dict: information parserd from the assessment_meta.xml file
        """
        items = {}

        if (title_node := self._get_first_node_ending_with(xml, 'title')) is not None:
            items['title'] = TextPlain(title_node.text)
        if (description_node := self._get_first_node_ending_with(xml, 'description')) is not None:
            items['description'] = self._parse_html_str(description_node.text)
        return items

    def _load_qti_question_resource(self, xml):
        """Load questions from a QTI questions resource file.

        Args:
            xml (etree): the questions file loaded as an etree.

        Returns:
            List [ybe.lib.ybe_contents.Question]: the questions from the provided XML diagram
        """
        sections = self._get_section_nodes(xml)

        question_nodes = []
        for section in sections:
            question_nodes.extend(self._get_nodes_ending_with(section, 'item'))

        question_types = {
            'multiple_choice_question': self._load_multiple_choice,
            'multiple_answers_question': self._load_multiple_response,
            'essay_question': self._load_open_question,
            'text_only_question': self._load_text_only_question
        }

        ybe_questions = []
        for question_node in question_nodes:
            meta_data = self._qtimetadata_to_dict(question_node[0][0])

            if meta_data['question_type'] in question_types:
                ybe_questions.append(question_types[meta_data['question_type']](question_node))

        return ybe_questions

    def _get_section_nodes(self, main_node):
        """Get, from the main node, all the question nodes.

        Args:
            main_node (etree): the main node is typically structured as ::

                <questestinterop>
                    <assessment ident="" title="">
                        <qtimetadata>...</qtimetadata>
                        <section ident="root_section">...</section>
                        ...
                        <section ident="root_section">...</section>
                    </assessment>
                <questestinterop>

                from this, we load all the section nodes.

        Returns:
            List[etree]: List of section nodes
        """
        sections = []
        assessment_node = main_node[0]
        for child in assessment_node:
            if child.tag.endswith('section') and len(list(child)):
                sections.append(child)
        return sections

    def _qtimetadata_to_dict(self, qtimetadata):
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

    def _load_multiple_choice(self, question_node):
        """Load a multiple choice question from the given XML tree.

        Args:
            question_node (etree): an question item node

        Returns:
             ybe.lib.ybe_contents.MultipleChoice: multiple choice question
        """
        meta_data = self._qtimetadata_to_dict(question_node[0][0])
        feedbacks = self._load_feedbacks(self._get_nodes_ending_with(question_node, 'itemfeedback'))
        text = self._load_text(question_node[1][0])
        title = question_node.get('title')

        correct_answer = None
        for resprocessing_node in question_node[2]:
            if resprocessing_node.tag.endswith('respcondition'):
                for item in resprocessing_node:
                    if item.tag.endswith('setvar'):
                        correct_answer = resprocessing_node[0][0].text

        answers = []
        for response_label in question_node[1][1][0]:
            response_id = response_label.get('ident')
            answers.append(AnswerOption(text=self._load_text(response_label[0]),
                                        correct=(response_id == correct_answer),
                                        hint=feedbacks.get(f'{response_id}_fb')))

        return MultipleChoice(id=question_node.get('ident'),
                              title=title, text=text, answers=answers,
                              points=float(meta_data['points_possible']),
                              feedback=Feedback(general=feedbacks.get('general_fb'),
                                                on_correct=feedbacks.get('correct_fb'),
                                                on_incorrect=feedbacks.get('general_incorrect_fb')))

    def _load_multiple_response(self, question_node):
        """Load a multiple response question from the given XML tree.

        Args:
           question_node (etree): an question item node

        Returns:
            ybe.lib.ybe_contents.MultipleChoice: multiple choice question
        """
        meta_data = self._qtimetadata_to_dict(question_node[0][0])
        feedbacks = self._load_feedbacks(self._get_nodes_ending_with(question_node, 'itemfeedback'))
        text = self._load_text(question_node[1][0])
        title = question_node.get('title')
        correct_answers = self._load_multiple_response_correct_answers(question_node[2])

        answers = []
        for response_label in question_node[1][1][0]:
            response_id = response_label.get('ident')
            answers.append(AnswerOption(text=self._load_text(response_label[0]),
                                        correct=(response_id in correct_answers),
                                        hint=feedbacks.get(f'{response_id}_fb')))

        return MultipleResponse(id=question_node.get('ident'),
                                title=title, text=text, answers=answers,
                                points=float(meta_data['points_possible']),
                                feedback=Feedback(general=feedbacks.get('general_fb'),
                                                  on_correct=feedbacks.get('correct_fb'),
                                                  on_incorrect=feedbacks.get('general_incorrect_fb')))

    def _load_multiple_response_correct_answers(self, resprocessing_node):
        """Load the correct answers from the right ``respcondition`` node.

        Args:
            resprocessing_node (etree): the node with all the respcondition nodes.

        Returns:
            List[str]: list with the correct answer id's
        """

        def is_scoring_respcondition(respcondition):
            """Get the respcondition node holding the scoring condition.

            This is typically the node holding the ``setvar`` node.
            """
            return len(self._get_nodes_ending_with(respcondition, 'setvar'))

        def parse_correct_answers(conditionvar):
            """Parse the correct answers from the conditionvar node."""
            correct_answers = []
            and_node = conditionvar[0]
            for condition_node in and_node:
                if condition_node.tag.endswith('varequal'):
                    correct_answers.append(condition_node.text)
            return correct_answers

        for respcondition in resprocessing_node:
            if is_scoring_respcondition(respcondition):
                return parse_correct_answers(respcondition[0])
        return []

    def _load_open_question(self, question_node):
        """Load an open question from the given XML tree.

        Args:
            question_node (etree): an question item node

        Returns:
             ybe.lib.ybe_contents.OpenQuestion: loaded question
        """
        meta_data = self._qtimetadata_to_dict(question_node[0][0])
        feedbacks = self._load_feedbacks(self._get_nodes_ending_with(question_node, 'itemfeedback'))
        text = self._load_text(question_node[1][0])
        title = question_node.get('title')

        return OpenQuestion(id=question_node.get('ident'),
                            title=title, text=text,
                            points=float(meta_data['points_possible']),
                            feedback=Feedback(general=feedbacks.get('general_fb')))

    def _load_feedbacks(self, feedback_nodes):
        """Load feedback from a list of feedback nodes.

        Args:
            feedback_nodes (List[etree]): list of feedback nodes. These are structured as::

                <itemfeedback ident="...">
                    <flow_mat>
                    <material>
                        <mattext texttype="text/html">...</mattext>
                    </material>
                    </flow_mat>
                </itemfeedback>

        Returns:
            dict[str, TextNode]: dictionary mapping the ident keys to text nodes
        """
        feedbacks = {}
        for node in feedback_nodes:
            id = node.get('ident')
            text = self._load_text(node[0][0])
            feedbacks[id] = text
        return feedbacks

    def _load_text_only_question(self, question_node):
        """Load a text only question from the given XML tree.

        Args:
            question_node (etree): an question item node

        Returns:
             ybe.lib.ybe_contents.TextOnlyQuestion: loaded question
        """
        title = question_node.get('title')
        text = self._load_text(question_node[1][0])
        return TextOnly(id=question_node.get('ident'), text=text, title=title)

    def _load_text(self, material_node):
        """Load the text from a node marked ``material``.

        Args:
            material_node (etree): a node marked as "material"

        Returns:
             ybe.lib.ybe_contents.TextNode: a text node subclass
        """
        mattext = material_node[0]
        texttype = mattext.get('texttype')

        if mattext.text is None:
            return None

        if texttype == 'text/html':
            return self._parse_html_str(mattext.text)
        if texttype == 'text/plain':
            return TextPlain(mattext.text)

        raise ValueError('No suitable text type found.')

    def _parse_html_str(self, text):
        """Parse a string with HTML content into a TextHTML datatype.

        This correctly converses equations and images for use in Ybe.

        Args:
            text (str): a string with HTML content

        Returns:
            TextHTML: a TextHTML node with the prepared and converted data.
        """
        parsed_html = BeautifulSoup(text, 'lxml')

        def only_local(src):
            return src.startswith('%24IMS-CC-FILEBASE%24/') or src.startswith('$IMS-CC-FILEBASE$/')

        for img in parsed_html.find_all('img', src=only_local):
            src = img.get('src')
            if src.startswith('%24IMS-CC-FILEBASE%24/'):
                src = src[len('%24IMS-CC-FILEBASE%24/'):]
            elif src.startswith('$IMS-CC-FILEBASE$/'):
                src = src[len('$IMS-CC-FILEBASE$/'):]

            if src.find('?') >= 0:
                src = src[:src.find('?')]
            img['src'] = src

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
        return TextHTML(html_without_html_and_body_tags)
