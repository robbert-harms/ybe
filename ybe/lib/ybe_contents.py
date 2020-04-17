from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2020-04-14'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from dataclasses import dataclass, field
from typing import Dict, Tuple, Sequence, List


@dataclass
class YbeFile:
    """Representation of an Ybe file.

    An Ybe file basically consists of a header followed of a number of questions.
    """
    file_info: YbeFileInfo = field(default_factory=lambda: YbeFileInfo)
    questions: List[Question] = field(default_factory=list)


@dataclass
class YbeFileInfo:
    """The header information in a Ybe file."""
    title: str = ''
    description: str = ''
    document_version: str = ''
    authors: List[str] = field(default_factory=list)
    creation_date: str = None

a = YbeFile()
print()

    # def __init__(self, title=None, description=None, document_version=None, authors=None, creation_date=None):
    #     """Contains meta information about an Ybe file.
    #
    #     Args:
    #         title (str): a one-line description of the contents of this file
    #         description (str): a longer description regarding the questions in this file
    #         document_version (str): an version identifier, should be of the format ``<number>.<number>.<number>``.
    #             For example: '0.1.4'.
    #         authors (List[str]): list of the authors
    #         creation_date (str): the date at which this file was created
    #     """
    #     self.title = title
    #     self.description = description
    #     self.document_version = document_version
    #     self.authors = authors
    #     self.creation_date = creation_date


class Question:

    def __init__(self, id=None, text=None, meta_data=None):
        """Basic question information.

        Args:
            id (str): an identifier for this question
            text (QuestionText): the text of the question
            meta_data (QuestionMetaData): the meta data of this question
        """
        self.id = id
        self.text = text or RegularText()
        self.meta_data = meta_data or QuestionMetaData()


class MultipleChoice(Question):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class OpenQuestion(Question):

    def __init__(self, options=None, **kwargs):
        super().__init__(**kwargs)
        self.options = options or OpenQuestionOptions()


class QuestionMetaData:

    def __init__(self, general=None, lifecycle=None, classification=None):
        self.general = general or GeneralQuestionMetaData()
        self.lifecycle = lifecycle or LifecycleQuestionMetaData()
        self.classification = classification or ClassificationQuestionMetaData()


class GeneralQuestionMetaData:

    def __init__(self, description=None, keywords=None, language=None):
        self.description = description
        self.keywords = keywords
        self.language = language


class LifecycleQuestionMetaData:

    def __init__(self, author=None):
        self.author = author


class ClassificationQuestionMetaData:

    def __init__(self, skill_level=None, related_concepts=None, module=None, chapter=None, difficulty=None):
        """

        Args:
            skill_level (str): one of {Knowledge, Comprehension, Application, Analysis, Synthesis, Evaluation}
            related_concepts (List[str]): list of related concepts / topics
            module (str): the book or module this question is about
            chapter (int): the chapter the work is about
            difficulty (int): the difficulty level from 1 to 10, with 10 being the hardest
        """
        self.skill_level = skill_level
        self.related_concepts = related_concepts
        self.module = module
        self.chapter = chapter
        self.difficulty = difficulty


class QuestionText:

    def __init__(self, text=None):
        self.text = text or ''


class RegularText(QuestionText):
    pass


class LatexText(QuestionText):
    pass


class OpenQuestionOptions:

    def __init__(self, max_words=None, min_words=None, expected_words=None, expected_lines=None):
        """Simple open questions information object.

        Args:
            max_words (int): the maximum number of allowed words
            min_words (int): the minimum number of allowed words
            expected_words (int): the expected number of words (size hint)
            expected_lines (int): the number of lines expected to be typed (size hint)
        """
        self.max_words = max_words
        self.min_words = min_words
        self.expected_words = expected_words
        self.expected_lines = expected_lines
