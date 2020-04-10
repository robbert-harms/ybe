__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


def load_ybe_file(fname):
    ...

    # todo deal with syntax errors (yaml)
    # todo deal with semantic errors (i.e. questions not well formed)

    '''semantics:

    1. a header must be present, like:

        ybe_version: 0.1.0
        info:
            title: Example questions
            description: Some examples to look up the way of describing questions.
            document_version: 0.1.0
            authors: [Robbert Harms, Sanne Schoenmakers]
            date: 2020-04-07

    2. each question is separated by ---
    3. each question must have a 'type'
    4. multiple choice questions must have at least one answer with 'correct: True'
    '''


