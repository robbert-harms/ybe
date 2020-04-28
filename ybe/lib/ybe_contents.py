from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2020-04-14'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from dataclasses import dataclass, field, fields
from typing import List, Union

from ybe.lib.utils import get_default_value


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


class YbeNodeVisitor:
    """Interface class for a node visitor, part of the ``visitor`` design pattern."""

    def visit(self, node):
        """Visit method, called by the node which accepted this visitor.

        Args:
            node (YbeNode): the node being visited.
        """
        raise NotImplementedError()


@dataclass
class YbeFile(SimpleYbeNode):
    """Representation of an Ybe file.

    An Ybe file basically consists of a header followed of a number of questions.
    """
    file_info: YbeFileInfo = field(default_factory=lambda: YbeFileInfo())
    questions: List[Question] = field(default_factory=list)

    def __str__(self):
        """Prints itself in Ybe Yaml format."""
        from ybe.lib.ybe_writer import write_ybe_string
        return write_ybe_string(self, minimal=True)


@dataclass
class YbeFileInfo(SimpleYbeNode):
    """The header information in a Ybe file."""
    title: str = None
    description: str = None
    document_version: str = None
    authors: List[str] = field(default_factory=list)
    creation_date: str = None


@dataclass
class Question(SimpleYbeNode):
    id: str = ''
    text: TextBlock = field(default_factory=lambda: Text())
    meta_data: QuestionMetaData = field(default_factory=lambda: QuestionMetaData())


@dataclass
class MultipleChoice(Question):
    answers: List[MultipleChoiceAnswer] = field(default_factory=list)


@dataclass
class MultipleResponse(Question):
    answers: List[MultipleResponseAnswer] = field(default_factory=list)


@dataclass
class OpenQuestion(Question):
    points: Union[float, int] = None
    options: OpenQuestionOptions = field(default_factory=lambda: OpenQuestionOptions())


@dataclass
class MultipleChoiceAnswer(SimpleYbeNode):
    text: TextBlock = field(default_factory=lambda: Text())
    points: float = 0


@dataclass
class MultipleResponseAnswer(SimpleYbeNode):
    text: TextBlock = field(default_factory=lambda: Text())
    points: float = 0


@dataclass
class QuestionMetaData(SimpleYbeNode):
    general: GeneralQuestionMetaData = field(default_factory=lambda: GeneralQuestionMetaData())
    lifecycle: LifecycleQuestionMetaData = field(default_factory=lambda: LifecycleQuestionMetaData())
    classification: ClassificationQuestionMetaData = field(default_factory=lambda: ClassificationQuestionMetaData())
    analytics: AnalyticsQuestionMetaData = field(default_factory=lambda: AnalyticsQuestionMetaData())


@dataclass
class GeneralQuestionMetaData(SimpleYbeNode):
    description: str = None
    keywords: List[str] = field(default_factory=list)
    language: str = None


@dataclass
class LifecycleQuestionMetaData(SimpleYbeNode):
    author: str = None


@dataclass
class ClassificationQuestionMetaData(SimpleYbeNode):
    """The skill level and difficulty of the question.

    Args:
        skill_level (str): one of {Knowledge, Comprehension, Application, Analysis, Synthesis, Evaluation}
        related_concepts (List[str]): list of related concepts / topics
        module (str): the book or module this question is about
        chapter (int): the chapter the work is about
        difficulty (int): the difficulty level from 1 to 10, with 10 being the hardest
    """
    skill_level: str = None
    related_concepts: List[str] = field(default_factory=list)
    module: str = None
    chapter: int = None
    difficulty: int = None

    available_skill_levels = ['Knowledge', 'Comprehension', 'Application', 'Analysis', 'Synthesis', 'Evaluation']


@dataclass
class AnalyticsQuestionMetaData(SimpleYbeNode):
    """Analytics about this question, e.g. usage statistics."""
    analytics: List[dict] = field(default_factory=list)


@dataclass
class TextBlock(SimpleYbeNode):
    text: str = ''


@dataclass
class Text(TextBlock):
    """Text without any formatting."""


@dataclass
class TextLatex(TextBlock):
    """Text in Latex format."""


@dataclass
class TextMarkdown(TextBlock):
    """Text in Markdown format."""


@dataclass
class TextHTML(TextBlock):
    """Text in HTML format."""


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
