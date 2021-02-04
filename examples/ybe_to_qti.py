__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


from ybe import read_ybe_file, YbeToQTI_v1p2
from importlib import resources

# read the provided example Ybe.
with resources.path('ybe.data', 'example_database.ybe') as path:
    ybe_exam = read_ybe_file(path)

# change to your preference
output_dir = '/tmp/qti_output/'

# Write a QTI with the equations converted to the way Canvas (https://canvas.instructure.com) likes it.
YbeToQTI_v1p2(convert_canvas_equations=True).convert(ybe_exam, output_dir + 'new.zip')
YbeToQTI_v1p2(convert_canvas_equations=True).convert(ybe_exam, output_dir + 'new')
