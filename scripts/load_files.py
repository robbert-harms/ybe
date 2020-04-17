__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import sys
from pprint import pprint
import ybe
import yaml
from ybe.lib.utils import load, dumps, dump
# import text2qti
from ruamel.yaml import YAML


# with open('../ybe/data/example_database.ybe', 'r') as f:
#     yaml = YAML(typ='rt')
#     a = yaml.load(f)
#
#     yaml2 = YAML()
# #     yaml2.dump(a, sys.stdout)
# #
# #
# #     print()
# # exit()

ybe_file = load('../ybe/data/example_database.ybe')
# print(ybe_file)

# print(ybe_file.get_warnings())  # todo

print(dumps(ybe_file))
dump(ybe_file, '/tmp/test.ybe')
