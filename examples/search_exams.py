__author__ = 'Robbert Harms'
__date__ = '2020-05-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


from ybe import read_ybe_file
from importlib import resources

# read the provided example Ybe.
with resources.path('ybe.data', 'example_database.ybe') as path:
    ybe_exam = read_ybe_file(path)


# find and print questions which give only 1 point
for question in ybe_exam.questions:
    if question.points == 1:
        print(question)
