__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


from ybe import read_ybe_file
from importlib import resources
from ybe.lib.qti_writer import write_qti_zip, ConvertCanvasEquations


# read the provided example Ybe.
with resources.path('ybe.data', 'example_database.ybe') as path:
    ybe_exam = read_ybe_file(path)

# change to your preference
output_dir = '/tmp/qti_output/'

# write a generic QTI.
write_qti_zip(ybe_exam, output_dir + 'qti.zip')

# Write a QTI with the equations converted to the way Canvas (https://canvas.instructure.com) likes it.
write_qti_zip(ybe_exam, output_dir + 'qti_canvas.zip', text_formatter=ConvertCanvasEquations())
