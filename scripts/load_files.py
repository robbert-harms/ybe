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
from ybe.lib.qti_writer import write_qti_dir, write_qti_zip

# ybe_file = read_ybe_file('/home/robbert/Documents/ybe_assessments/2019Quiz2_database.ybe')
from ybe.lib.utils import copy_ybe_resources

# ybe_file = read_ybe_file('../ybe/data/example_database.ybe')

# copy_ybe_resources(ybe_file, '/tmp/test')



# write_qti_dir(ybe_file, '../ybe/data/qti_examples/example_database')
# print(ybe_file.resource_specifier)
# print(ybe_file)
# print(ybe_file.get_resources())
# for question in ybe_file.questions:
#     print(question.text.to_html().text)

# exit()
# # # # # print(ybe_file.get_warnings())  # todo
# # # print(write_ybe_string(ybe_file, minimal=True))
# write_ybe_file(ybe_file, '/tmp/test.ybe', minimal=True)
# #

ybe_file = read_qti_zip('../ybe/data/qti_examples/canvas_export_6.zip')
# ybe_file = read_qti_dir('../ybe/data/qti_examples/canvas_export_6')
# print(ybe_file.get_resources())
# print(ybe_file)
# print(ybe_file.get_resources())
# write_qti_zip(ybe_file, '../ybe/data/qti_examples/canvas_export_6_output')
write_qti_dir(ybe_file, '../ybe/data/qti_examples/canvas_export_6_output')


# copy_ybe_resources(ybe_file, '/tmp/test')
