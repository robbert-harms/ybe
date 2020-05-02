__author__ = 'Robbert Harms'
__date__ = '2020-04-08'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from textwrap import indent


class YbeBaseError(Exception):
    """Base exception class for all Ybe related errors."""


class YbeLoadingError(YbeBaseError):

    def __init__(self, description='', question_ind=None):
        """Indicates an error while loading an .ybe file.

        Args:
            description (str): Human-readable description of the problem
            question_ind (int): the question index regarding this loading error
        """
        self.description = description
        self.question_ind = question_ind

    def __str__(self):
        if self.question_ind is not None:
            return f'Question number {self.question_ind} could not be loaded: ' + self.description
        return self.description


class YbeMultipleLoadingErrors(YbeLoadingError):

    def __init__(self, items, question_ind=None, question_id=None):
        """Collection of multiple loading exceptions.

        Args:
            List[YbeLoadingError]: list of exceptions
            question_ind (int): the question index regarding this collection of errors
            question_id (str): the ID of the question raising the error
        """
        self.items = items
        self.question_ind = question_ind
        self.question_id = question_id

    def to_string(self, in_recurse=False):
        if self.question_ind is not None and not in_recurse:
            result = f'Errors loading question number {self.question_ind + 1} (id: {self.question_id}): \n'
            for item in self.items:
                if isinstance(item, YbeMultipleLoadingErrors):
                    result += indent(item.to_string(True), '    ') + '\n'
                else:
                    result += indent(item.description, '    ') + '\n'
            return result
        else:
            if in_recurse:
                return '\n'.join(map(str, self.items))
            else:
                result = '\n'
                for item in self.items:
                    result += '- ' + str(item)
                return result

    def __str__(self):
        return self.to_string()


class YbeVisitingError(YbeBaseError):

    def __init__(self, description=''):
        """Indicates an error while traversing the Ybe node objects.

        Args:
            description (str): Human-readable description of the problem
        """
        self.description = description

    def __str__(self):
        return self.description
