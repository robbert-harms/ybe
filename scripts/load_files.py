__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import sys
from pprint import pprint
import ybe
import yaml
import text2qti
from ruamel.yaml import YAML
from ybe import read_ybe_file, write_ybe_string, write_ybe_file
from ybe.lib.qti_reader import read_qti_zip, read_qti_dir


ybe_file = read_ybe_file('../ybe/data/example_database.ybe')
print(ybe_file)
# # # # print(ybe_file.get_warnings())  # todo
# # print(write_ybe_string(ybe_file, minimal=True))
write_ybe_file(ybe_file, '/tmp/test.ybe', minimal=True)
#

# ybe_file = read_qti_zip('../ybe/data/qti_examples/canvas_export.zip')
# print(ybe_file)
#
# ybe_file = read_qti_dir('../ybe/data/qti_examples/canvas_export_6')
# print(ybe_file)
