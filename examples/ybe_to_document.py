__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


from ybe import read_ybe_file, DefaultYbeLatexConverter, DefaultYbeMarkdownConverter
from importlib import resources

# read the provided example Ybe.
with resources.path('ybe.data', 'example_database.ybe') as path:
    ybe_exam = read_ybe_file(path)

DefaultYbeLatexConverter().convert(ybe_exam, '/tmp/ybe/latex/main.tex', copy_resources=True)
DefaultYbeMarkdownConverter().convert(ybe_exam, '/tmp/ybe/markdown/main.md', copy_resources=True)
