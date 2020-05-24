__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import sys
from pprint import pprint
from textwrap import dedent

from jinja2 import FileSystemLoader, ChoiceLoader

import ybe
import yaml
import text2qti
from ruamel.yaml import YAML
from ybe import read_ybe_file, write_ybe_string, write_ybe_file
from ybe.lib.latex_writer import write_latex_file, get_jinja2_loader, get_jinja2_environment
from ybe.lib.qti_reader import read_qti_zip, read_qti_dir
from ybe.lib.qti_writer import write_qti_dir, write_qti_zip, ConvertCanvasEquations

# ybe_exam = read_ybe_exam('/home/robbert/Documents/ybe_assessments/2019Quiz2_database.ybe')
from ybe.lib.utils import copy_ybe_resources, markdown_to_latex

ybe_exam = read_ybe_file('../ybe/data/example_database.ybe')

# ybe_exam = read_qti_zip('../ybe/data/canvas_export.zip')


copy_ybe_resources(ybe_exam, '/tmp/test')
write_latex_file(ybe_exam, '/tmp/test/test.tex', jinja2_kwargs={
    'header': {
        'university': 'Eindhoven University',
        'faculty': 'Faculty of Human Computer Interaction',
        'course': 'Brain, Body and Behaviour',
        'day': '1st of January 2020',
        'hours': '10:00 - 12:00',
        'appendices': r'A table of numbers \\ A manual',
        'aids': r'A calculator \\ Any written or printed material',
        'lecturers': r'Prof. dr. Wijnand IJsselsteijn \\ Prof. dr. ir. Yvonne de Kort \\ Prof. dr. Armin Kohlrausch',
    },
    'introduction': r'''
        \textbf{Important: Read this first}
        \\

        Please \textbf{switch off your mobile phone}, and store it in your bag. No pen cases, books, notes, or electronic devices are needed or allowed. Only a pencil is necessary. No talking, morse code, coughing, nervous ticking or other forms of sound that may be interpreted as communication.
        \\

        \textbf{Multiple Choice Questions}, there are 20 multiple choice questions. For each question you will be provided with 4 possible answers. Only one will be completely correct. The other answers may range from being partly or nearly right to being obviously wrong. Read all the answers before committing yourself to the answer you consider correct.
        \\

        Please indicate the correct answer using the SEPARATE answering form. \textbf{Make sure to indicate the version you are filling out} (version A, B, or C).
        \\

        You have 45 minutes to complete this test, from 9:45-10:30. \textbf{In order to avoid disturbance, you are not allowed to leave before 10:30}, unless indicated otherwise by the lecturer.
        \\

        \textbf{After the test, please return everything}, both the questions and the answering forms.
        \\

        \textbf{Good luck!}
        \newpage
    '''
})


# print(ybe_exam.questions[-1].text.to_html().text)

# copy_ybe_resources(ybe_exam, '/tmp/test')



# write_qti_dir(ybe_exam, '../ybe/data/qti_examples/example_database')
# print(ybe_exam.resource_specifier)
# print(ybe_exam)
# print(ybe_exam.get_resources())
# for question in ybe_exam.questions:
#     print(question.text.to_html().text)


# # # # # print(ybe_exam.get_warnings())  # todo
# # # print(write_ybe_string(ybe_exam, minimal=True))
# write_ybe_file(ybe_exam, '/tmp/test.ybe', minimal=True)
# exit()


# ybe_exam = read_qti_zip('../ybe/data/canvas_export.zip')
# ybe_exam = read_qti_dir('../ybe/data/qti_examples/canvas_export_6')
# print(ybe_exam.get_resources())
# print(ybe_exam)
# print(ybe_exam.get_resources())
# write_qti_zip(ybe_exam, '../ybe/data/qti_examples/canvas_export_6_output')
# write_qti_dir(ybe_exam, '../ybe/data/canvas_import', text_formatter=ConvertCanvasEquations())
# write_qti_zip(ybe_exam, '../ybe/data/canvas_import.zip', text_formatter=ConvertCanvasEquations())

# copy_ybe_resources(ybe_exam, '/tmp/test')
