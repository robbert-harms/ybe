from __future__ import annotations  # needed until Python 3.10

__author__ = 'Robbert Harms'
__date__ = '2020-04-14'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from datetime import date

from dataclasses import dataclass, field, fields
from typing import List, Union, get_type_hints

from ybe.lib.data_types import TextData, TextPlain, YbeResourceContext
from ybe.lib.utils import get_default_value


@dataclass
class YbeNode:
    """Basic inheritance class for all Ybe related content nodes."""

    @classmethod
    def get_default_value(cls, field_name):
        """Get the default value for a field of this node.

        Args:
            field_name (str): the name of the field for which we want the default value

        Returns:
            Any: the default value
        """
        raise NotImplementedError()

    def get_resources(self):
        """Get a list of :class:`ResourceData` in this node or sub-tree.

        This will need to do a recursive lookup to find all the resources.

        Returns:
            List[ResourceData]: list of resources nodes.
        """
        raise NotImplementedError()


class SimpleYbeNode(YbeNode):
    """Simple implementation of the required methods of an YbeNode."""

    @classmethod
    def get_default_value(cls, field_name):
        """By default, resolve the default value using the dataclass fields."""
        for field in fields(cls):
            if field.name == field_name:
                return get_default_value(field)
        raise AttributeError('No default value found for class.')

    def __post_init__(self):
        """Apply some data type checks and value checks.

        First, if a provided value is None, we want to initialize it do the indicated default value.
        As such, this routine initializes fields using the :func:`get_default_value` from the dataclass fields.

        Second, if a field is marked as type TextData, we want to convert provided str types to TextData.
        """
        type_hints = get_type_hints(type(self))

        for field in fields(self):
            if field.init:
                value = getattr(self, field.name)
                if value is None:
                    setattr(self, field.name, get_default_value(field))
                    continue

                if type_hints[field.name] == TextData and isinstance(value, str):
                    setattr(self, field.name, TextPlain(value))
                    continue

    def get_resources(self):
        def get_resources_of_value(value):
            resources = []
            if isinstance(value, YbeNode):
                resources.extend(value.get_resources())
            elif isinstance(value, TextData):
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
class YbeExam(SimpleYbeNode):
    """Representation of an Ybe file.

    An Ybe file basically consists of a header followed of a number of questions.
    """
    info: YbeInfo = field(default_factory=lambda: YbeInfo())
    questions: List[Question] = field(default_factory=list)
    resource_context: YbeResourceContext = field(init=False)

    def get_points_possible(self):
        """Get the maximum number of points possible in this exam.

        Returns:
            float: the maximum number of points possible.
        """
        return sum(question.points for question in self.questions if hasattr(question, 'points'))

    def __str__(self):
        """Prints itself in Ybe Yaml format."""
        from ybe.lib.ybe_writer import write_ybe_string
        return write_ybe_string(self, minimal=True)


@dataclass
class YbeInfo(SimpleYbeNode):
    """The header information in a Ybe file."""
    title: TextData = field(default_factory=lambda: TextPlain(''))
    description: TextData = field(default_factory=lambda: TextPlain(''))
    document_version: str = None
    date: date = None
    authors: List[str] = field(default_factory=list)


@dataclass
class YbeExamElement(SimpleYbeNode):
    """Base class for questions and other nodes appearing in an exam / questionnaire."""
    id: str = ''
    title: TextData = None
    text: TextData = field(default_factory=lambda: TextPlain(''))
    feedback: Feedback = field(default_factory=lambda: Feedback())
    meta_data: QuestionMetaData = field(default_factory=lambda: QuestionMetaData())


@dataclass
class Question(YbeExamElement):
    points: Union[float, int] = 0


@dataclass
class MultipleChoice(Question):
    answers: List[AnswerOption] = field(default_factory=list)


@dataclass
class MultipleResponse(Question):
    answers: List[AnswerOption] = field(default_factory=list)


@dataclass
class OpenQuestion(Question):
    options: OpenQuestionOptions = field(default_factory=lambda: OpenQuestionOptions())


@dataclass
class TextOnly(Question):
    pass


@dataclass
class AnswerOption(SimpleYbeNode):
    text: TextData = field(default_factory=lambda: TextPlain(''))
    correct: bool = False
    hint: TextData = None


@dataclass
class QuestionMetaData(SimpleYbeNode):
    general: GeneralQuestionMetaData = field(default_factory=lambda: GeneralQuestionMetaData())
    analytics: List[AnalyticsQuestionUsage] = field(default_factory=list)


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
        skill_type (str): can be anything, but typically one of
            {Knowledge, Comprehension, Application, Analysis, Synthesis, Evaluation}
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


@dataclass
class AnalyticsQuestionUsage(SimpleYbeNode):
    """Represents the usage of this question"""


@dataclass
class QuestionUsedInExam(AnalyticsQuestionUsage):
    """Represents the usage of this question in an exam.

    This is loaded using the keyword ``exam``.
    """
    name: str = None
    participants: int = None
    nmr_correct: int = None


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


@dataclass
class Feedback(SimpleYbeNode):
    """Feedback texts"""
    general: TextData = None
    on_correct: TextData = None
    on_incorrect: TextData = None

