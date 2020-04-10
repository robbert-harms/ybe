__author__ = 'Robbert Harms'
__date__ = '2020-04-08'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


class BaseError:
    ...


class SyntaxError(BaseError):
    ...


class SemanticsError(BaseError):
    ...



# class LintProblem(object):
#     """Represents a linting problem found by yamllint."""
#     def __init__(self, line, column, desc='<no description>', rule=None):
#         #: Line on which the problem was found (starting at 1)
#         self.line = line
#         #: Column on which the problem was found (starting at 1)
#         self.column = column
#         #: Human-readable description of the problem
#         self.desc = desc
#         #: Identifier of the rule that detected the problem
#         self.rule = rule
#         self.level = None
#
#     @property
#     def message(self):
#         if self.rule is not None:
#             return '{} ({})'.format(self.desc, self.rule)
#         return self.desc
#
#     def __eq__(self, other):
#         return (self.line == other.line and
#                 self.column == other.column and
#                 self.rule == other.rule)
#
#     def __lt__(self, other):
#         return (self.line < other.line or
#                 (self.line == other.line and self.column < other.column))
#
#     def __repr__(self):
#         return '%d:%d: %s' % (self.line, self.column, self.message)
#
#
