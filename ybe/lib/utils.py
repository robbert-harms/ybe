__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import os
from dataclasses import MISSING

import pypandoc


def markdown_to_latex(text):
    """Convert text in MarkDown format to Latex.

    Args:
        text: the text in Markdown format

    Returns:
        str: a Latex conversion of the text in this node
    """
    return pypandoc.convert_text(text, 'latex', 'md')


def html_to_latex(text):
    """Convert text in HTML format to Latex.

    Args:
        text: the text in HTML format

    Returns:
        str: a Latex conversion of the text in this node
    """
    return pypandoc.convert_text(text, 'latex', 'html')


def copy_ybe_resources(ybe_exam, dirname):
    """Copy all the resource specified in the provided Ybe file object to the provided directory.

    Args:
        ybe_exam (ybe.lib.ybe_contents.YbeExam): the Ybe exam to search for (external) resources.
        dirname (str): the directory to write the data to.

    Returns:
        List[str]: list of path names to the copied resources
    """
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if ybe_exam.resource_context is None:
        raise ValueError('Can\'t copy resources because the YbeResourceContext is not set.')

    paths = []
    for resource in ybe_exam.get_resources():
        paths.append(ybe_exam.resource_context.copy_resource(resource, dirname))
    return paths


def get_default_value(field):
    """Resolve the default value of a dataclass field.

    This first looks if ``default`` is defined, next it tries to call the function ``default_factory``, else it
    returns None.

    Args:
        field (dataclass.field): one field of a class with @dataclass decorator

    Returns:
        Any: the default field object.
    """
    if hasattr(field, 'default') and field.default is not MISSING:
        return field.default
    elif hasattr(field, 'default_factory') and field.default_factory is not MISSING:
        return field.default_factory()
    return None
