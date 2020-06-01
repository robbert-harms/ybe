from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2020-04-14'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import os
import shutil
import zipfile
from datetime import date

import pypandoc
from bs4 import BeautifulSoup
from dataclasses import dataclass, field, fields
from typing import List, Union

from ybe.lib.utils import get_default_value, markdown_to_latex, html_to_latex


@dataclass
class YbeNode:
    """Basic inheritance class for all Ybe related content nodes."""

    def accept_visitor(self, visitor):
        """Ybe nodes support the ``visitor pattern`` to allow for document traversal.

        Args:
            visitor (YbeNodeVisitor): the visitor we will give a callback.
        """
        visitor.visit(self)

    def get_default_value(self, attribute_name):
        """Get the default value for an attribute of this node.

        Args:
            attribute_name (str): the name of the attribute for which we want the default value

        Returns:
            Any: the default value
        """
        raise NotImplementedError()

    def get_resources(self):
        """Get a list of :class:`YbeResources` in this node or sub-tree.

        This will need to do a recursive lookup to find all the resources.

        Returns:
            List[YbeResource]: list of resources nodes.
        """
        raise NotImplementedError()


class YbeNodeVisitor:
    """Interface class for a node visitor, part of the ``visitor`` design pattern."""

    def visit(self, node):
        """Visit method, called by the node which accepted this visitor.

        Args:
            node (YbeNode): the node being visited.
        """
        raise NotImplementedError()


class SimpleYbeNode(YbeNode):
    """Simple implementation of the required methods of an YbeNode."""

    def get_default_value(self, attribute_name):
        """By default, resolve the default value using the dataclass fields."""
        if attribute_name not in self.__dict__:
            raise AttributeError('Attribute not found in class.')

        for field in fields(self):
            if field.name == attribute_name:
                return get_default_value(field)

        raise AttributeError('No default value found for class.')

    def __post_init__(self):
        """By default, initialize the fields using the :func:`get_default_value` using the dataclass fields."""
        for field in fields(self):
            value = getattr(self, field.name)
            if value is None:
                setattr(self, field.name, get_default_value(field))

    def get_resources(self):
        def get_resources_of_value(value):
            resources = []
            if isinstance(value, YbeNode):
                resources.extend(value.get_resources())
            elif isinstance(value, (list, tuple)):
                for el in value:
                    resources.extend(get_resources_of_value(el))
            return resources

        resources = []
        for key, value in self.__dict__.items():
            resources.extend(get_resources_of_value(value))

        return resources


@dataclass
class YbeExamElement(SimpleYbeNode):
    """Base class for questions and other nodes appearing in an exam / questionnaire."""


@dataclass
class YbeResource(SimpleYbeNode):
    """Reference to another file for included content."""
    path: str = None


@dataclass
class ImageResource(YbeResource):
    """Path and meta data of an image which need to be included as a resource."""
    alt: str = None


@dataclass
class YbeResourceContext:
    """The context used to load Ybe resource."""

    def copy_resource(self, resource, dirname):
        """Copy the indicated resource to the indicated directory.

        Args:
            resource (YbeResource): the resource to copy
            dirname (str): the directory to copy to

        Returns:
            str: the path to the new file
        """
        raise NotImplementedError()


@dataclass
class ZipArchiveContext(YbeResourceContext):
    """Loading resources from a zipped archive."""
    path: str

    def copy_resource(self, resource, dirname):
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if os.path.isabs(resource.path):
            return shutil.copy(resource.path, dirname)
        else:
            if subdir := os.path.dirname(resource.path):
                dirname = os.path.join(dirname, subdir) + '/'

                if not os.path.exists(dirname):
                    os.makedirs(dirname)

            archive = zipfile.ZipFile(self.path, 'r')
            return archive.extract(resource.path, dirname)


@dataclass
class DirectoryContext(YbeResourceContext):
    """Loading resources from a directory"""
    path: str

    def copy_resource(self, resource, dirname):
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if os.path.isabs(resource.path):
            return shutil.copy(resource.path, dirname)
        else:
            if subdir := os.path.dirname(resource.path):
                dirname = os.path.join(dirname, subdir) + '/'

                if not os.path.exists(dirname):
                    os.makedirs(dirname)

            return shutil.copy(os.path.join(self.path, resource.path), dirname)


@dataclass
class YbeExam(SimpleYbeNode):
    """Representation of an Ybe file.

    An Ybe file basically consists of a header followed of a number of questions.
    """
    info: YbeInfo = field(default_factory=lambda: YbeInfo())
    questions: List[Question] = field(default_factory=list)
    resource_context: YbeResourceContext = None

    def get_points_possible(self):
        """Get the maximum number of points possible in this exam.

        Returns:
            float: the maximum number of points possible.
        """
        return sum(question.points for question in self.questions)

    def __str__(self):
        """Prints itself in Ybe Yaml format."""
        from ybe.lib.ybe_writer import write_ybe_string
        return write_ybe_string(self, minimal=True)


@dataclass
class YbeInfo(SimpleYbeNode):
    """The header information in a Ybe file."""
    title: str = None
    description: str = None
    document_version: str = None
    authors: List[str] = field(default_factory=list)
    date: date = None


@dataclass
class Question(YbeExamElement):
    id: str = ''
    points: Union[float, int] = 0
    text: TextNode = field(default_factory=lambda: Text())
    meta_data: QuestionMetaData = field(default_factory=lambda: QuestionMetaData())


@dataclass
class MultipleChoice(Question):
    answers: List[MultipleChoiceAnswer] = field(default_factory=list)


@dataclass
class MultipleResponse(Question):
    answers: List[MultipleResponseAnswer] = field(default_factory=list)


@dataclass
class OpenQuestion(Question):
    options: OpenQuestionOptions = field(default_factory=lambda: OpenQuestionOptions())


@dataclass
class TextOnlyQuestion(Question):
    pass


@dataclass
class MultipleChoiceAnswer(SimpleYbeNode):
    text: TextNode = field(default_factory=lambda: Text())
    correct: bool = False


@dataclass
class MultipleResponseAnswer(SimpleYbeNode):
    text: TextNode = field(default_factory=lambda: Text())
    correct: bool = False


@dataclass
class QuestionMetaData(SimpleYbeNode):
    general: GeneralQuestionMetaData = field(default_factory=lambda: GeneralQuestionMetaData())
    analytics: AnalyticsQuestionMetaData = field(default_factory=lambda: AnalyticsQuestionMetaData())


@dataclass
class GeneralQuestionMetaData(SimpleYbeNode):
    """General meta-data of a question.

    Args:
        description (str): free text area for info about this question
        keywords (List[str]): list of (free entry) keywords
        language (str): the language of this question
        creation_date (date): date of when this question was added
        authors (List[str]): list of authors who made this question
        module (str): the book or module this question is about
        chapters (List[str]): the chapters this question refers to
        skill_type (str): one of {Knowledge, Comprehension, Application, Analysis, Synthesis, Evaluation}
        difficulty (int): a difficulty rating, typically between 1 to 10 with 10 being the most difficult questions.
    """
    description: str = None
    keywords: List[str] = field(default_factory=list)
    language: str = None
    creation_date: date = None
    authors: List[str] = field(default_factory=list)
    module: str = None
    chapters: List[str] = field(default_factory=list)
    skill_type: str = None
    difficulty: int = None

    available_skill_types = ['Knowledge', 'Comprehension', 'Application', 'Analysis', 'Synthesis', 'Evaluation']


@dataclass
class AnalyticsQuestionMetaData(SimpleYbeNode):
    """Analytics about this question, e.g. usage statistics."""
    analytics: List[dict] = field(default_factory=list)


@dataclass
class TextNode(SimpleYbeNode):
    text: str = ''

    def to_html(self):
        """Convert the text in this node to HTML and return that.

        Returns:
            str: a HTML conversion of this text block node
        """
        raise NotImplementedError()

    def to_latex(self):
        """Convert the text in this node to Latex and return that.

        Returns:
            str: a Latex conversion of the text in this node
        """
        raise NotImplementedError()


@dataclass
class TextMarkdown(TextNode):
    """Text in Markdown format, use as ``text_markdown``."""

    def get_resources(self):
        return TextHTML(self.to_html()).get_resources()

    def to_html(self):
        return pypandoc.convert_text(self.text, 'html', 'md', extra_args=['--mathjax'])

    def to_latex(self):
        return markdown_to_latex(self.text)


@dataclass
class TextHTML(TextNode):
    """Text in HTML format, use as ``text_html``."""

    def get_resources(self):
        parsed = BeautifulSoup(self.text, 'lxml')

        def only_files(src):
            return not any(src.startswith(el) for el in ['http://', 'https://', 'data:'])

        resources = []
        for img in parsed.find_all('img', src=only_files):
            resources.append(ImageResource(path=img.get('src'), alt=img.get('alt')))
        return resources

    def to_html(self):
        return self.text

    def to_latex(self):
        return html_to_latex(self.text)


@dataclass
class Text(TextMarkdown):
    """Subclass of TextMarkDown, i.e. short for ``text_markdown`` in the Ybe file."""


@dataclass
class OpenQuestionOptions(SimpleYbeNode):
    """Options concerning an open question.

    Args:
        max_words (int): the maximum number of allowed words
        min_words (int): the minimum number of allowed words
        expected_lines (int): the number of lines expected to be typed (size hint)
    """
    max_words: int = None
    min_words: int = None
    expected_lines: int = None
