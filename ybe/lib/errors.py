__author__ = 'Robbert Harms'
__date__ = '2020-04-08'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


class YbeBaseError(Exception):
    """Base exception class for all Ybe related errors."""


class YbeLoadingError(YbeBaseError):

    def __init__(self, description=''):
        """Indicates an error while loading an .ybe file.

        Args:
            description (str): Human-readable description of the problem
        """
        self.description = description

    def __str__(self):
        return self.description
