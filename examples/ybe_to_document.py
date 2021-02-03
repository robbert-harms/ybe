__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


from ybe import read_ybe_file, YbeToLatex, YbeToMarkdown, YbeToDocx, YbeToODT, YbeToHTML

from importlib import resources

with resources.path('ybe.data', 'example_database.ybe') as path:
    ybe_exam = read_ybe_file(path)

YbeToLatex().convert(ybe_exam, '/tmp/ybe/latex/main.tex', copy_resources=True)
YbeToMarkdown().convert(ybe_exam, '/tmp/ybe/markdown/main.md', copy_resources=True)
YbeToHTML().convert(ybe_exam, '/tmp/ybe/html/main.html', copy_resources=True)
YbeToDocx().convert(ybe_exam, '/tmp/ybe/main.docx')
YbeToODT().convert(ybe_exam, '/tmp/ybe/main.odt')
