__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from pprint import pprint

import ybe
import yaml

# from yamllint.linter import run
#
# with open("../ybe/data/example_database.ybe", "r") as stream:
#     run(stream)

from yamllint.config import YamlLintConfig
from yamllint import linter

conf = YamlLintConfig('extends: default')
with open("../ybe/data/example_database.ybe", "r") as stream:
    gen = linter.run(stream, conf)
errors = list(gen)
print(errors)
# if errors:
    # raise ImproperlyConfigured

# with open("../ybe/data/example_database.ybe", "r") as stream:
#     d = list(yaml.safe_load_all(stream))
# pprint(d)
