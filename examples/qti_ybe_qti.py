__author__ = 'Robbert Harms'
__date__ = '2021-01-28'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


import importlib.resources as pkg_resources
from ybe import read_qti_zip, write_ybe_file, read_ybe_file, YbeToQTI_v1p2
from ybe.lib.utils import copy_ybe_resources


def qti_to_ybe(qti_path, output_path):
    ybe_exam = read_qti_zip(qti_path)
    write_ybe_file(ybe_exam, output_path, minimal=True)
    copy_ybe_resources(ybe_exam, output_dir)


def ybe_to_qti(ybe_path, output_path, for_canvas=True):
    ybe_exam = read_ybe_file(ybe_path)
    YbeToQTI_v1p2(convert_canvas_equations=for_canvas).convert(ybe_exam, output_path)


output_dir = '/tmp/ybe_test/'

with pkg_resources.path('ybe.data', 'canvas_export.zip') as qti_path:
    qti_to_ybe(qti_path, output_dir + '/canvas_export.ybe')

ybe_to_qti(output_dir + '/canvas_export.ybe', output_dir + 'qti_canvas.zip')
