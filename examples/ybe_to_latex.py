__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


from ybe import read_ybe_file, write_latex_file
from importlib import resources
from ybe.lib.utils import copy_ybe_resources


# read the provided example Ybe.
with resources.path('ybe.data', 'example_database.ybe') as path:
    ybe_exam = read_ybe_file(path)

# change to your preference
output_dir = '/tmp/latex_output/'

# copy the images to the directory
copy_ybe_resources(ybe_exam, output_dir)

# write a latex file, this uses an provided latex template which has some fields you can fill in.
write_latex_file(ybe_exam, output_dir + '/main.tex', jinja2_kwargs={
    'header': {
        'university': 'My University',
        'faculty': 'My Faculty',
        'course': 'Some nice course',
        'day': '1st of January 2020',
        'hours': '10:00 - 12:00',
        'appendices': r'A table of numbers \\ A manual',
        'aids': r'A calculator \\ Any written or printed material',
        'lecturers': r'Prof. dr. John Doe \\ Prof. dr. Jane Doe',
    },
    'introduction': r'''
        \textbf{Important: Read this first}
        \\

        Please \textbf{switch off your mobile phone}, and store it in your bag. No pen cases, books, notes, or electronic devices are needed or allowed. Only a pencil is necessary. No talking, morse code, coughing, nervous ticking or other forms of sound that may be interpreted as communication.
        \\

        \textbf{Multiple Choice Questions}, there are a lot of multiple choice questions. Read all the answers before committing yourself to the answer you consider correct.
        \\

        You have two hours to complete this test.  \textbf{In order to avoid disturbance, you are not allowed to leave before 11:30}, unless indicated otherwise by the lecturer.
        \\

        \textbf{After the test, please return everything}, both the questions and the answering forms.
        \\

        \textbf{Good luck!}
        \newpage
    '''
})
