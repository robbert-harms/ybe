__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import importlib.resources as pkg_resources
from ybe import read_qti_zip, write_ybe_file
from ybe.lib.utils import copy_ybe_resources


# read the provided example QTI
with pkg_resources.path('ybe.data', 'canvas_export.zip') as path:
    ybe_exam = read_qti_zip(path)


# change to your preference
output_dir = '/tmp/ybe_output/'

# write the ybe file
write_ybe_file(ybe_exam, output_dir + '/canvas_export.ybe')

# and write the images referred to in the QTI
copy_ybe_resources(ybe_exam, output_dir)
