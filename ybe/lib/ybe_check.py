__author__ = 'Robbert Harms'
__date__ = '2021-01-28'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import collections
from dataclasses import fields
from ybe.lib.ybe_nodes import YbeNode


def check_ybe(ybe):
    """Check the provided ybe exam for problems and errors.

    Args:
        ybe (YbeExam): the ybe exam to check.

    Returns:
        List[SemanticError]: list of semantical errors
    """
    return YbeLinter().check(ybe)


class SemanticError:

    def __init__(self, description):
        """Problem with the Ybe content."""
        self.description = description

    def __str__(self):
        return self.description


class YbeLinter:
    """Check the ybe nodes for semantical errors."""

    def check(self, node):
        """Check the given node for problems.

        Returns:
            List[SemanticError]: the list of errors found.
        """
        problems = []

        method = f'_check_{node.__class__.__name__}'
        if hasattr(self, method):
            problems.extend(getattr(self, method)(node))
        else:
            problems.extend(self._defaultcheck(node))

        return problems

    def _defaultcheck(self, node):
        problems = []
        for field in fields(node):
            if not field.init:
                continue
            problems.extend(self._check_value(getattr(node, field.name)))
        return problems

    def _check_value(self, value):
        problems = []
        if isinstance(value, YbeNode):
            problems.extend(self.check(value))
        elif isinstance(value, (list, tuple)):
            for el in value:
                problems.extend(self._check_value(el))
        return problems

    def _check_YbeExam(self, node):
        problems = []
        question_ids = [question.id for question in node.questions]
        if len(question_ids) != len(set(question_ids)):
            duplicates = [item for item, count in collections.Counter(question_ids).items() if count > 1]
            problems.append(SemanticError(f'There were multiple questions with the same id: "{duplicates}"'))
        problems.extend(self._defaultcheck(node))
        return problems

    def _check_MultipleChoice(self, node):
        problems = []
        if not (s := sum(answer.correct for answer in node.answers)) == 1:
            problems.append(SemanticError(f'A multiple choice question must have exactly '
                                          f'1 answer marked as correct, {s} marked.'))
        problems.extend(self._defaultcheck(node))
        return problems

    def _check_MultipleResponse(self, node):
        problems = []
        if not (s := sum(answer.correct for answer in node.answers)) > 0:
            problems.append(SemanticError(f'A multiple response question must have at least '
                                          f'1 answer marked as correct, {s} marked.'))
        problems.extend(self._defaultcheck(node))
        return problems
