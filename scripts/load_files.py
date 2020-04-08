__author__ = 'Robbert Harms'
__date__ = '2020-04-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from pprint import pprint

import ybe
import yaml


with open("../ybe/data/example_database.yaml", "r") as stream:
    d = list(yaml.safe_load_all(stream))
pprint(d)
