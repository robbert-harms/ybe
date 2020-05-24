__author__ = 'Robbert Harms'
__date__ = '2020-05-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


import os
import jinja2

from ybe.lib.ybe_contents import MultipleChoice, OpenQuestion, TextOnlyQuestion, MultipleResponse


def write_latex_file(ybe_exam, fname, jinja2_env=None, jinja2_kwargs=None):
    """Write the provided Ybe object as a Latex file.

    Args:
        ybe_exam (ybe.lib.ybe_exam.YbeExam): the ybe file object to dump
        fname (str): the filename to write to
        jinja2_env (jinja2.Environment): the environment we use to render the Latex files. If not provided
            we use the environment returned by :func:`get_jinja2_environment`.
        jinja2_kwargs (dict): additional keyword arguments used when rendering the Jinja2 template.
            This will be unpacked and provided to the render method.
    """
    if not os.path.exists(dir := os.path.dirname(fname)):
        os.makedirs(dir)

    with open(fname, 'w') as f:
        f.write(write_latex_string(ybe_exam, jinja2_env=jinja2_env, jinja2_kwargs=jinja2_kwargs))


def write_latex_string(ybe_exam, jinja2_env=None, jinja2_kwargs=None):
    """Write the provided Ybe object as a Latex string.

    Args:
        ybe_exam (ybe.lib.ybe_exam.YbeExam): the ybe file object to dump
        jinja2_env (jinja2.Environment): the environment we use to render the Latex files. If not provided
            we use the environment returned by :func:`get_jinja2_environment`.
        jinja2_kwargs (dict): additional keyword arguments used when rendering the Jinja2 template.
            This will be unpacked and provided to the render method.

    Returns:
        str: the filled in Latex template.
    """
    jinja2_env = jinja2_env or get_jinja2_environment()

    jinja2_kwargs = jinja2_kwargs or {}
    jinja2_kwargs['header'] = jinja2_kwargs.get('header', {})
    template = jinja2_env.get_template('exam.tex')
    return template.render(exam=ybe_exam, **jinja2_kwargs)


def get_jinja2_environment(**kwargs):
    """Get the default Jinja2 environment we use for writing the Latex files.

    The provided kwargs overwrite the default keyword arguments we use to create the Jinja2 environment, meaning
    you can tune the environment to your needs.

    Args:
        kwargs: keyword argument overwriting the default environment arguments.

    Returns:
        jinja2.Environment: a configured environment
    """
    default_kwargs = dict(
        block_start_string=r'\BLOCK{',
        block_end_string='}',
        variable_start_string=r'\VAR{',
        variable_end_string='}',
        comment_start_string=r'\#{',
        comment_end_string='}',
        line_statement_prefix='%-',
        line_comment_prefix='%#',
        trim_blocks=True,
        autoescape=False,
        loader=get_jinja2_loader())

    default_kwargs.update(kwargs)
    env = jinja2.Environment(**default_kwargs)

    env.tests['multiple_choice'] = lambda question: isinstance(question, MultipleChoice)
    env.tests['open'] = lambda question: isinstance(question, OpenQuestion)
    env.tests['text_only'] = lambda question: isinstance(question, TextOnlyQuestion)
    env.tests['multiple_response'] = lambda question: isinstance(question, MultipleResponse)

    return env


def get_jinja2_loader():
    """Get the default Jinja2 loader.

    Returns:
        jinja2.PackageLoader: the default loader using the in build latex template.
    """
    return jinja2.PackageLoader('ybe', 'data/latex_template')
