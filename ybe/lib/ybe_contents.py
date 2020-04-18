from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2020-04-14'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from dataclasses import dataclass
from typing import List


class YbeNode:
    """Basic inheritance class for all Ybe related content nodes."""

    def accept_visitor(self, visitor):
        """Ybe nodes support the ``visitor pattern`` to allow for document traversal.

        Args:
            visitor (YbeNodeVisitor): the visitor we will give a callback.
        """
        visitor.visit(self)


class YbeNodeVisitor:
    """Interface class for a node visitor, part of the ``visitor`` design pattern."""

    def visit(self, node):
        """Visit method, called by the node which accepted this visitor.

        Args:
            node (YbeNode): the node being visited.
        """
        raise NotImplementedError()


@dataclass
class YbeFile(YbeNode):
    """Representation of an Ybe file.

    An Ybe file basically consists of a header followed of a number of questions.
    """
    file_info: YbeFileInfo = None
    questions: List[Question] = None

    def __post_init__(self):
        self.file_info = self.file_info or YbeFileInfo()
        self.questions = self.questions or []

    def __str__(self):
        """Prints itself in Ybe Yaml format."""
        from ybe.lib.utils import dumps
        return dumps(self)


@dataclass
class YbeFileInfo(YbeNode):
    """The header information in a Ybe file."""
    title: str = None
    description: str = None
    document_version: str = None
    authors: List[str] = None
    creation_date: str = None

    def __post_init__(self):
        self.authors = self.authors or []


@dataclass
class Question(YbeNode):
    id: str = ''
    text: TextBlock = None
    meta_data: QuestionMetaData = None

    def __post_init__(self):
        self.id = self.id or ''
        self.text = self.text or Text()
        self.meta_data = self.meta_data or QuestionMetaData()


@dataclass
class MultipleChoice(Question):
    answers: List[MultipleChoiceAnswer] = None

    def __post_init__(self):
        self.answers = self.answers or []

    def nmr_correct_answers(self):
        """Get the number of answers marked as ``correct.``.

        Returns:
            int: the number of correct answers in this question
        """
        return sum(answer.correct for answer in self.answers)


@dataclass
class OpenQuestion(Question):
    options: OpenQuestionOptions = None

    def __post_init__(self):
        self.options = self.options or OpenQuestionOptions()


@dataclass
class MultipleChoiceAnswer(YbeNode):
    text: TextBlock = None
    points: float = None
    correct: bool = None

    def __post_init__(self):
        self.text = self.text or Text()
        self.points = self.points or 0
        self.correct = self.correct or False


@dataclass
class QuestionMetaData(YbeNode):
    general: GeneralQuestionMetaData = None
    lifecycle: LifecycleQuestionMetaData = None
    classification: ClassificationQuestionMetaData = None
    analytics: AnalyticsQuestionMetaData = None

    def __post_init__(self):
        self.general = self.general or GeneralQuestionMetaData()
        self.lifecycle = self.lifecycle or LifecycleQuestionMetaData()
        self.classification = self.classification or ClassificationQuestionMetaData()
        self.analytics = self.analytics or AnalyticsQuestionMetaData()


@dataclass
class GeneralQuestionMetaData(YbeNode):
    description: str = None
    keywords: List[str] = None
    language: str = None

    def __post_init__(self):
        self.keywords = self.keywords or []


@dataclass
class LifecycleQuestionMetaData(YbeNode):
    author: str = None


@dataclass
class ClassificationQuestionMetaData(YbeNode):
    """The skill level and difficulty of the question.

    Args:
        skill_level (str): one of {Knowledge, Comprehension, Application, Analysis, Synthesis, Evaluation}
        related_concepts (List[str]): list of related concepts / topics
        module (str): the book or module this question is about
        chapter (int): the chapter the work is about
        difficulty (int): the difficulty level from 1 to 10, with 10 being the hardest
    """
    skill_level: str = None
    related_concepts: List[str] = None
    module: str = None
    chapter: int = None
    difficulty: int = None

    available_skill_levels = ['Knowledge', 'Comprehension', 'Application', 'Analysis', 'Synthesis', 'Evaluation']

    def __post_init__(self):
        self.related_concepts = self.related_concepts or []


@dataclass
class AnalyticsQuestionMetaData(YbeNode):
    """Analytics about this question, e.g. usage statistics."""
    analytics: List[dict] = None

    def __post_init__(self):
        self.analytics = self.analytics or []


@dataclass
class TextBlock(YbeNode):
    text: str = ''


@dataclass
class Text(TextBlock):
    """Text without any formatting."""
    pass


@dataclass
class TextLatex(TextBlock):
    """Text in Latex format."""
    pass


@dataclass
class OpenQuestionOptions(YbeNode):
    """Options concerning an open question.

    Args:
        max_words (int): the maximum number of allowed words
        min_words (int): the minimum number of allowed words
        expected_words (int): the expected number of words (size hint)
        expected_lines (int): the number of lines expected to be typed (size hint)
    """
    max_words: int = None
    min_words: int = None
    expected_words: int = None
    expected_lines: int = None
