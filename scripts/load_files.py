__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from pprint import pprint
import ybe
import yaml
from ybe.lib.utils import load, dumps
# import text2qti

with open('../ybe/data/example_database_v2.ybe', "r") as f:
    a = yaml.safe_load(f)
print(a)
exit()



ybe_file = load('../ybe/data/example_database.ybe')
print(ybe_file)

# print(ybe_file.get_warnings())  # todo

print(dumps(ybe_file))


# chapters = [question.meta_data.get('chapter') for question in ybe_file.questions]
# print(chapters)

# print(repr(ybe_file))

# dump(ybe_file, '/tmp/test.ybe')
#
#
# yaml_str = '''
#
# --- !ybe.question.multiple_choice
# id: '<some_random_string>'
# text: |-
#     Due to the "|" operator, all newlines in this text will be kept intact.
#     That is, this line will appear on a new line in the example file.
#     The "-" operator at the end (i.e "|-") indicates we want to remove any pending new line at the end.
#
#     Question: Which basic variants of line folding are there?
# '''
#
#
# class MultipleChoice(yaml.YAMLObject):
#     yaml_tag = u'!ybe'
#
#     def __init__(self, id, text):
#         self.id = id
#         self.text = text
#
#     def __repr__(self):
#         return '''
#         --- !test
#         id: ...
#         text: ...
#         '''
#
#     @classmethod
#     def from_yaml(cls, loader, node):
#         return MultipleChoice(node.value, node)
#
#     @classmethod
#     def to_yaml(cls, dumper, data):
#         return dumper.represent_scalar(cls.yaml_tag, '''
#             --- test
#             test
#             test
#         ''')
#
#
# # Required for safe_load
# yaml.SafeLoader.add_constructor('!ybe.question.multiple_choice', MultipleChoice.from_yaml)
# # Required for safe_dump
# yaml.SafeDumper.add_multi_representer(MultipleChoice, MultipleChoice.to_yaml)
#
# # settings_file = open('defaults.yaml', 'r')
#
# # settings = yaml.safe_load(settings_file)
# # print(settings)
#
# print(yaml.safe_dump_all(yaml.safe_load_all(yaml_str)))
